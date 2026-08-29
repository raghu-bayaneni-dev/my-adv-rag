from typing import List, Dict, Any
from pydantic import BaseModel, Field


class EvalSample(BaseModel):
    """Single question evaluation record for Ragas benchmarking."""
    question_id: str = Field(..., description="Unique test case identifier")
    question: str = Field(..., description="Test query prompt")
    ground_truth: str = Field(..., description="Factual reference answer")
    department: str = Field(..., description="Associated department (Engineering, Finance, Public)")
    role_required: str = Field(..., description="Role needed to retrieve sufficient context")
    contexts: List[str] = Field(default_factory=list, description="Retrieved context chunks")
    generated_answer: str = Field(default="", description="System generated response")
    faithfulness: float = Field(..., ge=0.0, le=1.0, description="Ragas faithfulness score")
    answer_relevance: float = Field(..., ge=0.0, le=1.0, description="Ragas answer relevance score")
    context_recall: float = Field(..., ge=0.0, le=1.0, description="Ragas context recall score")


class BenchmarkReport(BaseModel):
    """Aggregated offline evaluation report for Tab 2 visualization."""
    timestamp: str = Field(..., description="ISO 8601 execution timestamp")
    total_samples: int = Field(..., ge=1, description="Number of evaluated test cases")
    mean_faithfulness: float = Field(..., ge=0.0, le=1.0, description="Average faithfulness across dataset")
    mean_answer_relevance: float = Field(..., ge=0.0, le=1.0, description="Average answer relevance across dataset")
    mean_context_recall: float = Field(..., ge=0.0, le=1.0, description="Average context recall across dataset")
    by_department: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Department breakdown of scores (Engineering, Finance, Public)"
    )
    samples: List[EvalSample] = Field(default_factory=list, description="Per-sample evaluation details")
