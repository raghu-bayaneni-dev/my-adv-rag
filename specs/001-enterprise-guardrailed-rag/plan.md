# Implementation Plan: Enterprise Guardrailed Multi-Department RAG System

**Branch**: `001-enterprise-guardrailed-rag` | **Date**: 2026-08-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-enterprise-guardrailed-rag/spec.md`

---

## Summary

Build an enterprise-grade, guardrailed Retrieval-Augmented Generation (RAG) system with strict Role-Based Access Control (RBAC) across departmental documents (`Engineering`, `Finance`, `Public`). Documents are parsed with Docling into 600-token chunks with 120-token overlap and mandatory metadata (`department_access`, `source_file`, `page_number`). A black-box guardrail intercepts out-of-scope queries (e.g., coding/general advice) and prompt injections before vector search. Grounded answers are generated with strict citations, backed by a dual-tab Streamlit dashboard and an offline Ragas evaluation benchmark suite.

---

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
* **Parsing & Ingestion**: `docling`, `pypdf`
* **Vector Store & Embeddings**: `chromadb`, `sentence-transformers` / `google-genai` / `openai`
* **Configuration & Validation**: `pydantic>=2.0`, `pydantic-settings>=2.0`
* **LLM Orchestration**: `litellm` / `google-genai` / `langchain-core`
* **Security & Guardrails**: Custom regex PII sanitizer + Fast LLM Structured Classifier
* **Evaluation Framework**: `ragas`, `datasets`
* **User Interface & Viz**: `streamlit>=1.30`, `plotly>=5.18`
* **Testing Framework**: `pytest`, `pytest-asyncio`, `pytest-mock`

**Storage**: Local persistent ChromaDB index (`data/chroma_db/`) + JSON benchmark artifacts (`data/eval/`)

**Testing**: `pytest` unit, contract, and RBAC integration tests with deterministic mocks

**Target Platform**: Cross-platform (macOS / Linux / Windows) local execution and cloud container deployment

**Project Type**: Python Web Service + Streamlit Dashboard + CLI Ingestion & Eval Tools

**Performance Goals**: Sub-3.0s end-to-end response time for guardrailed query retrieval and generation

**Constraints**: Zero secret leakage; zero cross-department data leakage for unauthorized roles; 100% prompt groundedness with polite refusal fallback.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle / Rule | Status | Compliance Evidence in Design |
| :--- | :--- | :--- |
| **I. Modular & Testable Architecture** | ✅ **PASS** | Clean separation of concerns (`src/config/`, `src/ingestion/`, `src/retrieval/`, `src/generation/`, `src/security/`, `src/eval/`). Unit tests run with local offline mocks without live API dependencies. |
| **II. Strict Configuration & Secret Isolation** | ✅ **PASS** | `src/config/settings.py` implements Pydantic `BaseSettings` loading from `.env`. Zero hardcoded API keys. Fails fast on missing configurations. |
| **III. Mandatory Document Metadata Boundaries** | ✅ **PASS** | `ChunkMetadata` schema strictly requires `department_access`, `source_file`, and `page_number >= 1`. Ingestion pipeline validates before inserting into ChromaDB. |
| **IV. Strict Groundedness & Hallucination Prevention** | ✅ **PASS** | Generation engine enforces context boundaries in prompt; gracefully returns standardized refusal message when evidence is missing. |
| **V. Black-Box Security Gates & PII/Prompt Defense** | ✅ **PASS** | `SecurityGuardrailGate` runs prior to vector search, enforcing RBAC filtering, PII redaction, prompt injection defense, and out-of-scope canned refusal. |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-enterprise-guardrailed-rag/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Phase 0: Technical decisions & trade-offs
├── data-model.md        # Phase 1: Pydantic schemas & RBAC mapping
├── quickstart.md        # Phase 1: Setup & validation walkthrough
├── contracts/           # Phase 1: Service interface contracts
│   ├── rag-engine-contract.md
│   ├── guardrail-contract.md
│   └── eval-contract.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
.
├── .env.example              # Template for environment variables
├── requirements.txt          # Python dependencies
├── app.py                    # Streamlit Multi-Tab Dashboard entrypoint
├── data/                     # Raw documents and persistent stores
│   ├── engineering/          # Engineering department documents
│   ├── finance/              # Finance department documents
│   ├── public/               # Public documents
│   ├── eval/                 # Golden evaluation datasets & benchmark results
│   │   ├── golden_dataset.json
│   │   └── eval_results.json
│   └── chroma_db/            # Local persistent ChromaDB store
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py       # Pydantic Settings configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py       # DocumentChunk & ChunkMetadata schemas
│   │   ├── security.py       # UserRole, RBAC mappings, & GuardrailResult
│   │   ├── query.py          # QueryRequest, QueryResponse, & Citation
│   │   └── evaluation.py     # BenchmarkReport & EvalSample schemas
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── parser.py         # Docling document parser
│   │   ├── chunker.py        # 600-token / 120-overlap token chunker
│   │   └── pipeline.py       # Ingestion orchestrator & metadata validator
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── vector_store.py   # ChromaDB wrapper with dynamic RBAC where-filter
│   │   └── retriever.py      # Similarity search service
│   ├── security/
│   │   ├── __init__.py
│   │   ├── pii_sanitizer.py  # Regex-based PII scrubber
│   │   ├── injection_guard.py# Prompt injection filter
│   │   └── guardrails.py     # Chipotle-style fast LLM scope classifier
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── prompts.py        # Grounded system prompts & templates
│   │   └── generator.py      # LLM synthesis & citation extractor
│   ├── engine/
│   │   ├── __init__.py
│   │   └── rag_pipeline.py   # End-to-end RAG orchestrator
│   └── eval/
│       ├── __init__.py
│       ├── metrics.py        # Ragas evaluation metric calculators
│       └── benchmark_runner.py# CLI benchmark runner
└── tests/
    ├── __init__.py
    ├── conftest.py           # Shared fixtures & mocks
    ├── test_config.py        # Pydantic Settings validation tests
    ├── test_ingestion.py     # Docling parsing & metadata tests
    ├── test_rbac.py          # Vector store role isolation tests
    ├── test_guardrails.py    # Out-of-scope & prompt injection tests
    ├── test_grounding.py     # Hallucination & refusal tests
    └── test_eval.py          # Benchmark metrics tests
```

**Structure Decision**: Single modular Python project with clean sub-packages for `config`, `models`, `ingestion`, `retrieval`, `security`, `generation`, `engine`, and `eval`.

---

## Complexity Tracking

*No constitutional violations or unjustified complexities present.*
