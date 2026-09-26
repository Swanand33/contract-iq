"""
LLM generation chain — takes retrieved context and produces an answer
with source citations.
"""

import time
import logging
from typing import Optional

from openai import OpenAI

from app.config import settings
from app.retrieval.search import ContractRetriever
from app.generation.prompts import (
    SYSTEM_PROMPT,
    QUERY_PROMPT_TEMPLATE,
    NO_CONTEXT_RESPONSE,
)
from app.database.query_log import QueryLogger

logger = logging.getLogger(__name__)


class ContractQAChain:
    """End-to-end question answering over contracts."""

    def __init__(
        self,
        retriever: ContractRetriever | None = None,
        query_logger: QueryLogger | None = None,
    ):
        self.retriever = retriever or ContractRetriever()
        self.query_logger = query_logger or QueryLogger()
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def answer(
        self,
        question: str,
        document_type: Optional[str] = None,
        document_name: Optional[str] = None,
        top_k: int = settings.top_k,
    ) -> dict:
        """
        Answer a question about contracts.

        Flow:
        1. Retrieve relevant chunks via similarity search
        2. Build context from retrieved chunks
        3. Send to LLM with system prompt enforcing citation rules
        4. Return answer with source citations
        5. Log the query for audit trail

        Returns dict with: answer, sources, metadata
        """
        start_time = time.time()

        # Step 1: Retrieve
        results = self.retriever.retrieve(
            query=question,
            top_k=top_k,
            document_type=document_type,
            document_name=document_name,
        )

        # Step 2: Handle no results
        if not results:
            elapsed_ms = (time.time() - start_time) * 1000
            self.query_logger.log_query(
                question=question,
                document_filter=document_type or document_name,
                chunks_retrieved=0,
                answer=NO_CONTEXT_RESPONSE,
                latency_ms=elapsed_ms,
            )
            return {
                "answer": NO_CONTEXT_RESPONSE,
                "sources": [],
                "metadata": {
                    "chunks_retrieved": 0,
                    "latency_ms": round(elapsed_ms, 2),
                    "model": settings.llm_model,
                },
            }

        # Step 3: Build context
        context = self.retriever.build_context(results)
        citations = self.retriever.get_source_citations(results)

        # Step 4: Generate answer
        prompt = QUERY_PROMPT_TEMPLATE.format(
            context=context,
            question=question,
        )

        response = self.openai_client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,  # Low temperature for factual accuracy
            max_tokens=1500,
        )

        answer = response.choices[0].message.content

        elapsed_ms = (time.time() - start_time) * 1000

        # Step 5: Log query
        relevance_scores = [r["relevance_score"] for r in results]
        self.query_logger.log_query(
            question=question,
            document_filter=document_type or document_name,
            chunks_retrieved=len(results),
            sources=[
                {"document": c["document"], "section": c["section"]}
                for c in citations
            ],
            answer=answer,
            relevance_scores=relevance_scores,
            latency_ms=elapsed_ms,
        )

        return {
            "answer": answer,
            "sources": citations,
            "metadata": {
                "chunks_retrieved": len(results),
                "top_relevance_score": max(relevance_scores),
                "latency_ms": round(elapsed_ms, 2),
                "model": settings.llm_model,
            },
        }
