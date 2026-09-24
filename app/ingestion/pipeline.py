"""
Full ingestion pipeline: parse → chunk → embed → store.

Orchestrates the end-to-end process of loading contracts
into the vector store for retrieval.
"""

import logging
from pathlib import Path

from app.ingestion.parser import parse_document, parse_directory
from app.ingestion.chunker import chunk_sections, Chunk
from app.database.vector_store import VectorStore
from app.config import settings

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Coordinates document parsing, chunking, and vector storage."""

    def __init__(self, vector_store: VectorStore | None = None):
        self.vector_store = vector_store or VectorStore()

    def ingest_file(self, file_path: str | Path) -> int:
        """
        Ingest a single contract file.

        Returns the number of chunks stored.
        """
        file_path = Path(file_path)
        logger.info(f"Parsing: {file_path.name}")

        # Parse into sections
        sections = parse_document(file_path)
        logger.info(f"  Found {len(sections)} sections")

        # Chunk sections
        chunks = chunk_sections(sections)
        logger.info(f"  Created {len(chunks)} chunks")

        if not chunks:
            logger.warning(f"  No chunks created from {file_path.name}")
            return 0

        # Store in vector database
        self.vector_store.add_chunks(chunks)
        logger.info(f"  Stored {len(chunks)} chunks in vector DB")

        return len(chunks)

    def ingest_directory(self, directory: str | Path | None = None) -> dict:
        """
        Ingest all markdown contracts from a directory.

        Returns a summary dict with file-level counts.
        """
        directory = Path(directory or settings.contracts_dir)
        logger.info(f"Ingesting contracts from: {directory}")

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        md_files = sorted(directory.glob("*.md"))
        if not md_files:
            raise FileNotFoundError(f"No .md files found in: {directory}")

        summary = {
            "directory": str(directory),
            "files_processed": 0,
            "total_sections": 0,
            "total_chunks": 0,
            "files": {},
        }

        # Parse all files first
        all_sections = parse_directory(directory)
        summary["total_sections"] = len(all_sections)

        # Chunk all sections
        all_chunks = chunk_sections(all_sections)
        summary["total_chunks"] = len(all_chunks)

        # Group chunks by document for reporting
        doc_chunks: dict[str, list[Chunk]] = {}
        for chunk in all_chunks:
            doc_name = chunk.metadata.get("document_name", "unknown")
            doc_chunks.setdefault(doc_name, []).append(chunk)

        # Store all chunks
        if all_chunks:
            self.vector_store.add_chunks(all_chunks)

        # Build per-file summary
        for doc_name, chunks in doc_chunks.items():
            summary["files"][doc_name] = {
                "chunks": len(chunks),
                "document_type": chunks[0].metadata.get("document_type", "Unknown"),
            }

        summary["files_processed"] = len(doc_chunks)

        logger.info(
            f"Ingestion complete: {summary['files_processed']} files, "
            f"{summary['total_sections']} sections, "
            f"{summary['total_chunks']} chunks"
        )

        return summary

    def clear_and_reingest(self, directory: str | Path | None = None) -> dict:
        """Clear the vector store and reingest all documents."""
        logger.info("Clearing vector store...")
        self.vector_store.clear()
        return self.ingest_directory(directory)

    def get_stats(self) -> dict:
        """Get current vector store statistics."""
        return self.vector_store.get_stats()
