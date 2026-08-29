import os
import json
import argparse
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from src.config.settings import get_settings
from src.models.security import UserRole
from src.models.query import QueryRequest
from src.models.evaluation import EvalSample, BenchmarkReport
from src.eval.metrics import calculate_faithfulness, calculate_answer_relevance, calculate_context_recall
from src.retrieval.vector_store import VectorStoreService
from src.retrieval.retriever import RetrieverService, DefaultEmbeddingService
from src.generation.generator import LLMGenerator
from src.engine.rag_pipeline import RAGEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BenchmarkRunner")


def run_benchmark(dataset_path: str, output_path: str):
    """
    Executes offline evaluation benchmark across golden test cases
    and computes Faithfulness, Answer Relevance, and Context Recall.
    """
    logger.info(f"Loading benchmark dataset from {dataset_path}...")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    settings = get_settings()
    embedding_service = DefaultEmbeddingService(model_name=settings.embedding_model)
    vector_store = VectorStoreService(settings=settings, embedding_service=embedding_service)
    retriever = RetrieverService(vector_store=vector_store)
    generator = LLMGenerator(settings=settings)
    engine = RAGEngine(settings=settings, retriever=retriever, generator=generator)

    eval_samples: List[EvalSample] = []
    by_department: Dict[str, Dict[str, List[float]]] = {
        "Engineering": {"faithfulness": [], "answer_relevance": [], "context_recall": []},
        "Finance": {"faithfulness": [], "answer_relevance": [], "context_recall": []},
        "Public": {"faithfulness": [], "answer_relevance": [], "context_recall": []},
    }

    for case in test_cases:
        qid = case["question_id"]
        q_text = case["question"]
        gt = case["ground_truth"]
        dept = case["department"]
        role_str = case.get("role_required", "Admin")

        try:
            role = UserRole(role_str)
        except ValueError:
            role = UserRole.ADMIN

        logger.info(f"Evaluating {qid} [{dept} | Role: {role.value}]...")
        
        # Execute query
        req = QueryRequest(query_text=q_text, user_role=role, top_k=3)
        res = engine.query(req)

        # Extract contexts
        retrieved_chunks = retriever.retrieve(query=q_text, user_role=role, top_k=3)
        context_str = " ".join([c.text for c in retrieved_chunks])
        contexts_list = [c.text for c in retrieved_chunks]

        # Calculate metrics
        faith_score = calculate_faithfulness(answer=res.answer, context=context_str)
        rel_score = calculate_answer_relevance(query=q_text, answer=res.answer)
        rec_score = calculate_context_recall(ground_truth=gt, context=context_str)

        sample = EvalSample(
            question_id=qid,
            question=q_text,
            ground_truth=gt,
            department=dept,
            role_required=role.value,
            contexts=contexts_list,
            generated_answer=res.answer,
            faithfulness=faith_score,
            answer_relevance=rel_score,
            context_recall=rec_score
        )
        eval_samples.append(sample)

        # Record by department
        if dept in by_department:
            by_department[dept]["faithfulness"].append(faith_score)
            by_department[dept]["answer_relevance"].append(rel_score)
            by_department[dept]["context_recall"].append(rec_score)

    # Compute aggregates
    all_faith = [s.faithfulness for s in eval_samples] or [1.0]
    all_rel = [s.answer_relevance for s in eval_samples] or [1.0]
    all_rec = [s.context_recall for s in eval_samples] or [1.0]

    dept_summary = {}
    for d, scores in by_department.items():
        f_list = scores["faithfulness"] or [1.0]
        r_list = scores["answer_relevance"] or [1.0]
        c_list = scores["context_recall"] or [1.0]
        dept_summary[d] = {
            "faithfulness": round(sum(f_list) / len(f_list), 2),
            "answer_relevance": round(sum(r_list) / len(r_list), 2),
            "context_recall": round(sum(c_list) / len(c_list), 2)
        }

    report = BenchmarkReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_samples=len(eval_samples),
        mean_faithfulness=round(sum(all_faith) / len(all_faith), 2),
        mean_answer_relevance=round(sum(all_rel) / len(all_rel), 2),
        mean_context_recall=round(sum(all_rec) / len(all_rec), 2),
        by_department=dept_summary,
        samples=eval_samples
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    logger.info(f"[SUCCESS] Benchmark complete! Faithfulness: {report.mean_faithfulness}, Relevance: {report.mean_answer_relevance}, Recall: {report.mean_context_recall}")
    logger.info(f"Results saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run offline Ragas evaluation benchmark.")
    parser.add_argument("--dataset", default="data/eval/golden_dataset.json", help="Path to golden dataset")
    parser.add_argument("--output", default="data/eval/eval_results.json", help="Path to output results file")
    args = parser.parse_args()
    run_benchmark(args.dataset, args.output)
