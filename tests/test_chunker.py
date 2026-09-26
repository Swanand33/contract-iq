"""Tests for the section-aware chunker."""

import pytest

from app.ingestion.parser import Section
from app.ingestion.chunker import Chunk, chunk_section, chunk_sections


def _make_section(
    title: str = "Definitions",
    content: str = "Some content.",
    section_number: str = "1",
    document_name: str = "test_contract.md",
    document_type: str = "NDA",
) -> Section:
    """Helper to build a Section for testing."""
    return Section(
        title=title,
        content=content,
        level=2,
        section_number=section_number,
        document_name=document_name,
        document_type=document_type,
        parties=["Acme Corp", "Beta Inc"],
        agreement_number="AGR-001",
        effective_date="2024-01-01",
    )


class TestChunkSection:
    def test_small_section_stays_whole(self):
        section = _make_section(content="Short clause content.")
        chunks = chunk_section(section, chunk_size=800)

        assert len(chunks) == 1
        assert "Short clause content." in chunks[0].text
        assert chunks[0].metadata["document_name"] == "test_contract.md"

    def test_large_section_splits(self):
        # Create content that exceeds chunk_size
        paragraphs = [f"Paragraph {i}. " * 20 for i in range(10)]
        content = "\n\n".join(paragraphs)

        section = _make_section(content=content)
        chunks = chunk_section(section, chunk_size=200, chunk_overlap=50)

        assert len(chunks) > 1

    def test_chunk_has_section_header(self):
        section = _make_section(
            title="Payment Terms",
            section_number="3",
            document_type="SaaS Agreement",
        )
        chunks = chunk_section(section, chunk_size=800)

        # The header should be prepended
        assert "[SaaS Agreement] Section 3: Payment Terms" in chunks[0].text

    def test_chunk_metadata_preserved(self):
        section = _make_section(
            document_name="nda_acme.md",
            document_type="NDA",
            section_number="5",
            title="Confidentiality",
        )
        chunks = chunk_section(section, chunk_size=800)

        meta = chunks[0].metadata
        assert meta["document_name"] == "nda_acme.md"
        assert meta["document_type"] == "NDA"
        assert meta["section_number"] == "5"
        assert meta["section_title"] == "Confidentiality"
        assert meta["parties"] == "Acme Corp, Beta Inc"

    def test_chunk_id_deterministic(self):
        section = _make_section(
            document_name="test.md", section_number="2"
        )
        chunks = chunk_section(section, chunk_size=800)

        expected_id = "test.md_s2_c0"
        assert chunks[0].id == expected_id

        # Same input should produce same ID
        chunks2 = chunk_section(section, chunk_size=800)
        assert chunks2[0].id == expected_id

    def test_chunk_index_increments(self):
        paragraphs = [f"Content block {i}. " * 30 for i in range(5)]
        content = "\n\n".join(paragraphs)

        section = _make_section(content=content, section_number="1")
        chunks = chunk_section(section, chunk_size=200, chunk_overlap=50)

        for i, chunk in enumerate(chunks):
            assert chunk.metadata["chunk_index"] == i

    def test_empty_section_returns_empty(self):
        section = _make_section(content="")
        chunks = chunk_section(section, chunk_size=800)
        assert chunks == []


class TestChunkSections:
    def test_multiple_sections(self):
        sections = [
            _make_section(title="Terms", section_number="1", content="Term content."),
            _make_section(title="Payment", section_number="2", content="Payment content."),
            _make_section(title="Liability", section_number="3", content="Liability content."),
        ]
        chunks = chunk_sections(sections)

        assert len(chunks) == 3
        # Each chunk should have its own section metadata
        section_nums = [c.metadata["section_number"] for c in chunks]
        assert section_nums == ["1", "2", "3"]

    def test_empty_list(self):
        assert chunk_sections([]) == []
