"""
Tests for the retrieval layer (context building and citation formatting).

These tests exercise the pure-logic methods of ContractRetriever
without requiring ChromaDB or OpenAI — they work with pre-built
result dicts, the same format the vector store returns.
"""

import pytest
import sys
from unittest.mock import MagicMock

# Mock heavy dependencies so tests run without chromadb/openai installed
sys.modules.setdefault("chromadb", MagicMock())
sys.modules.setdefault("chromadb.config", MagicMock())
sys.modules.setdefault("openai", MagicMock())

from app.retrieval.search import ContractRetriever


def _make_results(n: int = 3) -> list[dict]:
    """Build fake retrieval results for testing context/citation formatting."""
    results = []
    for i in range(n):
        results.append(
            {
                "text": f"Chunk text for result {i + 1}.",
                "metadata": {
                    "document_name": f"contract_{chr(65 + i)}.md",
                    "document_type": "NDA" if i % 2 == 0 else "SaaS Agreement",
                    "section_title": f"Section Title {i + 1}",
                    "section_number": str(i + 1),
                    "chunk_index": 0,
                    "parties": "Acme / Beta",
                },
                "distance": 0.2 + i * 0.05,
                "relevance_score": round(0.8 - i * 0.05, 4),
            }
        )
    return results


@pytest.fixture
def retriever():
    """Create a ContractRetriever without initializing the vector store."""
    r = object.__new__(ContractRetriever)
    return r


class TestBuildContext:
    def test_formats_source_references(self, retriever):
        results = _make_results(2)
        context = retriever.build_context(results)

        assert "[Source 1]" in context
        assert "[Source 2]" in context
        assert "contract_A.md" in context

    def test_includes_section_info(self, retriever):
        results = _make_results(1)
        context = retriever.build_context(results)

        assert "Section 1: Section Title 1" in context

    def test_includes_document_type(self, retriever):
        results = _make_results(1)
        context = retriever.build_context(results)

        assert "NDA" in context

    def test_includes_chunk_text(self, retriever):
        results = _make_results(1)
        context = retriever.build_context(results)

        assert "Chunk text for result 1." in context

    def test_separates_sources_with_dividers(self, retriever):
        results = _make_results(3)
        context = retriever.build_context(results)

        assert context.count("---") >= 2

    def test_deduplicates_overlapping_chunks(self, retriever):
        results = _make_results(2)
        # Make both results point to the same section (overlap)
        results[1]["metadata"]["document_name"] = results[0]["metadata"]["document_name"]
        results[1]["metadata"]["section_number"] = results[0]["metadata"]["section_number"]
        results[1]["metadata"]["chunk_index"] = results[0]["metadata"]["chunk_index"]

        context = retriever.build_context(results)

        # Should only have one source reference (deduped)
        assert context.count("[Source") == 1

    def test_empty_results(self, retriever):
        context = retriever.build_context([])
        assert context == ""


class TestGetSourceCitations:
    def test_returns_citations(self, retriever):
        results = _make_results(3)
        citations = retriever.get_source_citations(results)

        assert len(citations) == 3
        assert citations[0]["source_number"] == 1
        assert citations[0]["document"] == "contract_A.md"
        assert citations[0]["relevance_score"] == 0.8

    def test_citation_structure(self, retriever):
        results = _make_results(1)
        citations = retriever.get_source_citations(results)

        c = citations[0]
        assert "source_number" in c
        assert "document" in c
        assert "document_type" in c
        assert "section" in c
        assert "section_number" in c
        assert "relevance_score" in c

    def test_deduplicates_by_doc_and_section(self, retriever):
        results = _make_results(2)
        results[1]["metadata"]["document_name"] = results[0]["metadata"]["document_name"]
        results[1]["metadata"]["section_number"] = results[0]["metadata"]["section_number"]

        citations = retriever.get_source_citations(results)

        assert len(citations) == 1

    def test_empty_results(self, retriever):
        citations = retriever.get_source_citations([])
        assert citations == []
