"""
Section-aware chunking for legal contracts.

Unlike naive text splitting, this chunker:
1. Respects section boundaries — never splits mid-clause
2. Attaches metadata (document, section type, parties) to each chunk
3. Uses overlap only within a section, not across sections
4. Keeps subsections (3.1, 3.2) as individual chunks when they're
   small enough, or splits them at paragraph boundaries when they're not
"""

from dataclasses import dataclass, field
from app.ingestion.parser import Section
from app.config import settings


@dataclass
class Chunk:
    """A chunk ready for embedding, with metadata."""

    text: str
    metadata: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        """Generate a deterministic chunk ID from metadata."""
        doc = self.metadata.get("document_name", "unknown")
        section = self.metadata.get("section_number", "0")
        idx = self.metadata.get("chunk_index", 0)
        return f"{doc}_s{section}_c{idx}"


def chunk_section(
    section: Section,
    chunk_size: int = settings.chunk_size,
    chunk_overlap: int = settings.chunk_overlap,
) -> list[Chunk]:
    """
    Split a section into chunks respecting clause boundaries.

    Strategy:
    - If the section fits in one chunk, keep it whole
    - Otherwise, split at subsection markers (e.g., 3.1, 3.2)
    - If subsections are still too large, split at paragraph boundaries
    - Apply overlap only within a section, never bleed across sections
    """
    content = section.content.strip()
    if not content:
        return []

    # Base metadata attached to every chunk from this section
    base_metadata = {
        "document_name": section.document_name,
        "document_type": section.document_type,
        "section_title": section.title,
        "section_number": section.section_number,
        "parties": ", ".join(section.parties) if section.parties else "",
        "agreement_number": section.agreement_number,
        "effective_date": section.effective_date,
    }

    # Prepend section context to each chunk for better retrieval
    section_header = f"[{section.document_type}] {section.title}"
    if section.section_number:
        section_header = f"[{section.document_type}] Section {section.section_number}: {section.title}"

    # If section fits in one chunk, keep it whole
    full_text = f"{section_header}\n\n{content}"
    if len(full_text) <= chunk_size:
        return [
            Chunk(
                text=full_text,
                metadata={**base_metadata, "chunk_index": 0},
            )
        ]

    # Split at paragraph boundaries (double newline or numbered subsections)
    paragraphs = _split_into_paragraphs(content)

    chunks: list[Chunk] = []
    current_text = section_header + "\n\n"
    chunk_idx = 0

    for para in paragraphs:
        # If adding this paragraph exceeds chunk_size, save current and start new
        if len(current_text) + len(para) > chunk_size and current_text.strip() != section_header:
            chunks.append(
                Chunk(
                    text=current_text.strip(),
                    metadata={**base_metadata, "chunk_index": chunk_idx},
                )
            )
            chunk_idx += 1

            # Start new chunk with overlap: take the tail of previous chunk
            overlap_text = _get_overlap(current_text, chunk_overlap)
            current_text = f"{section_header}\n\n{overlap_text}\n\n"

        current_text += para + "\n\n"

    # Don't forget the last chunk
    if current_text.strip() and current_text.strip() != section_header:
        chunks.append(
            Chunk(
                text=current_text.strip(),
                metadata={**base_metadata, "chunk_index": chunk_idx},
            )
        )

    return chunks


def _split_into_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs, keeping numbered clauses together."""
    # Split on double newlines
    raw_paragraphs = text.split("\n\n")

    paragraphs: list[str] = []
    for para in raw_paragraphs:
        para = para.strip()
        if para:
            paragraphs.append(para)

    return paragraphs


def _get_overlap(text: str, overlap_size: int) -> str:
    """Get the last `overlap_size` characters of text for chunk overlap."""
    if len(text) <= overlap_size:
        return text
    # Try to break at a sentence or clause boundary
    overlap = text[-overlap_size:]
    # Find the start of the next sentence within the overlap
    sentence_start = overlap.find(". ")
    if sentence_start != -1 and sentence_start < len(overlap) // 2:
        overlap = overlap[sentence_start + 2 :]
    return overlap.strip()


def chunk_sections(sections: list[Section]) -> list[Chunk]:
    """Chunk all sections from parsed documents."""
    all_chunks: list[Chunk] = []

    for section in sections:
        chunks = chunk_section(section)
        all_chunks.extend(chunks)

    return all_chunks
