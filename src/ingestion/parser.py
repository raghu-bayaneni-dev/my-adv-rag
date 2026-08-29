import os
import re
from pathlib import Path
from typing import List, Dict, Any


class DocumentParser:
    """
    Document parser utilizing Docling when available with robust fallback parsers
    for standard PDF, Markdown, and Text files. Extracts text and page structure.
    """
    def __init__(self):
        self._docling_available = False
        try:
            from docling.document_converter import DocumentConverter
            self._converter = DocumentConverter()
            self._docling_available = True
        except ImportError:
            self._converter = None

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parses a document and returns a list of page objects:
        [{"page_number": 1, "text": "...", "metadata": {...}}]
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext in [".md", ".txt"]:
            return self._parse_text_file(path)
        elif ext == ".pdf":
            return self._parse_pdf_file(path)
        else:
            return self._parse_generic_file(path)

    def _parse_text_file(self, path: Path) -> List[Dict[str, Any]]:
        content = path.read_text(encoding="utf-8", errors="replace")
        # Split by explicit pagebreak comments if present, otherwise treat as page 1
        pages = re.split(r'<!--\s*pagebreak\s*-->', content, flags=re.IGNORECASE)
        results = []
        for idx, page_content in enumerate(pages, start=1):
            cleaned = page_content.strip()
            if cleaned:
                results.append({
                    "page_number": idx,
                    "text": cleaned,
                    "metadata": {"source": str(path.name)}
                })
        if not results:
            results.append({"page_number": 1, "text": "", "metadata": {"source": str(path.name)}})
        return results

    def _parse_pdf_file(self, path: Path) -> List[Dict[str, Any]]:
        # If Docling is available, attempt Docling conversion
        if self._docling_available and self._converter:
            try:
                conv_res = self._converter.convert(str(path))
                doc = conv_res.document
                # Export markdown or page-wise text
                md_text = doc.export_to_markdown()
                return self._parse_text_file_string(md_text, path.name)
            except Exception:
                pass  # Fall back to PyPDF

        # PyPDF fallback
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            results = []
            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                cleaned = text.strip()
                if cleaned:
                    results.append({
                        "page_number": idx,
                        "text": cleaned,
                        "metadata": {"source": str(path.name)}
                    })
            if not results:
                results.append({"page_number": 1, "text": "", "metadata": {"source": str(path.name)}})
            return results
        except Exception as e:
            raise RuntimeError(f"Failed to parse PDF {path.name}: {e}")

    def _parse_generic_file(self, path: Path) -> List[Dict[str, Any]]:
        content = path.read_text(encoding="utf-8", errors="replace")
        return [{"page_number": 1, "text": content.strip(), "metadata": {"source": str(path.name)}}]

    def _parse_text_file_string(self, content: str, source_name: str) -> List[Dict[str, Any]]:
        pages = re.split(r'<!--\s*pagebreak\s*-->', content, flags=re.IGNORECASE)
        results = []
        for idx, page_content in enumerate(pages, start=1):
            cleaned = page_content.strip()
            if cleaned:
                results.append({
                    "page_number": idx,
                    "text": cleaned,
                    "metadata": {"source": source_name}
                })
        return results
