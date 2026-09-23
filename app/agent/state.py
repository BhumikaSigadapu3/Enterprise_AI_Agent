from typing import TypedDict, Any


class AgentState(TypedDict, total=False):
    task: str
    session_id: str
    allowed_tools: list[str]
    context: dict[str, Any]

    # LLM-generated structured plan.
    plan: list[dict[str, Any]]
    current_step: int

    tool_calls: list[dict[str, Any]]
    evidence: list[dict[str, Any]]

    answer: str
    trace: list[dict[str, Any]]
    iterations: int
