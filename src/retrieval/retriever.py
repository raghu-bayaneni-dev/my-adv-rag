from typing import List, Optional
from src.config.settings import Settings
from src.models.document import DocumentChunk
from src.models.security import UserRole
from src.retrieval.vector_store import VectorStoreService


class DefaultEmbeddingService:
    """
    Embedding service supporting sentence-transformers, Google Gemini embeddings, or OpenAI.
    Defaults to sentence-transformers for local execution.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_query(self, text: str) -> List[float]:
        model = self._get_model()
        return model.encode(text, normalize_embeddings=True).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        return model.encode(texts, normalize_embeddings=True).tolist()


class RetrieverService:
    """
    High-level similarity retrieval service integrating embedding generation and vector query.
    """
    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store

    def retrieve(self, query: str, user_role: UserRole, top_k: int = 4) -> List[DocumentChunk]:
        """
        Retrieves top-k relevant chunks matching the user's role authorization.
        """
        return self.vector_store.search(
            query_text=query,
            user_role=user_role,
            top_k=top_k
        )
