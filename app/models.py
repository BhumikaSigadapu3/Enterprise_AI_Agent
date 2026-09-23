from typing import Any, Literal
from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    task: str = Field(min_length=3, max_length=5000)
    session_id: str = "default"
    allowed_tools: list[str] = Field(
        default_factory=lambda: ["document_search", "calculator", "research"]
    )
    context: dict[str, Any] = Field(default_factory=dict)


class PlanStep(BaseModel):
    """One LLM-generated step in the agent execution plan."""

    tool: Literal["document_search", "calculator", "research", "final_answer"]
    input: str = Field(min_length=1, max_length=2000)
    reason: str = Field(min_length=1, max_length=1000)


class AgentPlan(BaseModel):
    steps: list[PlanStep] = Field(min_length=1, max_length=5)


class TraceEvent(BaseModel):
    step: str
    detail: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    answer: str
    task: str
    plan: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    trace: list[TraceEvent] = Field(default_factory=list)
    latency_ms: float
    validation_passed: bool


class SearchRequest(BaseModel):
    query: str = Field(min_length=2)
    k: int = Field(default=4, ge=1, le=10)


class EvaluationCase(BaseModel):
    task: str
    expected_keywords: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
