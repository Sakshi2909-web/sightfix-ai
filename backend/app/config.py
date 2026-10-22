import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DATABASE_URL: str = "sqlite:///./sightfix.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_URL: str = "http://localhost:6333"
    STORAGE_DIR: str = "./data_storage"

    # Providers: mock | anthropic | openai | gemini | local
    VLM_PROVIDER: str = "mock"
    LLM_PROVIDER: str = "mock"
    EMBEDDING_PROVIDER: str = "mock"

    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    SANDBOX_TIMEOUT_SEC: int = 180
    SANDBOX_MEM_MB: int = 2048
    MAX_UPLOAD_MB: int = 50

    # Fusion ranking default weights
    W_DENSE: float = 0.25
    W_LEX: float = 0.20
    W_STACK: float = 0.30
    W_UI: float = 0.15
    W_GIT: float = 0.05
    W_GRAPH: float = 0.05

    @property
    def storage_path(self) -> Path:
        p = Path(self.STORAGE_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
