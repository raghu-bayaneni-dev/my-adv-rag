# Research & Technical Decisions: Enterprise Guardrailed Multi-Department RAG System

**Feature**: `001-enterprise-guardrailed-rag` | **Date**: 2026-08-28

## 1. Document Parsing & Chunking Pipeline

* **Decision**: Use **Docling** (`docling`) for structured document parsing combined with a token-aware chunker set to **600 tokens** chunk size with **120 tokens** sliding overlap.
* **Rationale**: Docling accurately extracts document layout, sections, tables, and exact physical page numbers across PDF, DOCX, and Markdown formats. Attaching `department_access` (inferred from `data/<department>/` directory structure), `source_file`, and `page_number` satisfies Principle III of the Constitution.
* **Alternatives Considered**:
  * *PyPDF / PDFMiner*: Rejected because they fail on complex multi-column layouts and don't natively extract table hierarchies.
  * *Unstructured.io*: High overhead and requires extensive external system dependencies.

## 2. Vector Store & Dynamic Metadata Filtering

* **Decision**: Use **ChromaDB** as the embedded, persistent vector database with pre-filtering on metadata fields.
* **Rationale**: ChromaDB supports persistent local storage without requiring external Docker services, provides native `$in` metadata filtering (`{"department_access": {"$in": allowed_depts}}`), and integrates cleanly with Python RAG pipelines.
* **Filtering Strategy**:
  * `Public` queries → `where={"department_access": {"$in": ["Public"]}}`
  * `Finance-Manager` queries → `where={"department_access": {"$in": ["Finance", "Public"]}}`
  * `Engineering-Lead` queries → `where={"department_access": {"$in": ["Engineering", "Public"]}}`
  * `Admin` queries → no filter or `where={"department_access": {"$in": ["Engineering", "Finance", "Public"]}}`
* **Alternatives Considered**:
  * *FAISS*: Requires custom metadata indexing and manual post-filtering logic which risks leaking or reducing top-k counts.
  * *Qdrant / Pinecone Cloud*: Adds external service dependencies and network overhead for local development and demos.

## 3. Black-Box Guardrail & Scope Classification ("Chipotle-Style")

* **Decision**: Implement a two-phase security guardrail:
  1. **Phase 1 (Regex & Pattern Gate)**: Fast detection of prompt injection patterns (e.g., `ignore previous instructions`, `system prompt reveal`) and sensitive PII formats (e.g., SSN, credit cards) for sanitization.
  2. **Phase 2 (Fast LLM Intent Classifier)**: Low-temperature structured JSON classifier evaluating if the query is an in-scope corporate document lookup or out-of-scope (e.g., general programming, trivia, casual chit-chat).
* **Refusal Message**: Standardized canned response:
  > *"I am an enterprise assistant dedicated solely to searching authorized corporate documentation. I cannot assist with general programming, casual conversation, or external topics."*
* **Rationale**: Eliminates unnecessary vector search and LLM generation costs for off-topic requests and prevents prompt exploitation.

## 4. Grounded Response Generation & Refusal Strategy

* **Decision**: Prompt-enforced context grounding with deterministic citation mapping and standardized refusal fallback.
* **Prompt Contract**: LLM is instructed to answer strictly using provided context snippets, including inline citations formatted as `[Source: <filename>, Page: <page_number>]`.
* **Refusal Fallback**: If retrieved context is empty, below relevance thresholds, or lacks supporting evidence, LLM outputs:
  > *"I do not have sufficient information in the authorized corporate documents to answer this question."*
* **Alternatives Considered**:
  * *Hard distance cutoff only*: Discards semantically weak matches that might contain exact keyword hits. Prompt-level grounding + fallback yields superior accuracy.

## 5. UI Architecture & Dashboard (Streamlit + Plotly)

* **Decision**: Modern multi-tab **Streamlit** application with **Plotly** visualizations.
* **Layout**:
  * **Sidebar**: Role Switcher (`Public`, `Finance-Manager`, `Engineering-Lead`, `Admin`), API Key inputs, Model selector, and Similarity Top-K slider.
  * **Tab 1 (Conversational Assistant)**: Streaming chat bubbles with citation badges and collapsible raw chunk preview expanders.
  * **Tab 2 (Evaluation Visualizer)**: Interactive Plotly bar charts depicting Ragas metrics (*Faithfulness*, *Answer Relevance*, *Context Recall*) by department, metric gauges, and sample evaluation records loaded from `eval_results.json`.

## 6. Evaluation Framework (Ragas Benchmarking)

* **Decision**: Offline Ragas benchmark suite with pre-computed baseline records (`data/eval/eval_results.json`) and an executable CLI runner (`src.eval.run_benchmark`).
* **Metrics**:
  * **Faithfulness**: Measures if the answer is grounded in retrieved context (hallucination defense).
  * **Answer Relevance**: Measures if the answer directly answers the query without extraneous facts.
  * **Context Recall**: Measures if all necessary ground-truth facts were retrieved.
