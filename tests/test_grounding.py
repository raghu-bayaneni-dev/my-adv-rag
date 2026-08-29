import pytest
from src.models.document import Department, ChunkMetadata, DocumentChunk
from src.models.query import QueryRequest, QueryResponse
from src.models.security import UserRole
from src.generation.generator import LLMGenerator, STANDARD_REFUSAL_MESSAGE
from src.engine.rag_pipeline import RAGEngine
from src.retrieval.retriever import RetrieverService


def test_generator_standard_refusal_when_no_context(test_settings):
    """Verify generator returns standardized refusal when context is empty (Principle IV)."""
    generator = LLMGenerator(settings=test_settings)
    answer, citations, is_refusal = generator.generate_response("What is our secret space mission?", chunks=[])
    
    assert is_refusal is True
    assert answer == STANDARD_REFUSAL_MESSAGE
    assert len(citations) == 0


def test_rag_engine_grounded_refusal_on_empty_retrieval(test_settings, mock_embedding_service):
    """Verify end-to-end RAG engine gracefully declines when retrieval yields 0 matching chunks."""
    from src.retrieval.vector_store import VectorStoreService
    
    empty_vector_store = VectorStoreService(
        settings=test_settings,
        embedding_service=mock_embedding_service,
        collection_name="empty_test_collection"
    )
    retriever = RetrieverService(vector_store=empty_vector_store)
    engine = RAGEngine(
        settings=test_settings,
        retriever=retriever
    )

    request = QueryRequest(
        query_text="What is our confidential quantum chip roadmap?",
        user_role=UserRole.PUBLIC
    )
    response = engine.query(request)
    
    assert response.is_refusal is True
    assert STANDARD_REFUSAL_MESSAGE in response.answer
    assert len(response.citations) == 0
