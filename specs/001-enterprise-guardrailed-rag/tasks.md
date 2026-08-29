# Implementation Tasks: Enterprise Guardrailed Multi-Department RAG System

**Branch**: `001-enterprise-guardrailed-rag` | **Date**: 2026-08-28 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency specification, and sample document layout.

- [X] T001 [P] Create `requirements.txt` with dependencies (`docling`, `chromadb`, `pydantic>=2.0`, `pydantic-settings>=2.0`, `streamlit>=1.30`, `plotly>=5.18`, `ragas`, `sentence-transformers`, `litellm`, `pytest`, `pytest-asyncio`, `pytest-mock`)
- [X] T002 [P] Create `.env.example` with template environment variables for API keys and embedding models
- [X] T003 [P] Create initial departmental document directories and sample files in `data/engineering/`, `data/finance/`, and `data/public/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core configuration, domain models, and testing infrastructure required before any user story implementation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Implement Pydantic Settings configuration in `src/config/settings.py` (enforcing Principle II)
- [X] T005 [P] Create domain models in `src/models/document.py` (Department enum, ChunkMetadata, DocumentChunk) and `src/models/security.py` (UserRole, RBAC mappings, GuardrailCategory, GuardrailResult)
- [X] T006 [P] Create query and evaluation schemas in `src/models/query.py` (QueryRequest, QueryResponse, Citation) and `src/models/evaluation.py` (BenchmarkReport, EvalSample)
- [X] T007 [P] Implement unit tests for configuration loading and validation in `tests/test_config.py`
- [X] T008 Implement shared pytest fixtures and offline LLM/embedding mocks in `tests/conftest.py` (enforcing Principle I)

**Checkpoint**: Foundation ready - domain contracts and settings validated.

---

## Phase 3: User Story 1 - Multi-Department Role-Based Document Lookup (Priority: P1) 🎯 MVP

**Goal**: Ingest multi-department documents via Docling into 600-token chunks with 120-token overlap, attach mandatory metadata (`department_access`, `source_file`, `page_number`), store in ChromaDB, and execute dynamic RBAC vector retrieval by active user role.

**Independent Test**: Ingest test documents from `data/engineering`, `data/finance`, and `data/public`. Query as `Public` user and verify 0 `Engineering`/`Finance` chunks returned. Query as `Finance-Manager` and verify retrieval of finance + public documents with source file and page citations.

### Tests for User Story 1

- [X] T009 [P] [US1] Unit and integration tests for Docling parsing and chunk metadata validation in `tests/test_ingestion.py`
- [X] T010 [P] [US1] Unit and integration tests for ChromaDB dynamic RBAC role filtering in `tests/test_rbac.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement Docling document parser supporting PDF, DOCX, and Markdown in `src/ingestion/parser.py`
- [X] T012 [US1] Implement token-aware sliding window chunker (600 tokens target, 120 tokens overlap) in `src/ingestion/chunker.py`
- [X] T013 [US1] Implement ingestion orchestrator and metadata validation pipeline in `src/ingestion/pipeline.py`
- [X] T014 [US1] Implement persistent ChromaDB vector store client with dynamic `where` RBAC metadata pre-filtering in `src/retrieval/vector_store.py`
- [X] T015 [US1] Implement similarity retrieval service in `src/retrieval/retriever.py`
- [X] T016 [US1] Implement grounded generation prompt templates and synthesis generator with citation mapping in `src/generation/prompts.py` and `src/generation/generator.py`
- [X] T017 [US1] Implement core end-to-end RAG orchestrator pipeline in `src/engine/rag_pipeline.py`

**Checkpoint**: User Story 1 complete — fully functional RBAC document ingestion, vector retrieval, and citation-backed answer generation.

---

## Phase 4: User Story 2 - Out-of-Scope Query Guardrailing & Hallucination Defense (Priority: P2)

**Goal**: Intercept out-of-scope queries (e.g., coding, trivia, casual advice) and prompt injections before vector search, return standardized canned refusal, sanitize PII, and gracefully decline unanswerable questions.

**Independent Test**: Submit out-of-scope queries ("Write a python sort script") and verify immediate canned refusal without vector search. Submit in-scope unanswerable questions and verify graceful refusal (*"I do not have sufficient information in the authorized corporate documents to answer this question."*).

### Tests for User Story 2

