from typing import List, Optional
from pydantic import BaseModel, Field
from src.models.document import Department
from src.models.security import UserRole


class Citation(BaseModel):
    """Grounding citation for a statement in the answer."""
    source_file: str = Field(..., description="Source document file name")
    page_number: int = Field(..., ge=1, description="Source page number")
    department: Department = Field(..., description="Department owner of the cited chunk")
    chunk_preview: str = Field(..., description="Snippet of supporting text excerpt")
    score: Optional[float] = Field(default=None, description="Similarity score")


class QueryRequest(BaseModel):
    """Incoming user query payload."""
    query_text: str = Field(..., min_length=1, description="Raw user query string")
    user_role: UserRole = Field(default=UserRole.PUBLIC, description="Active user role for RBAC")
    top_k: int = Field(default=4, ge=1, le=10, description="Max chunks to retrieve")


class QueryResponse(BaseModel):
    """End-to-end RAG response."""
    query: str = Field(..., description="Original or sanitized user query")
    answer: str = Field(..., description="Grounded answer or polite refusal")
    user_role: UserRole = Field(..., description="Role under which query was evaluated")
    is_refusal: bool = Field(default=False, description="True if query declined or ungrounded")
    guardrail_triggered: bool = Field(default=False, description="True if blocked by pre-retrieval guardrail")
    citations: List[Citation] = Field(default_factory=list, description="List of source citations")
    latency_ms: float = Field(..., ge=0.0, description="Total execution time in milliseconds")
