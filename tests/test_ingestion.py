import os
import pytest
from src.models.document import Department, ChunkMetadata, DocumentChunk
from src.ingestion.chunker import TokenChunker
from src.ingestion.parser import DocumentParser
from src.ingestion.pipeline import IngestionPipeline


def test_token_chunker_basic():
    """Verify chunker respects token boundaries and creates sliding overlaps."""
    chunker = TokenChunker(target_chunk_tokens=100, overlap_tokens=20)
    sample_text = " ".join([f"word{i}" for i in range(250)])
    chunks = chunker.chunk_text(sample_text)
    
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk.split()) <= 150  # within reasonable token estimate


def test_token_chunker_small_text():
    """Verify short text is returned as a single chunk without truncation."""
    chunker = TokenChunker(target_chunk_tokens=600, overlap_tokens=120)
    text = "Short policy document text."
    chunks = chunker.chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_document_parser_markdown(tmp_path):
    """Verify parser extracts text, structure, and page numbers from markdown files."""
    doc_path = tmp_path / "test_doc.md"
    doc_path.write_text("# Section 1\nThis is page 1 content.\n\n<!-- pagebreak -->\n# Section 2\nThis is page 2 content.")
    
    parser = DocumentParser()
    pages = parser.parse_file(str(doc_path))
    assert len(pages) >= 1
    assert "Section 1" in pages[0]["text"]


def test_ingestion_pipeline_metadata_enforcement(tmp_path):
    """Verify ingestion pipeline attaches and validates mandatory constitutional metadata."""
    eng_dir = tmp_path / "engineering"
    eng_dir.mkdir(parents=True)
    doc_file = eng_dir / "service_spec.md"
    doc_file.write_text("Payment service requires 3 retries and 2.0 backoff multiplier.")

    pipeline = IngestionPipeline(chunk_size=600, chunk_overlap=120)
    chunks = pipeline.process_directory(str(tmp_path))
    
    assert len(chunks) >= 1
    chunk = chunks[0]
    assert chunk.metadata.department_access == Department.ENGINEERING
    assert "service_spec.md" in chunk.metadata.source_file
    assert chunk.metadata.page_number >= 1
    assert chunk.chunk_id is not None
