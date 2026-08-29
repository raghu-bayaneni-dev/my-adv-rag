# Interface Contract: RAG Engine

**Component**: `src.engine.rag_pipeline` | **Type**: Python Core Service

---

## 1. Overview

The `RAGEngine` orchestrates the complete guardrailed query lifecycle: query sanitation, guardrail verification, RBAC vector retrieval from ChromaDB, grounded prompt assembly, and LLM answer generation with citation mapping.

---

## 2. Public API Interface

```python
class RAGEngine:
    def __init__(self, config: Settings, vector_store: VectorStoreService, llm_service: LLMService):
        """Initializes RAG Engine with dependency-injected services."""
        ...

    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Executes end-to-end query workflow synchronously.
        
        Args:
            request: QueryRequest containing query_text, user_role, and top_k.
            
        Returns:
            QueryResponse with generated answer, citations, and execution latency.
        """
        ...

    async def aquery_stream(self, request: QueryRequest) -> AsyncGenerator[str, None]:
        """
        Streams generated response chunks for conversational UI rendering.
        """
        ...
```

---

## 3. Workflow Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Streamlit App
    participant Engine as RAG Engine
    participant Guardrail as Security Gate
    participant VectorDB as ChromaDB Vector Store
    participant LLM as Generator LLM

    User->>UI: Submit Query (query_text, user_role)
    UI->>Engine: query(QueryRequest)
    Engine->>Guardrail: evaluate(query_text)
    
    alt Out-of-Scope or Prompt Injection
        Guardrail-->>Engine: GuardrailResult(is_allowed=False, refusal_message)
        Engine-->>UI: QueryResponse(answer=refusal_message, guardrail_triggered=True)
    else In-Scope Corporate Query
        Guardrail-->>Engine: GuardrailResult(is_allowed=True, sanitized_query)
        Engine->>VectorDB: search(sanitized_query, allowed_depts, top_k)
        VectorDB-->>Engine: list[DocumentChunk]
        
        alt Zero Chunks Retrieved
            Engine-->>UI: QueryResponse(answer="I do not have sufficient information...", citations=[])
        else Chunks Found
            Engine->>LLM: generate(sanitized_query, chunks)
            LLM-->>Engine: grounded_text
            Engine-->>UI: QueryResponse(answer=grounded_text, citations=citations)
        end
    end
    UI-->>User: Render Message + Citation Badges
```
