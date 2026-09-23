from langchain_openai import ChatOpenAI

from app.config import settings


def get_llm() -> ChatOpenAI:
    """Create the shared LLM client used for planning and synthesis."""
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Copy .env.example to .env and add a valid key."
        )

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )
