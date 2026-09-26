"""
ChromaDB vector store wrapper.

Handles embedding generation, storage, and similarity search
with metadata filtering for contract retrieval.
"""

import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI

from app.config import settings
from app.ingestion.chunker import Chunk

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB-backed vector store with OpenAI embeddings."""

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},  # cosine similarity
        )
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI text-embedding-3-small."""
        response = self.openai_client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
            dimensions=settings.embedding_dimensions,
        )
        return [item.embedding for item in response.data]

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """Add chunks to the vector store with embeddings and metadata."""
        if not chunks:
            return

        # Batch embeddings (OpenAI allows up to 2048 inputs per call)
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]

            texts = [c.text for c in batch]
            ids = [c.id for c in batch]
            metadatas = [c.metadata for c in batch]

            embeddings = self._get_embeddings(texts)

            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

            logger.info(f"  Stored batch of {len(batch)} chunks")

    def search(
        self,
        query: str,
        top_k: int = settings.top_k,
        document_type: Optional[str] = None,
        document_name: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for relevant chunks using similarity search with optional
        metadata filtering.

        Returns list of dicts with: text, metadata, distance, relevance_score
        """
        # Build metadata filter
        where_filter = None
        conditions = []

        if document_type:
            conditions.append({"document_type": {"$eq": document_type}})
        if document_name:
            conditions.append({"document_name": {"$eq": document_name}})

        if len(conditions) == 1:
            where_filter = conditions[0]
        elif len(conditions) > 1:
            where_filter = {"$and": conditions}

        # Embed the query
        query_embedding = self._get_embeddings([query])[0]

        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                # ChromaDB returns cosine distance; convert to similarity
                relevance_score = 1 - dist

                # Apply similarity threshold
                if relevance_score < settings.similarity_threshold:
                    continue

                formatted.append(
                    {
                        "text": doc,
                        "metadata": meta,
                        "distance": dist,
                        "relevance_score": round(relevance_score, 4),
                    }
                )

        return formatted

    def clear(self) -> None:
        """Delete and recreate the collection."""
        self.client.delete_collection(settings.chroma_collection)
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Vector store cleared")

    def get_stats(self) -> dict:
        """Return collection statistics."""
        count = self.collection.count()
        return {
            "collection": settings.chroma_collection,
            "total_chunks": count,
            "persist_dir": settings.chroma_persist_dir,
            "embedding_model": settings.embedding_model,
            "embedding_dimensions": settings.embedding_dimensions,
        }

    def list_documents(self) -> list[dict]:
        """List all unique documents in the store with their types."""
        # Get all metadata
        results = self.collection.get(include=["metadatas"])

        docs = {}
        if results["metadatas"]:
            for meta in results["metadatas"]:
                doc_name = meta.get("document_name", "unknown")
                if doc_name not in docs:
                    docs[doc_name] = {
                        "document_name": doc_name,
                        "document_type": meta.get("document_type", "Unknown"),
                        "parties": meta.get("parties", ""),
                        "agreement_number": meta.get("agreement_number", ""),
                        "chunk_count": 0,
                    }
                docs[doc_name]["chunk_count"] += 1

        return list(docs.values())
