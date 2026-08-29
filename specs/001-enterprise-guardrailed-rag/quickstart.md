# Quickstart Validation Guide: Enterprise Guardrailed Multi-Department RAG System

**Feature**: `001-enterprise-guardrailed-rag` | **Date**: 2026-08-28

This guide provides end-to-end instructions to set up, ingest sample documents, run validation tests, and launch the Streamlit application.

---

## 1. Prerequisites & Environment Setup

```bash
# 1. Ensure Python 3.11+ is installed
python3 --version

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install project dependencies
pip install -r requirements.txt

# 4. Configure environment variables (Pydantic Settings)
cp .env.example .env
# Edit .env with your LLM API keys (OpenAI / Gemini / Anthropic)
```

---

## 2. Ingest Sample Multi-Department Documents

```bash
# Ingest PDF/Markdown documents from data/engineering, data/finance, data/public
python -m src.ingestion.pipeline --data-dir data/ --chunk-size 600 --overlap 120
```

**Expected Output**:
```text
[INFO] Scanning directory: data/
[INFO] Ingesting Engineering documents from data/engineering/... (12 chunks)
[INFO] Ingesting Finance documents from data/finance/... (18 chunks)
[INFO] Ingesting Public documents from data/public/... (8 chunks)
[SUCCESS] Ingested 38 total chunks into ChromaDB with constitutional metadata.
```

---

## 3. Run Automated Validation & RBAC Tests

```bash
# Run unit & integration test suites
pytest tests/ -v
```

**Validation Assertions Checked**:
* ✅ `tests/test_rbac.py`: Asserts `Public` queries return 0 `Finance`/`Engineering` chunks.
* ✅ `tests/test_guardrails.py`: Asserts out-of-scope coding queries trigger canned refusal.
* ✅ `tests/test_grounding.py`: Asserts unanswerable questions gracefully return standard refusal without hallucinating.
* ✅ `tests/test_config.py`: Asserts Pydantic Settings fails fast on missing critical configurations.

---

## 4. Run Offline Benchmark Suite

```bash
# Execute offline Ragas evaluation against golden test dataset
python -m src.eval.benchmark_runner --dataset data/eval/golden_dataset.json --output data/eval/eval_results.json
```

---

## 5. Launch Modern Streamlit Dashboard

```bash
streamlit run app.py
```

* **Sidebar**: Select `Active User Role` (`Public`, `Finance-Manager`, `Engineering-Lead`, `Admin`).
* **Tab 1**: Ask queries (e.g., *"What were the Q3 financial revenue figures?"* as `Public` vs. `Finance-Manager`).
* **Tab 2**: View Plotly evaluation charts comparing Faithfulness, Relevance, and Recall across departments.
