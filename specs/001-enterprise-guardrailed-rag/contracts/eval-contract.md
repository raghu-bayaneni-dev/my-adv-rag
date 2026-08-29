# Interface Contract: Evaluation Benchmark & Metrics Visualizer

**Component**: `src.eval` & `app.py (Tab 2)` | **Type**: Python Evaluation & Visualization Service

---

## 1. Overview

Defines the benchmark dataset schema, offline runner command contract, and the metric visualization contract for Tab 2 of the Streamlit dashboard.

---

## 2. CLI Runner Contract

```bash
# Execute offline evaluation benchmark against golden test dataset
python -m src.eval.benchmark_runner --dataset data/eval/golden_dataset.json --output data/eval/eval_results.json
```

### Input Golden Dataset Schema (`data/eval/golden_dataset.json`)

```json
[
  {
    "question_id": "eval-eng-001",
    "question": "What is the retry limit and backoff multiplier for our payment processing service?",
    "department": "Engineering",
    "ground_truth": "The payment processing service enforces a maximum of 3 retries with exponential backoff multiplier of 2.0.",
    "role_required": "Engineering-Lead"
  }
]
```

### Output Evaluation Results Schema (`data/eval/eval_results.json`)

```json
{
  "timestamp": "2026-08-28T12:00:00Z",
  "total_samples": 15,
  "mean_faithfulness": 0.98,
  "mean_answer_relevance": 0.94,
  "mean_context_recall": 0.96,
  "by_department": {
    "Engineering": { "faithfulness": 0.99, "answer_relevance": 0.95, "context_recall": 0.97 },
    "Finance": { "faithfulness": 0.97, "answer_relevance": 0.93, "context_recall": 0.95 },
    "Public": { "faithfulness": 0.98, "answer_relevance": 0.94, "context_recall": 0.96 }
  },
  "samples": [...]
}
```

---

## 3. Streamlit Visualizer Contract (Tab 2)

* **Component**: `render_eval_dashboard(eval_data: BenchmarkReport)`
* **Charts Rendered**:
  1. **Metric Overview Cards**: Large KPIs for Average Faithfulness, Answer Relevance, and Context Recall.
  2. **Department Comparison Bar Chart**: Plotly grouped bar chart comparing the 3 Ragas metrics across Engineering, Finance, and Public.
  3. **Sample Drill-Down Table**: Interactive data table displaying individual test questions, retrieved context chunks, generated answers, and per-question score breakdowns.
