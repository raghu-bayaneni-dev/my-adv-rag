import time
import logging
from typing import Optional, List
from src.config.settings import Settings
from src.models.query import QueryRequest, QueryResponse, Citation
from src.models.security import UserRole, GuardrailResult, GuardrailCategory
from src.retrieval.retriever import RetrieverService
from src.generation.generator import LLMGenerator

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Orchestrates the complete guardrailed query lifecycle:
    1. Black-box security gate (PII sanitization & intent classification).
    2. Dynamic RBAC similarity vector search.
    3. Grounded answer generation with citations or graceful refusal.
    """
    def __init__(
        self,
        settings: Settings,
        retriever: RetrieverService,
        generator: Optional[LLMGenerator] = None,
        guardrail_gate = None
    ):
        self.settings = settings
        self.retriever = retriever
        self.generator = generator or LLMGenerator(settings=settings)
        self.guardrail_gate = guardrail_gate

    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Executes end-to-end synchronous RAG pipeline.
        """
        start_time = time.time()
        raw_query = request.query_text.strip()
        user_role = request.user_role
        top_k = request.top_k

        # 1. Security Gate & Scope Classification
        sanitized_query = raw_query
        if self.guardrail_gate:
            guardrail_res: GuardrailResult = self.guardrail_gate.evaluate(raw_query)
            if not guardrail_res.is_allowed:
                latency = round((time.time() - start_time) * 1000, 2)
                return QueryResponse(
                    query=raw_query,
                    answer=guardrail_res.refusal_message or "Query rejected by security policy.",
                    user_role=user_role,
                    is_refusal=True,
                    guardrail_triggered=True,
                    citations=[],
                    latency_ms=latency
                )
            sanitized_query = guardrail_res.sanitized_query

        # 2. Dynamic RBAC Vector Retrieval
        retrieved_chunks = self.retriever.retrieve(
            query=sanitized_query,
            user_role=user_role,
            top_k=top_k
        )

        # 3. Grounded Synthesis & Citation Mapping
        answer, citations, is_refusal = self.generator.generate_response(
            query=sanitized_query,
            chunks=retrieved_chunks
        )

        latency = round((time.time() - start_time) * 1000, 2)
        return QueryResponse(
            query=raw_query,
            answer=answer,
            user_role=user_role,
            is_refusal=is_refusal,
            guardrail_triggered=False,
            citations=citations,
            latency_ms=latency
        )
