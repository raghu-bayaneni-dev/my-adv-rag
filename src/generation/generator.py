import os
import re
import logging
from typing import List, Tuple
from src.config.settings import Settings
from src.models.document import DocumentChunk
from src.models.query import Citation
from src.generation.prompts import GROUNDED_SYSTEM_PROMPT, build_rag_prompt

logger = logging.getLogger(__name__)

STANDARD_REFUSAL_MESSAGE = "I do not have sufficient information in the authorized corporate documents to answer this question."


class LLMGenerator:
    """
    LLM Generator using LiteLLM/Google GenAI with strict prompt groundedness
    and citation extraction.
    """
    def __init__(self, settings: Settings, model_name: str = None, api_key: str = None):
        self.settings = settings
        self.model_name = model_name or settings.default_llm_model
        self.api_key = (
            api_key 
            or settings.groq_api_key 
            or os.getenv("GROQ_API_KEY") 
            or settings.gemini_api_key 
            or os.getenv("GEMINI_API_KEY") 
            or settings.openai_api_key
        )

    def generate_response(self, query: str, chunks: List[DocumentChunk]) -> Tuple[str, List[Citation], bool]:
        """
        Generates grounded response and returns (answer_text, citations, is_refusal).
        """
        if not chunks:
            return STANDARD_REFUSAL_MESSAGE, [], True

        prompt = build_rag_prompt(query, chunks)
        
        try:
            from litellm import completion
            messages = [
                {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.1,
            }
            if self.api_key:
                kwargs["api_key"] = self.api_key

            response = completion(**kwargs)
            raw_answer = response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM API call failed or keys absent, using rule-based synthesis: {e}")
            raw_answer = self._synthesize_fallback(query, chunks)

        is_refusal = (
            STANDARD_REFUSAL_MESSAGE.lower() in raw_answer.lower()
            or "do not have sufficient information" in raw_answer.lower()
        )

        citations = self._extract_citations(chunks)
        return raw_answer, citations, is_refusal

    def _extract_citations(self, chunks: List[DocumentChunk]) -> List[Citation]:
        """Maps retrieved chunks to structured citations."""
        citations = []
        seen = set()
        for chunk in chunks:
            key = (chunk.metadata.source_file, chunk.metadata.page_number)
            if key not in seen:
                seen.add(key)
                preview = (chunk.text[:120] + "...") if len(chunk.text) > 120 else chunk.text
                citations.append(Citation(
                    source_file=chunk.metadata.source_file,
                    page_number=chunk.metadata.page_number,
                    department=chunk.metadata.department_access,
                    chunk_preview=preview
                ))
        return citations

    def _synthesize_fallback(self, query: str, chunks: List[DocumentChunk]) -> str:
        """Deterministic synthesis for offline test execution without external API."""
        if not chunks:
            return STANDARD_REFUSAL_MESSAGE

        top_chunk = chunks[0]
        src = top_chunk.metadata.source_file
        page = top_chunk.metadata.page_number
        return f"Based on authorized documents: {top_chunk.text} [Doc: {src}, Page: {page}]"
