import json
from typing import Any

from langgraph.graph import END, StateGraph

from app.agent.state import AgentState
from app.config import settings
from app.guardrails.security import validate_tool_permission
from app.llm.client import get_llm
from app.llm.prompts import PLANNER_SYSTEM_PROMPT, SYNTHESIS_SYSTEM_PROMPT
from app.mcp.client import call_mcp_tool
from app.models import AgentPlan
from app.tools.registry import TOOL_REGISTRY


REAL_TOOLS = {"document_search", "calculator", "research"}


def add_trace(state: AgentState, step: str, detail: str, **metadata: Any) -> None:
    state.setdefault("trace", []).append(
        {"step": step, "detail": detail, "metadata": metadata}
    )


async def planner(state: AgentState):
    """Use an LLM with Pydantic structured output to build the execution plan."""
    llm = get_llm()
    allowed_tools = [tool for tool in state.get("allowed_tools", []) if tool in REAL_TOOLS]
    available_tools = allowed_tools + ["final_answer"]

    user_prompt = f"""
Available tools for this request: {available_tools}

User task:
{state['task']}

Additional context (may be empty):
{json.dumps(state.get('context', {}), ensure_ascii=False)}

Return an executable plan now.
""".strip()

    structured_llm = llm.with_structured_output(AgentPlan)
    plan_response = await structured_llm.ainvoke(
        [
            ("system", PLANNER_SYSTEM_PROMPT),
            ("human", user_prompt),
        ]
    )

    plan = [step.model_dump() for step in plan_response.steps]

    # Defense in depth: reject any tool outside the request's allowed surface.
    for step in plan:
        if step["tool"] != "final_answer" and step["tool"] not in allowed_tools:
            raise ValueError(f"Planner selected a tool that is not allowed: {step['tool']}")

    state["plan"] = plan
    state["current_step"] = 0
    add_trace(state, "planner", "LLM generated a structured execution plan.", plan=plan)
    return state


def select_tool(state: AgentState) -> str:
    index = state.get("current_step", 0)
    plan = state.get("plan", [])
    if index >= len(plan):
        return "finalize"
    return plan[index]["tool"]


async def execute_tool(state: AgentState):
    tool_name = select_tool(state)

    if tool_name in {"finalize", "final_answer"}:
        state["current_step"] = len(state.get("plan", []))
        return state

    permission = validate_tool_permission(tool_name, state.get("allowed_tools", []))
    if not permission.allowed:
        add_trace(state, "guardrail", permission.reason, tool=tool_name)
        state["current_step"] = state.get("current_step", 0) + 1
        return state

    current_step = state["plan"][state.get("current_step", 0)]
    tool_input = current_step["input"]

    try:
        execution_mode = "local"
        if settings.mcp_enabled and tool_name in {"document_search", "calculator"}:
            result = await call_mcp_tool(tool_name, tool_input)
            execution_mode = "mcp"
        elif tool_name == "research":
            result = await TOOL_REGISTRY[tool_name](tool_input)
        else:
            result = TOOL_REGISTRY[tool_name](tool_input)

        call = {
            "tool": tool_name,
            "input": tool_input,
            "output": result,
            "success": True,
            "execution_mode": execution_mode,
        }
        state.setdefault("tool_calls", []).append(call)
        state.setdefault("evidence", []).append(
            {
                "tool": tool_name,
                "input": tool_input,
                "result": result,
                "execution_mode": execution_mode,
            }
        )
        add_trace(
            state,
            "tool_execution",
            f"Executed {tool_name} via {execution_mode}.",
            input=tool_input,
            success=True,
        )
    except Exception as exc:
        state.setdefault("tool_calls", []).append(
            {
                "tool": tool_name,
                "input": tool_input,
                "error": str(exc),
                "success": False,
            }
        )
        add_trace(
            state,
            "tool_execution",
            f"{tool_name} failed.",
            error=str(exc),
        )

    state["current_step"] = state.get("current_step", 0) + 1
    state["iterations"] = state.get("iterations", 0) + 1
    return state


def should_continue(state: AgentState) -> str:
    if state.get("iterations", 0) >= settings.max_tool_calls:
        return "finalize"
    if state.get("current_step", 0) < len(state.get("plan", [])):
        return "tool"
    return "finalize"


async def finalize(state: AgentState):
    """Use the LLM to synthesize a user-facing answer grounded in tool evidence."""
    llm = get_llm()

    evidence_payload = json.dumps(
        state.get("evidence", []),
        ensure_ascii=False,
        default=str,
    )
    failures = [call for call in state.get("tool_calls", []) if not call.get("success")]

    user_prompt = f"""
Original user task:
{state['task']}

Execution plan:
{json.dumps(state.get('plan', []), ensure_ascii=False)}

Tool evidence:
{evidence_payload}

Tool failures:
{json.dumps(failures, ensure_ascii=False, default=str)}

Write the final answer to the user. Ground enterprise claims in the retrieved evidence.
""".strip()

    response = await llm.ainvoke(
        [
            ("system", SYNTHESIS_SYSTEM_PROMPT),
            ("human", user_prompt),
        ]
    )
    state["answer"] = str(response.content).strip()
    add_trace(state, "finalize", "LLM synthesized the final answer from execution evidence.")
    return state


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("planner", planner)
    graph.add_node("tool", execute_tool)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "tool")
    graph.add_conditional_edges(
        "tool",
        should_continue,
        {"tool": "tool", "finalize": "finalize"},
    )
    graph.add_edge("finalize", END)
    return graph.compile()


agent_graph = build_agent()


async def run_agent(initial_state: AgentState) -> AgentState:
    return await agent_graph.ainvoke(initial_state)
