#!/usr/bin/env python3
"""
CLI tool for ingesting contracts into the vector store.

Usage:
    python scripts/ingest.py                          # ingest sample_contracts/
    python scripts/ingest.py --directory ./my_contracts
    python scripts/ingest.py --clear                  # wipe and re-ingest
    python scripts/ingest.py --stats                  # show current stats
"""

import argparse
import sys
import os

# Add project root to path so imports work when run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.ingestion.pipeline import IngestionPipeline
from app.database.vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(
        description="Ingest contract documents into the ContractIQ vector store."
    )
    parser.add_argument(
        "--directory",
        "-d",
        default=settings.contracts_dir,
        help=f"Directory containing contract .md files (default: {settings.contracts_dir})",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data and re-ingest from scratch",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show vector store statistics and exit",
    )
    args = parser.parse_args()

    store = VectorStore()
    pipeline = IngestionPipeline(vector_store=store)

    # Stats mode
    if args.stats:
        stats = store.get_stats()
        print("\n=== Vector Store Statistics ===")
        print(f"  Collection:           {stats['collection']}")
        print(f"  Total chunks:         {stats['total_chunks']}")
        print(f"  Persist directory:    {stats['persist_dir']}")
        print(f"  Embedding model:      {stats['embedding_model']}")
        print(f"  Embedding dimensions: {stats['embedding_dimensions']}")

        documents = store.list_documents()
        if documents:
            print(f"\n=== Documents ({len(documents)}) ===")
            for doc in documents:
                print(
                    f"  {doc['document_name']:<50} "
                    f"{doc['document_type']:<20} "
                    f"{doc['chunk_count']} chunks"
                )
        else:
            print("\n  No documents ingested yet.")
        return

    # Ingest mode
    directory = args.directory
    if not os.path.isdir(directory):
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)

    print(f"\nContractIQ Ingestion")
    print(f"{'=' * 40}")
    print(f"  Source:  {os.path.abspath(directory)}")
    print(f"  Mode:   {'Clear + Re-ingest' if args.clear else 'Incremental'}")
    print()

    if args.clear:
        summary = pipeline.clear_and_reingest(directory)
    else:
        summary = pipeline.ingest_directory(directory)

    # Print results
    print(f"\n{'=' * 40}")
    print(f"Ingestion Complete")
    print(f"  Files processed:  {summary['files_processed']}")
    print(f"  Total sections:   {summary['total_sections']}")
    print(f"  Total chunks:     {summary['total_chunks']}")

    if summary.get("files"):
        print(f"\nPer-file breakdown:")
        for f in summary["files"]:
            print(
                f"  {f['file']:<50} "
                f"{f['sections']} sections → {f['chunks']} chunks"
            )

    # Final stats
    final_stats = store.get_stats()
    print(f"\nVector store now holds {final_stats['total_chunks']} total chunks.")


if __name__ == "__main__":
    main()
