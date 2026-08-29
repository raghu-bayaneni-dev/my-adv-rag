import os
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional
from src.config.settings import get_settings
from src.models.document import Department, ChunkMetadata, DocumentChunk
from src.ingestion.parser import DocumentParser
from src.ingestion.chunker import TokenChunker
from src.retrieval.vector_store import VectorStoreService
from src.retrieval.retriever import DefaultEmbeddingService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IngestionPipeline")


class IngestionPipeline:
    """
    Orchestrates scanning, parsing, chunking, and constitutional metadata validation
    for multi-department documents.
    """
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 120):
        self.parser = DocumentParser()
        self.chunker = TokenChunker(target_chunk_tokens=chunk_size, overlap_tokens=chunk_overlap)

    def process_directory(self, base_dir: str) -> List[DocumentChunk]:
        """
        Scans department directories (engineering, finance, public) and converts files
        into validated DocumentChunk objects.
        """
        base_path = Path(base_dir)
        if not base_path.exists():
            raise FileNotFoundError(f"Base directory does not exist: {base_dir}")

        all_chunks: List[DocumentChunk] = []

        dept_mappings = {
            "engineering": Department.ENGINEERING,
            "finance": Department.FINANCE,
            "public": Department.PUBLIC,
        }

        for folder_name, dept_enum in dept_mappings.items():
            dept_path = base_path / folder_name
            if not dept_path.exists() or not dept_path.is_dir():
                continue

            for file_path in dept_path.glob("**/*"):
                if file_path.is_file() and file_path.suffix.lower() in [".md", ".txt", ".pdf", ".docx"]:
                    try:
                        file_chunks = self.process_file(str(file_path), dept_enum)
                        all_chunks.extend(file_chunks)
                        logger.info(f"Ingested {len(file_chunks)} chunks from {file_path.name} [{dept_enum.value}]")
                    except Exception as e:
                        logger.warning(f"Skipping malformed or unreadable file {file_path.name}: {e}")

        return all_chunks

    def process_file(self, file_path: str, department: Department) -> List[DocumentChunk]:
        """
        Parses a single file, chunks it, and attaches constitutional metadata.
        """
        pages = self.parser.parse_file(file_path)
        source_name = Path(file_path).name
        file_chunks: List[DocumentChunk] = []

        for page in pages:
            page_number = page.get("page_number", 1)
            raw_text = page.get("text", "")
            if not raw_text.strip():
                continue

            text_chunks = self.chunker.chunk_text(raw_text)
            for idx, text_seg in enumerate(text_chunks):
                metadata = ChunkMetadata(
                    department_access=department,
                    source_file=source_name,
                    page_number=page_number,
                    extra={"chunk_index": idx}
                )
                chunk_id = DocumentChunk.generate_chunk_id(
                    source_file=source_name,
                    page_number=page_number,
                    chunk_index=idx,
                    text=text_seg
                )
                file_chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    text=text_seg,
                    metadata=metadata
                ))

        return file_chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest multi-department documents into ChromaDB.")
    parser.add_argument("--data-dir", default="data", help="Directory containing departmental document folders")
    parser.add_argument("--chunk-size", type=int, default=600, help="Target chunk size in tokens")
    parser.add_argument("--overlap", type=int, default=120, help="Chunk sliding overlap in tokens")
    args = parser.parse_args()

    settings = get_settings()
    pipeline = IngestionPipeline(chunk_size=args.chunk_size, chunk_overlap=args.overlap)
    chunks = pipeline.process_directory(args.data_dir)

    embedding_service = DefaultEmbeddingService(model_name=settings.embedding_model)
    vector_store = VectorStoreService(settings=settings, embedding_service=embedding_service)
    vector_store.add_chunks(chunks)
    logger.info(f"[SUCCESS] Ingested {len(chunks)} total chunks into ChromaDB.")
