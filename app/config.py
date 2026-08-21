import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto").lower()

    KNOWLEDGE_BASE_DIR: Path = Path(os.getenv("KNOWLEDGE_BASE_DIR", str(BASE_DIR / "knowledge-base")))
    ORDERS_DATA_PATH: Path = Path(os.getenv("ORDERS_DATA_PATH", str(BASE_DIR / "data" / "orders.json")))

    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")
    RAG_RELEVANCE_THRESHOLD: float = float(os.getenv("RAG_RELEVANCE_THRESHOLD", "1.5"))

    # Snapshot time for mock dataset evaluations (2026-08-15T12:00:00Z)
    SNAPSHOT_TIME: str = "2026-08-15T12:00:00Z"

    @classmethod
    def get_active_provider(cls) -> str:
        if cls.LLM_PROVIDER in ("gemini", "google") and cls.GEMINI_API_KEY:
            return "gemini"
        if cls.LLM_PROVIDER == "openai" and cls.OPENAI_API_KEY:
            return "openai"
        if cls.GEMINI_API_KEY:
            return "gemini"
        if cls.OPENAI_API_KEY:
            return "openai"
        return "deterministic"  # Standalone deterministic fallback engine

config = Config()
