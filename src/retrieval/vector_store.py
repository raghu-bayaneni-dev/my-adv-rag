import os
import logging
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from src.config.settings import Settings
from src.models.document import Department, ChunkMetadata, DocumentChunk
from src.models.security import UserRole

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    ChromaDB vector store service with enforced dynamic RBAC metadata pre-filtering.
    """
    def __init__(self, settings: Settings, embedding_service=None, collection_name: str = "enterprise_docs"):
        self.settings = settings
        self.embedding_service = embedding_service
        self.collection_name = collection_name

        # Ensure persist directory exists
        os.makedirs(self.settings.chroma_persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[DocumentChunk]):
        """
        Inserts document chunks into ChromaDB with constitutional metadata tags.
        """
        if not chunks:
            return

        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "department_access": c.metadata.department_access.value,
                "source_file": c.metadata.source_file,
                "page_number": c.metadata.page_number,
                **c.metadata.extra
            }
            for c in chunks
        ]

        embeddings = None
        if self.embedding_service:
            embeddings = self.embedding_service.embed_documents(documents)

        if embeddings:
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        else:
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        logger.info(f"Upserted {len(chunks)} chunks into ChromaDB collection '{self.collection_name}'.")

    def search(self, query_text: str, user_role: UserRole, top_k: int = 4) -> List[DocumentChunk]:
        """
        Performs vector similarity search with mandatory dynamic RBAC pre-filtering.
        Guarantees that unauthorized department chunks are omitted at index level.
        """
        allowed_depts = user_role.allowed_department_strings()

        # ChromaDB dynamic metadata pre-filter
        if len(allowed_depts) == 1:
            where_filter = {"department_access": allowed_depts[0]}
        else:
            where_filter = {"department_access": {"$in": allowed_depts}}

        query_embedding = None
        if self.embedding_service:
            query_embedding = [self.embedding_service.embed_query(query_text)]

        kwargs: Dict[str, Any] = {
            "n_results": top_k,
            "where": where_filter
        }

        if query_embedding:
            kwargs["query_embeddings"] = query_embedding
        else:
            kwargs["query_texts"] = [query_text]

        results = self.collection.query(**kwargs)

        retrieved_chunks: List[DocumentChunk] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return retrieved_chunks

        for idx, chunk_id in enumerate(results["ids"][0]):
            text = results["documents"][0][idx]
            meta = results["metadatas"][0][idx]
            dept_str = meta.get("department_access", Department.PUBLIC.value)
            
            chunk_metadata = ChunkMetadata(
                department_access=Department(dept_str),
                source_file=meta.get("source_file", "unknown"),
                page_number=int(meta.get("page_number", 1)),
                extra={k: v for k, v in meta.items() if k not in ["department_access", "source_file", "page_number"]}
            )

            retrieved_chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                text=text,
                metadata=chunk_metadata
            ))

        return retrieved_chunks

    def count(self) -> int:
        """Returns total documents in collection."""
        return self.collection.count()
