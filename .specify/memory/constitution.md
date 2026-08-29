<!--
Sync Impact Report:
- Version change: initial template -> 1.0.0
- List of modified principles:
  - PRINCIPLE_1: I. Modular & Testable Architecture
  - PRINCIPLE_2: II. Strict Configuration & Secret Isolation (Pydantic Settings)
  - PRINCIPLE_3: III. Mandatory Document Metadata & Schema Boundaries
  - PRINCIPLE_4: IV. Strict Groundedness & Hallucination Prevention
  - PRINCIPLE_5: V. Black-Box Security Gates & PII/Prompt Defense
- Added sections:
  - Security & Access Control Standards
  - Quality Assurance & Verification Gates
  - Governance
- Removed sections: N/A (initial baseline)
- Follow-up TODOs: None
-->

# my-adv-rag Constitution

## Core Principles

### I. Modular & Testable Architecture
The codebase MUST maintain a strictly modular layout separating configuration, document ingestion, vector retrieval, generation, security filtering, and evaluation. Every component MUST be independently unit-testable with deterministic mocks; tests MUST NOT require live third-party API keys or external network connections to pass.

### II. Strict Configuration & Secret Isolation
All application and pipeline configurations MUST be managed through Pydantic Settings (`BaseSettings`) loading strictly from environment variables or secure `.env` files. Hardcoding credentials, API tokens, or secrets anywhere in the codebase or git repository is STRICTLY PROHIBITED. Missing or malformed configurations MUST fail fast at startup with explicit validation errors.

### III. Mandatory Document Metadata & Schema Boundaries
All document ingestion pipelines and chunk schemas MUST strictly enforce and validate required metadata fields: `department_access` (authorized department/role list), `source_file` (origin file name/path), and `page_number` (source page index). Any chunk or document failing schema validation MUST be rejected at the ingestion boundary before persisting to the vector store or index.

### IV. Strict Groundedness & Hallucination Prevention
LLM response generation MUST be fully and strictly grounded in the retrieved context chunks. When retrieved context is empty, below relevance thresholds, or insufficient to satisfy the query, the system MUST gracefully decline to answer using a standardized fallback message rather than fabricating information or hallucinating.

### V. Black-Box Security Gates & PII/Prompt Defense
All user queries and document retrieval pipelines MUST pass through black-box security gates before and after LLM execution. Retrieval MUST enforce role-based department filtering at the index level. Ingestion and query boundaries MUST sanitize/redact PII and detect/block prompt injection or out-of-scope system override attempts.

## Security & Access Control Standards

- Role-based access control (RBAC) MUST be enforced at the retrieval query level using the document's `department_access` metadata.
- Pre-retrieval and post-generation guardrails MUST sanitize sensitive PII and inspect prompts for adversarial injection attempts.
- Security boundary failures MUST trigger secure audit logging without leaking protected context or sensitive query data into logs.

## Quality Assurance & Verification Gates

- Unit and contract tests MUST validate schema constraints, Pydantic settings parsing, and retrieval filter logic.
- RAG evaluation pipelines (e.g., faithfulness, answer relevance, context recall) MUST be integrated as testing quality gates.
- All code changes MUST pass automated test suites and linting checks prior to integration.

## Governance

This Constitution represents the non-negotiable architectural and operational rules for the `my-adv-rag` project. Any changes to core principles, metadata contracts, or security guardrails require a formal amendment and a corresponding version bump according to Semantic Versioning:
- **MAJOR**: Incompatible governance shifts, removal of core principles, or breaking schema/security contracts.
- **MINOR**: Addition of new principles, extended security constraints, or structural quality gates.
- **PATCH**: Non-semantic clarifications, wording enhancements, or formatting fixes.

**Version**: 1.0.0 | **Ratified**: 2026-08-28 | **Last Amended**: 2026-08-28
