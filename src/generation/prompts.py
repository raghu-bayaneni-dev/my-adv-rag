from typing import List
from src.models.document import DocumentChunk

GROUNDED_SYSTEM_PROMPT = """You are an Enterprise Corporate Knowledge Assistant.
Your job is to answer the user's question strictly and exclusively using the provided document context below.

CONSTITUTIONAL RULES (NON-NEGOTIABLE):
1. Strictly Grounded: Every factual statement you make must be derived directly from the provided context chunks.
2. In-Text Citations: For every factual claim, cite the source file and page using this format: [Doc: <source_file>, Page: <page_number>].
3. Missing / Insufficient Evidence: If the provided context is empty or does NOT contain sufficient evidence to answer the query, DO NOT hallucinate, assume, or bring in external knowledge. Instead, decline gracefully with:
   "I do not have sufficient information in the authorized corporate documents to answer this question."
4. Partial Evidence: If the context answers only part of the question, answer that grounded part with citations, and explicitly state what could not be answered due to lack of documentation.
"""

def build_rag_prompt(query: str, chunks: List[DocumentChunk]) -> str:
    """Formats context chunks and query into synthesis prompt."""
    if not chunks:
        context_block = "NO AUTHORIZED CONTEXT FOUND."
    else:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.metadata.source_file
            page = chunk.metadata.page_number
            dept = chunk.metadata.department_access.value
            context_parts.append(
                f"--- CHUNK {i} [Source: {source} | Page: {page} | Dept: {dept}] ---\n{chunk.text}\n"
            )
        context_block = "\n".join(context_parts)

    return f"""CONTEXT DOCUMENTS:
{context_block}

USER QUESTION:
{query}

ANSWER (Grounded strictly with citations [Doc: <file>, Page: <page>] or standard refusal):
"""
