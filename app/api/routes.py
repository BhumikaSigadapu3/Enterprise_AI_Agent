from time import perf_counter

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.agent.graph import run_agent
from app.guardrails.security import validate_input, validate_output
from app.models import AgentRequest, AgentResponse, SearchRequest
from app.rag.store import document_store

router = APIRouter()


@router.post("/agent/run", response_model=AgentResponse)
async def run_agent_endpoint(request: AgentRequest):
    guardrail = validate_input(request.task)
    if not guardrail.allowed:
        raise HTTPException(status_code=400, detail=guardrail.reason)

    start = perf_counter()
    try:
        state = await run_agent(
            {
                "task": request.task,
                "session_id": request.session_id,
                "allowed_tools": request.allowed_tools,
                "context": request.context,
                "tool_calls": [],
                "evidence": [],
                "trace": [],
                "iterations": 0,
            }
        )
    except RuntimeError as exc:
        # Missing LLM configuration should be explicit rather than silently falling
        # back to a fake rule-based planner.
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    latency_ms = (perf_counter() - start) * 1000
    output_check = validate_output(state.get("answer", ""))

    return AgentResponse(
        answer=state.get("answer", ""),
        task=request.task,
        plan=state.get("plan", []),
        tool_calls=state.get("tool_calls", []),
        trace=state.get("trace", []),
        latency_ms=round(latency_ms, 2),
        validation_passed=output_check.allowed,
    )


@router.post("/documents/ingest")
async def ingest_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="This project currently accepts UTF-8 text files.",
        ) from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="Document is empty.")

    document_store.add_document(text, file.filename)
    return {"status": "indexed", "source": file.filename}


@router.post("/documents/search")
async def search_documents(request: SearchRequest):
    return {"results": document_store.search(request.query, request.k)}
