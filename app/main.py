from pathlib import Path

from fastapi import FastAPI

from app.api.routes import router
from app.observability.logging import configure_logging, logger
from app.rag.store import document_store

configure_logging()

app = FastAPI(
    title="Enterprise AI Research & Automation Agent",
    version="2.0.0",
    description="LLM-planned LangGraph agent with RAG, MCP tools, guardrails, evaluation and Docker deployment.",
)

app.include_router(router)


@app.on_event("startup")
async def startup():
    # Make the repository runnable immediately by indexing the bundled demo policy
    # once. Uploaded documents can still be added through the API.
    sample_path = Path("sample_data/employee_policy.txt")
    if sample_path.exists():
        document_store.ensure_document(
            sample_path.read_text(encoding="utf-8"),
            sample_path.name,
        )
    logger.info("agent_platform_started", version="2.0.0")


@app.get("/")
async def root():
    return {
        "name": "Enterprise AI Research & Automation Agent",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
