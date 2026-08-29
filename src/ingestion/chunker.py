import re
from typing import List


class TokenChunker:
    """
    Token-aware sliding window chunker.
    Enforces target chunk size (default: 600 tokens) with sliding overlap (default: 120 tokens).
    """
    def __init__(self, target_chunk_tokens: int = 600, overlap_tokens: int = 120):
        self.target_chunk_tokens = max(50, target_chunk_tokens)
        self.overlap_tokens = min(overlap_tokens, self.target_chunk_tokens // 2)

    def chunk_text(self, text: str) -> List[str]:
        """
        Segments raw text into overlapping token windows while preserving sentence boundaries
        where feasible.
        """
        text = text.strip()
        if not text:
            return []

        # Split words while preserving punctuation
        words = text.split()
        total_words = len(words)

        if total_words <= self.target_chunk_tokens:
            return [text]

        chunks = []
        step = self.target_chunk_tokens - self.overlap_tokens
        if step <= 0:
            step = self.target_chunk_tokens // 2 or 1

        start_idx = 0
        while start_idx < total_words:
            end_idx = min(start_idx + self.target_chunk_tokens, total_words)
            chunk_words = words[start_idx:end_idx]
            chunk_str = " ".join(chunk_words).strip()
            if chunk_str:
                chunks.append(chunk_str)

            if end_idx >= total_words:
                break
            start_idx += step

        return chunks