- [X] T018 [P] [US2] Unit tests for PII sanitization and prompt injection defense in `tests/test_guardrails.py`
- [X] T019 [P] [US2] Unit tests for groundedness refusal and hallucination prevention in `tests/test_grounding.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement regex-based PII sanitizer (SSN, credit card redaction) in `src/security/pii_sanitizer.py`
- [X] T021 [US2] Implement prompt injection filter and system override detector in `src/security/injection_guard.py`
- [X] T022 [US2] Implement fast structured LLM corporate scope classifier and Chipotle canned response gate in `src/security/guardrails.py`
- [X] T023 [US2] Integrate SecurityGuardrailGate into the RAG Engine query pipeline in `src/engine/rag_pipeline.py`

**Checkpoint**: User Story 2 complete — black-box security gates active with PII redaction, prompt injection defense, and grounded refusal fallback.

---

## Phase 5: User Story 3 - Interactive Evaluation & Quality Benchmark Dashboard (Priority: P3)

**Goal**: Provide an offline Ragas evaluation benchmark runner, bundled baseline evaluation dataset, and modern multi-tab Streamlit dashboard with conversational chat and Plotly visual analytics.

**Independent Test**: Run `python -m src.eval.benchmark_runner` to execute offline Ragas evaluation. Launch `streamlit run app.py` and verify Sidebar controls, Tab 1 chat interface with collapsible citations, and Tab 2 Plotly evaluation charts for Faithfulness, Answer Relevance, and Context Recall.

### Tests for User Story 3

- [X] T024 [P] [US3] Create golden benchmark dataset in `data/eval/golden_dataset.json` and pre-computed baseline records in `data/eval/eval_results.json`
- [X] T025 [P] [US3] Write unit tests for Ragas evaluation metrics calculations in `tests/test_eval.py`

### Implementation for User Story 3

- [X] T026 [US3] Implement Ragas evaluation metrics calculator (Faithfulness, Answer Relevance, Context Recall) in `src/eval/metrics.py`
- [X] T027 [US3] Implement offline evaluation CLI benchmark runner in `src/eval/benchmark_runner.py`
- [X] T028 [US3] Build modern Streamlit UI application with Sidebar (Role selector, API key input), Tab 1 (Conversational chat with citation cards and chunk previews), and Tab 2 (Plotly evaluation metric dashboards) in `app.py`

**Checkpoint**: User Story 3 complete — full multi-tab UI and offline benchmarking suite operational.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, end-to-end integration testing, and documentation.

- [X] T029 [P] Validate quickstart guide end-to-end execution per `specs/001-enterprise-guardrailed-rag/quickstart.md`
- [X] T030 [P] Create comprehensive project documentation and README in `README.md`
- [X] T031 Run full automated test suite (`pytest tests/ -v`) and verify 100% test pass rate with zero lint/type errors

---

## Dependencies & Execution Order

### Phase Dependencies

```mermaid
graph TD
    P1[Phase 1: Setup] --> P2[Phase 2: Foundational]
    P2 --> P3[Phase 3: US1 - RBAC Document Lookup (MVP)]
    P3 --> P4[Phase 4: US2 - Security Guardrails]
    P4 --> P5[Phase 5: US3 - Streamlit UI & Evaluation]
    P5 --> P6[Phase 6: Polish & Validation]
```

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational Phase (Phase 2). Delivers standalone MVP.
- **User Story 2 (P2)**: Integrates into RAG Engine from US1. Enhances security & refusal boundaries.
- **User Story 3 (P3)**: Wraps RAG Engine and Guardrails into Streamlit UI and Ragas evaluation pipeline.

---

## Parallel Execution Opportunities

### User Story 1
```bash
# Tests in parallel:
Task T009: tests/test_ingestion.py
Task T010: tests/test_rbac.py

# Models & Parsers in parallel:
Task T011: src/ingestion/parser.py
Task T012: src/ingestion/chunker.py
```

### User Story 2
```bash
# Tests in parallel:
Task T018: tests/test_guardrails.py
Task T019: tests/test_grounding.py

# Sanitizers & Filters in parallel:
Task T020: src/security/pii_sanitizer.py
Task T021: src/security/injection_guard.py
```

### User Story 3
```bash
# Eval dataset & metric tests in parallel:
Task T024: data/eval/golden_dataset.json & eval_results.json
Task T025: tests/test_eval.py
```

---

## Implementation Strategy

1. **MVP First (Phases 1-3)**: Deliver complete Docling ingestion, ChromaDB vector store with RBAC filtering, and grounded citation generation.
2. **Security Hardening (Phase 4)**: Add regex PII scrubbing, injection defense, and fast LLM scope classification.
3. **Full Experience & Benchmarks (Phase 5)**: Deliver Streamlit multi-tab UI with Plotly charts and offline Ragas benchmarking.
4. **Validation (Phase 6)**: Run complete test suite and verify end-to-end quickstart workflows.
