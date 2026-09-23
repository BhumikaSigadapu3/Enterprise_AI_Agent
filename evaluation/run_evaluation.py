import asyncio
import json
from pathlib import Path
from time import perf_counter

from app.agent.graph import run_agent
from app.guardrails.security import validate_output
from app.rag.store import document_store


async def evaluate_case(case: dict) -> dict:
    start = perf_counter()
    state = await run_agent(
        {
            "task": case["task"],
            "session_id": "evaluation",
            "allowed_tools": ["document_search", "calculator", "research"],
            "context": {},
            "tool_calls": [],
            "evidence": [],
            "trace": [],
            "iterations": 0,
        }
    )
    latency_ms = (perf_counter() - start) * 1000

    answer = state.get("answer", "").lower()
    successful_tools = {
        call["tool"]
        for call in state.get("tool_calls", [])
        if call.get("success")
    }

    expected_keywords = case.get("expected_keywords", [])
    keyword_score = (
        sum(keyword.lower() in answer for keyword in expected_keywords)
        / len(expected_keywords)
        if expected_keywords
        else 1.0
    )

    required_tools = set(case.get("required_tools", []))
    tool_score = (
        len(required_tools & successful_tools) / len(required_tools)
        if required_tools
        else 1.0
    )

    return {
        "task": case["task"],
        "response_quality_score": round(keyword_score, 3),
        "tool_call_accuracy": round(tool_score, 3),
        "task_completion": validate_output(state.get("answer", "")).allowed,
        "latency_ms": round(latency_ms, 2),
    }


async def main():
    sample_path = Path("sample_data/employee_policy.txt")
    document_store.ensure_document(
        sample_path.read_text(encoding="utf-8"), sample_path.name
    )

    dataset = json.loads(Path("evaluation/dataset.json").read_text())
    results = [await evaluate_case(case) for case in dataset]

    print(json.dumps(results, indent=2))

    print("\nAggregate metrics")
    print(
        json.dumps(
            {
                "avg_response_quality": round(
                    sum(r["response_quality_score"] for r in results) / len(results), 3
                ),
                "avg_tool_accuracy": round(
                    sum(r["tool_call_accuracy"] for r in results) / len(results), 3
                ),
                "avg_latency_ms": round(
                    sum(r["latency_ms"] for r in results) / len(results), 2
                ),
                "task_completion_rate": round(
                    sum(r["task_completion"] for r in results) / len(results), 3
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
