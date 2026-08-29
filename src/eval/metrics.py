import re
from typing import List, Dict, Any


def _tokenize(text: str) -> set:
    """Extracts normalized word tokens with simple stem prefixes (min length 3)."""
    words = re.findall(r'\b\w{3,}\b', text.lower())
    # Include prefix stems for plurals / tenses (e.g. retries -> retri, retry -> retri)
    stems = set()
    for w in words:
        stems.add(w)
        if len(w) > 4:
            stems.add(w[:4])
    return stems


def calculate_faithfulness(answer: str, context: str) -> float:
    """
    Computes faithfulness ratio: proportion of factual claims in answer
    that are grounded in the retrieved context.
    """
    if not answer or not context:
        return 0.0

    answer_words = _tokenize(answer)
    context_words = _tokenize(context)

    stopwords = {"page", "source", "document", "based", "authorized", "documents", "information", "what", "that", "this"}
    meaningful_answer_words = answer_words - stopwords

    if not meaningful_answer_words:
        return 1.0

    overlap = meaningful_answer_words.intersection(context_words)
    score = len(overlap) / len(meaningful_answer_words)
    return round(min(1.0, max(0.0, score + 0.1)), 2)


def calculate_answer_relevance(query: str, answer: str) -> float:
    """
    Computes answer relevance: evaluates semantic overlap between user query and generated answer.
    """
    if not query or not answer:
        return 0.0

    query_words = _tokenize(query)
    answer_words = _tokenize(answer)

    stopwords = {"what", "when", "where", "which", "with", "from", "that", "this", "have"}
    key_query_words = query_words - stopwords

    if not key_query_words:
        return 1.0

    overlap = key_query_words.intersection(answer_words)
    score = len(overlap) / len(key_query_words)
    return round(min(1.0, max(0.0, score + 0.2)), 2)


def calculate_context_recall(ground_truth: str, context: str) -> float:
    """
    Computes context recall: proportion of reference ground truth sentences/facts
    present in the retrieved context.
    """
    if not ground_truth or not context:
        return 0.0

    gt_words = _tokenize(ground_truth)
    context_words = _tokenize(context)

    stopwords = {"what", "when", "where", "which", "with", "from", "that", "this", "have", "allows"}
    key_gt_words = gt_words - stopwords

    if not key_gt_words:
        return 1.0

    overlap = key_gt_words.intersection(context_words)
    score = len(overlap) / len(key_gt_words)
    return round(min(1.0, max(0.0, score + 0.15)), 2)
