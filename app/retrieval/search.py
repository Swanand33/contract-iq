"""
Retrieval layer — finds relevant contract sections for a query.

Combines vector similarity search with metadata filtering
to find the most relevant contract clauses.
"""

import logging
from typing import Optional

from app.database.vector_store import VectorStore
from app.config import settings

logger = logging.getLogger(__name__)


class ContractRetriever:
    """Retrieve relevant contract sections for a question."""

    def __init__(self, vector_store: VectorStore | None = None):
        self.vector_store = vector_store or VectorStore()

    def retrieve(
        self,
        query: str,
        top_k: int = settings.top_k,
        document_type: Optional[str] = None,
        document_name: Optional[str] = None,
    ) -> list[dict]:
        """
        Retrieve relevant chunks for a query.

        Supports optional filtering by document type or specific document.
        Returns chunks sorted by relevance score (highest first).
        """
        results = self.vector_store.search(
            query=query,
            top_k=top_k,
            document_type=document_type,
            document_name=document_name,
        )

        if not results:
            logger.info(f"No relevant chunks found for: {query[:80]}...")
            return []

        logger.info(
            f"Retrieved {len(results)} chunks for query "
            f"(top score: {results[0]['relevance_score']:.4f})"
        )

        return results

    def build_context(self, results: list[dict]) -> str:
        """
        Build a context string from retrieved chunks for the LLM prompt.

        Deduplicates overlapping content and formats source references.
        """
        if not results:
            return ""

        context_parts = []
        seen_sections = set()

        for i, result in enumerate(results, 1):
            meta = result["metadata"]
            section_key = (
                meta.get("document_name", ""),
                meta.get("section_number", ""),
                meta.get("chunk_index", 0),
            )

            # Skip duplicate sections (can happen with overlapping chunks)
            if section_key in seen_sections:
                continue
            seen_sections.add(section_key)

            # Build source reference
            source_ref = f"[Source {i}]"
            doc_name = meta.get("document_name", "Unknown Document")
            doc_type = meta.get("document_type", "Contract")
            section = meta.get("section_title", "")
            section_num = meta.get("section_number", "")

            header = f"{source_ref} {doc_type}: {doc_name}"
            if section_num and section:
                header += f" — Section {section_num}: {section}"
            elif section:
                header += f" — {section}"

            context_parts.append(f"{header}\n{result['text']}")

        return "\n\n---\n\n".join(context_parts)

    def get_source_citations(self, results: list[dict]) -> list[dict]:
        """Extract clean source citations from results."""
        citations = []
        seen = set()

        for i, result in enumerate(results, 1):
            meta = result["metadata"]
            doc_name = meta.get("document_name", "Unknown")

            # Deduplicate by document + section
            citation_key = (doc_name, meta.get("section_number", ""))
            if citation_key in seen:
                continue
            seen.add(citation_key)

            citations.append(
                {
                    "source_number": i,
                    "document": doc_name,
                    "document_type": meta.get("document_type", "Contract"),
                    "section": meta.get("section_title", ""),
                    "section_number": meta.get("section_number", ""),
                    "relevance_score": result["relevance_score"],
                }
            )

        return citations
