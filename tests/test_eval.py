import json
import pytest
from src.models.evaluation import BenchmarkReport, EvalSample
from src.eval.metrics import calculate_faithfulness, calculate_answer_relevance, calculate_context_recall


def test_eval_metrics_calculation():
    """Verify formula and scoring logic for Ragas evaluation metrics."""
    context = "The payment processing service enforces maximum retry limit of 3 attempts."
    answer = "The maximum retry limit for payment processing is 3 attempts."
    ground_truth = "The payment processing service allows up to 3 retries."

    faithfulness = calculate_faithfulness(answer=answer, context=context)
    assert 0.8 <= faithfulness <= 1.0

    relevance = calculate_answer_relevance(query="What is the retry limit?", answer=answer)
    assert 0.8 <= relevance <= 1.0

    recall = calculate_context_recall(ground_truth=ground_truth, context=context)
    assert 0.8 <= recall <= 1.0


def test_benchmark_report_serialization(tmp_path):
    """Verify BenchmarkReport schema parses and serializes evaluation results properly."""
    eval_file = "data/eval/eval_results.json"
    with open(eval_file, "r") as f:
        data = json.load(f)
    
    report = BenchmarkReport.model_validate(data)
    assert report.total_samples == 6
    assert report.mean_faithfulness >= 0.90
    assert "Engineering" in report.by_department
    assert "Finance" in report.by_department
    assert "Public" in report.by_department
