"""
FastAPI application — REST API for the Contract Q&A system.

Endpoints:
  POST /query       — ask a question about contracts
  POST /ingest      — ingest contracts from the sample directory
  GET  /documents   — list all ingested documents
  GET  /health      — health check with system stats
  GET  /query-log   — recent query history for audit
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.generation.chain import ContractQAChain
from app.ingestion.pipeline import IngestionPipeline
from app.database.vector_store import VectorStore
from app.database.query_log import QueryLogger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ContractIQ",
    description="AI-powered contract analysis — ask questions, get cited answers.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared instances — created once, reused across requests
vector_store = VectorStore()
query_logger = QueryLogger()
qa_chain = ContractQAChain(query_logger=query_logger)
pipeline = IngestionPipeline(vector_store=vector_store)


# ── Request / Response models ────────────────────────────────────────


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Question about contracts")
    document_type: Optional[str] = Field(
        None, description="Filter by type: NDA, SaaS Agreement, etc."
    )
    document_name: Optional[str] = Field(
        None, description="Filter by specific document name"
    )
    top_k: int = Field(
        default=settings.top_k,
        ge=1,
        le=20,
        description="Number of chunks to retrieve",
    )


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    metadata: dict


class IngestResponse(BaseModel):
    status: str
    summary: dict


# ── Endpoints ────────────────────────────────────────────────────────


@app.post("/query", response_model=QueryResponse)
async def query_contracts(request: QueryRequest):
    """
    Ask a question about the ingested contracts.

    The system retrieves relevant sections via similarity search,
    sends them to the LLM with citation rules, and returns a
    grounded answer with source references.
    """
    try:
        result = qa_chain.answer(
            question=request.question,
            document_type=request.document_type,
            document_name=request.document_name,
            top_k=request.top_k,
        )
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/ingest", response_model=IngestResponse)
async def ingest_contracts(
    directory: Optional[str] = None,
    clear_existing: bool = False,
):
    """
    Ingest contracts from a directory into the vector store.

    - Uses the configured sample_contracts directory by default.
    - Set clear_existing=True to wipe and re-ingest from scratch.
    """
    target_dir = directory or settings.contracts_dir

    try:
        if clear_existing:
            summary = pipeline.clear_and_reingest(target_dir)
        else:
            summary = pipeline.ingest_directory(target_dir)

        return IngestResponse(status="completed", summary=summary)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Directory not found: {target_dir}",
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/documents")
async def list_documents():
    """List all documents currently in the vector store."""
    try:
        documents = vector_store.list_documents()
        return {
            "total_documents": len(documents),
            "documents": documents,
        }
    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check with system statistics.

    Returns vector store stats, query log stats, and config info.
    """
    try:
        store_stats = vector_store.get_stats()
        log_stats = query_logger.get_stats()

        return {
            "status": "healthy",
            "vector_store": store_stats,
            "query_log": log_stats,
            "config": {
                "llm_model": settings.llm_model,
                "embedding_model": settings.embedding_model,
                "embedding_dimensions": settings.embedding_dimensions,
                "top_k": settings.top_k,
                "similarity_threshold": settings.similarity_threshold,
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {"status": "unhealthy", "error": str(e)}


@app.get("/query-log")
async def get_query_log(limit: int = 20):
    """Return recent queries for audit/debugging."""
    try:
        recent = query_logger.get_recent_queries(limit=limit)
        stats = query_logger.get_stats()
        return {"stats": stats, "recent_queries": recent}
    except Exception as e:
        logger.error(f"Failed to fetch query log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
