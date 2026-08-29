import hashlib
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class Department(str, Enum):
    """Authorized departmental boundaries."""
    ENGINEERING = "Engineering"
    FINANCE = "Finance"
    PUBLIC = "Public"


class ChunkMetadata(BaseModel):
    """
    Mandatory chunk metadata enforcing Constitution Principle III.
    Rejects any chunk missing department_access, source_file, or page_number.
    """
    department_access: Department = Field(
        ...,
        description="Department authorized to view this chunk (Constitutional requirement)"
    )
    source_file: str = Field(
        ...,
        min_length=1,
        description="Original source filename or path (Constitutional requirement)"
    )
    page_number: int = Field(
        ...,
        ge=1,
        description="Physical 1-indexed page number of the source document (Constitutional requirement)"
    )
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional non-critical metadata")

    @field_validator("source_file")
    @classmethod
    def validate_source_file(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_file cannot be empty or whitespace")
        return v.strip()


class DocumentChunk(BaseModel):
    """
    Segment of an ingested document with validated constitutional metadata.
    """
    chunk_id: str = Field(..., description="Deterministic unique identifier")
    text: str = Field(..., min_length=1, description="Extracted text chunk content")
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = Field(default=None, description="Dense vector embedding")

    @classmethod
    def generate_chunk_id(cls, source_file: str, page_number: int, chunk_index: int, text: str) -> str:
        """Generates deterministic SHA-256 hash ID to prevent duplicate ingestion."""
        raw_key = f"{source_file}:{page_number}:{chunk_index}:{text.strip()}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]
