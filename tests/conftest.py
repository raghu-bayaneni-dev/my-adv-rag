import pytest
from typing import List, Dict, Any
from src.config.settings import Settings
from src.models.document import Department, ChunkMetadata, DocumentChunk


class MockEmbeddingService:
    """Deterministic offline embedding generator for test isolation (Principle I)."""
    def __init__(self, dimension: int = 16):
        self.dimension = dimension

    def embed_query(self, text: str) -> List[float]:
        # Simple deterministic vector based on text hash
        val = sum(ord(c) for c in text) % 100 / 100.0
        return [val] * self.dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(t) for t in texts]


class MockLLMService:
    """Deterministic offline LLM service for testing synthesis and guardrails without API keys."""
    def __init__(self, default_response: str = "Mock grounded answer [Doc: architecture_guidelines.md, Page: 1]"):
        self.default_response = default_response

    def generate(self, prompt: str, **kwargs) -> str:
        if "classify" in prompt.lower() or "guardrail" in prompt.lower():
            if "sort a list" in prompt.lower() or "python" in prompt.lower() or "capital of france" in prompt.lower():
                return '{"is_allowed": false, "category": "out_of_scope", "reasoning": "General programming or trivia query"}'
            if "ignore previous instructions" in prompt.lower():
                return '{"is_allowed": false, "category": "prompt_injection", "reasoning": "Adversarial override attempt"}'
            return '{"is_allowed": true, "category": "in_scope", "reasoning": "Corporate query"}'
        return self.default_response


@pytest.fixture
def test_settings(tmp_path):
    """Provides test settings with temporary storage directory."""
    return Settings(
        chroma_persist_dir=str(tmp_path / "chroma_db"),
        data_dir=str(tmp_path / "data"),
        chunk_size=600,
        chunk_overlap=120
    )


@pytest.fixture
def mock_embedding_service():
    return MockEmbeddingService()


@pytest.fixture
def mock_llm_service():
    return MockLLMService()


@pytest.fixture
def sample_chunks() -> List[DocumentChunk]:
    """Generates sample multi-department document chunks."""
    return [
        DocumentChunk(
            chunk_id="eng-chunk-1",
            text="The payment processing service enforces maximum retry limit of 3 with 2.0 backoff.",
            metadata=ChunkMetadata(
                department_access=Department.ENGINEERING,
                source_file="payment_service_spec.md",
                page_number=1
            )
        ),
        DocumentChunk(
            chunk_id="fin-chunk-1",
            text="Total Revenue in Q3 2026 reached $48.5M with $14.8M R&D operating expenses.",
            metadata=ChunkMetadata(
                department_access=Department.FINANCE,
                source_file="q3_financial_report.md",
                page_number=1
            )
        ),
        DocumentChunk(
            chunk_id="pub-chunk-1",
            text="Enterprise headquarters is located in San Francisco, CA with 99.9% uptime SLA.",
            metadata=ChunkMetadata(
                department_access=Department.PUBLIC,
                source_file="company_overview.md",
                page_number=1
            )
        ),
    ]
