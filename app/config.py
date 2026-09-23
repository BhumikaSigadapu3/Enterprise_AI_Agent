from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    chroma_path: str = "./data/chroma"
    log_level: str = "INFO"
    max_tool_calls: int = Field(default=5, ge=1, le=20)

    # When enabled, enterprise document search and calculator calls are executed
    # through the MCP server rather than by directly importing local functions.
    mcp_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def chroma_dir(self) -> Path:
        path = Path(self.chroma_path)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
