from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings adhering to Constitution Principle II.
    Strictly loads configuration from environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API Key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API Key")

    # LLM & Embedding Models
    default_llm_model: str = Field(default="gemini/gemini-2.5-flash", description="Default model for synthesis")
    guardrail_llm_model: str = Field(default="gemini/gemini-2.5-flash", description="Model for guardrail classification")
    embedding_provider: str = Field(default="sentence-transformers", description="Embedding provider (sentence-transformers, openai, gemini)")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model name")

    # Ingestion & Chunker Parameters
    data_dir: str = Field(default="data", description="Path to source documents directory")
    chroma_persist_dir: str = Field(default="data/chroma_db", description="ChromaDB persistent store directory")
    chunk_size: int = Field(default=600, ge=100, le=2000, description="Target chunk size in tokens")
    chunk_overlap: int = Field(default=120, ge=0, le=500, description="Chunk sliding overlap in tokens")

    # Security & Guardrails
    enable_pii_redaction: bool = Field(default=True, description="Whether to redact PII in queries")
    enable_prompt_injection_defense: bool = Field(default=True, description="Whether to detect prompt injection")
    guardrail_temperature: float = Field(default=0.0, ge=0.0, le=1.0, description="Temperature for guardrail classifier")

    # App & Environment
    app_title: str = Field(default="Enterprise Guardrailed RAG", description="Application display title")
    environment: str = Field(default="development", description="Runtime environment (development, test, production)")
    log_level: str = Field(default="INFO", description="Logging level")


def get_settings() -> Settings:
    """Returns singleton/fresh instance of Settings."""
    return Settings()
