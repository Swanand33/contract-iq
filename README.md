# ContractIQ

AI-powered contract analysis system — ask natural language questions about legal contracts and get cited, grounded answers.

Built as a production-style RAG (Retrieval-Augmented Generation) pipeline with section-aware parsing, metadata-filtered vector search, and citation-enforced LLM generation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ContractIQ                                  │
│                                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌────────────┐    ┌─────────┐ │
│  │ Streamlit │───▶│  FastAPI      │───▶│  Retrieval │───▶│ ChromaDB│ │
│  │ Frontend  │    │  /query       │    │  Layer     │    │ Vector  │ │
│  │           │◀───│  /ingest      │◀───│            │    │ Store   │ │
│  │           │    │  /documents   │    │  ┌────────┐│    │         │ │
│  └──────────┘    │  /health      │    │  │Context ││    └─────────┘ │
│                  └──────┬───────┘    │  │Builder ││                 │
│                         │            │  └────────┘│                 │
│                         ▼            └────────────┘                 │
│                  ┌──────────────┐                                    │
│                  │  Generation   │    ┌────────────┐                 │
│                  │  Chain        │───▶│  OpenAI    │                 │
│                  │  (LLM + Cit) │    │  GPT-4o    │                 │
│                  └──────┬───────┘    └────────────┘                 │
│                         │                                           │
│                         ▼                                           │
│                  ┌──────────────┐                                    │
│                  │  Query Log    │  (SQLite audit trail)            │
│                  └──────────────┘                                    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Ingestion Pipeline                         │   │
│  │  Markdown ──▶ Section Parser ──▶ Chunker ──▶ Embeddings ──▶ DB│   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Section-Aware Parsing** — Splits contracts by clause boundaries, not arbitrary character counts. Each chunk retains document type, section number, parties, and agreement metadata.
- **Metadata-Filtered Search** — Filter by document type (NDA, SaaS Agreement, MSA, etc.) or specific document name before similarity search runs.
- **Citation-Enforced Answers** — System prompt requires `[Source N]` references. The LLM can only answer from retrieved context — no hallucinated contract terms.
- **Audit Trail** — Every query is logged with the question, retrieved chunks, relevance scores, generated answer, and latency.
- **10+ Realistic Sample Contracts** — SaaS, NDA, consulting, DPA, software license, employment, partnership, SLA, MSA, vendor supply, and independent contractor agreements with realistic clauses.

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Embeddings | OpenAI `text-embedding-3-small` (1536d) | Strong semantic understanding for legal text |
| Vector DB | ChromaDB (persistent, cosine similarity) | Zero-config local setup, no external service needed |
| LLM | GPT-4o-mini | Good accuracy at low cost; temperature=0.1 for factual grounding |
| API | FastAPI | Async, auto-docs, Pydantic validation |
| Frontend | Streamlit | Rapid prototyping, interactive filters |
| Query Log | SQLite | Lightweight audit trail, no infrastructure |
| Config | pydantic-settings | Type-safe, `.env` file support |
| Deployment | Docker Compose | Two-service setup (API + frontend) |

## Project Structure

```
contract-iq/
├── app/
│   ├── config.py                 # Settings from .env
│   ├── main.py                   # FastAPI endpoints
│   ├── ingestion/
│   │   ├── parser.py             # Section-aware markdown parser
│   │   ├── chunker.py            # Clause-boundary chunking with metadata
│   │   └── pipeline.py           # Ingestion orchestrator
│   ├── database/
│   │   ├── vector_store.py       # ChromaDB wrapper + embeddings
│   │   └── query_log.py          # SQLite query logging
│   ├── retrieval/
│   │   └── search.py             # Similarity search + context builder
│   └── generation/
│       ├── prompts.py            # System prompt + templates
│       └── chain.py              # End-to-end QA chain
├── frontend/
│   └── app.py                    # Streamlit UI
├── scripts/
│   └── ingest.py                 # CLI ingestion tool
├── sample_contracts/             # 10+ realistic legal contracts
├── tests/
│   ├── test_parser.py            # Parser unit tests
│   ├── test_chunker.py           # Chunker unit tests
│   └── test_search.py            # Retrieval logic tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/yourusername/contract-iq.git
cd contract-iq
cp .env.example .env
# Add your OpenAI API key to .env
```

### 2. Run with Docker

```bash
docker compose up --build
```

- API: http://localhost:8000 (Swagger docs at `/docs`)
- Frontend: http://localhost:8501

### 3. Or run locally

```bash
pip install -r requirements.txt

# Ingest sample contracts
python scripts/ingest.py

# Start the API
uvicorn app.main:app --reload

# Start the frontend (separate terminal)
streamlit run frontend/app.py
```

### 4. Ingest contracts

```bash
# Ingest the included sample contracts
python scripts/ingest.py

# Ingest from a custom directory
python scripts/ingest.py --directory /path/to/contracts

# Clear and re-ingest
python scripts/ingest.py --clear

# Check current stats
python scripts/ingest.py --stats
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/query` | Ask a question with optional filters |
| `POST` | `/ingest` | Ingest contracts from a directory |
| `GET` | `/documents` | List all ingested documents |
| `GET` | `/health` | System health + config info |
| `GET` | `/query-log` | Recent queries for audit |

### Example query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the termination notice periods across all agreements?",
    "top_k": 5
  }'
```

### Example response

```json
{
  "answer": "The termination notice periods vary across agreements:\n\n1. The SaaS Subscription Agreement requires 30 days written notice [Source 1]\n2. The Master Services Agreement allows termination with 60 days notice [Source 2]\n3. The Employment Agreement requires 2 weeks notice from the employee [Source 3]\n\nSources:\n[Source 1] SaaS Agreement: saas_subscription_agreement_acme\n[Source 2] MSA: master_services_agreement_brightpath\n[Source 3] Employment Agreement: employment_agreement_template",
  "sources": [
    {
      "source_number": 1,
      "document": "saas_subscription_agreement_acme",
      "document_type": "SaaS Agreement",
      "section": "Termination",
      "section_number": "8",
      "relevance_score": 0.8723
    }
  ],
  "metadata": {
    "chunks_retrieved": 5,
    "top_relevance_score": 0.8723,
    "latency_ms": 2340.12,
    "model": "gpt-4o-mini"
  }
}
```

## Sample Questions

Try these against the included contracts:

- "What are the termination clauses across all agreements?"
- "Which contracts have liability caps, and what are the limits?"
- "Compare the confidentiality obligations in the NDA vs the consulting agreement"
- "What are the data protection obligations in the Data Processing Agreement?"
- "What is the uptime SLA commitment from HostPro?"
- "What non-compete restrictions apply to Jordan Rivera?"
- "What are the payment terms in the Master Services Agreement?"
- "How is intellectual property handled across the SaaS and software license agreements?"

## Running Tests

```bash
pytest tests/ -v
```

Tests cover:
- **Parser** — Document type detection, metadata extraction, section parsing, directory scanning
- **Chunker** — Section splitting, metadata preservation, chunk ID determinism, overlap handling
- **Retrieval** — Context building, source citation formatting, deduplication

## Architecture Decisions

### Why section-aware chunking instead of naive text splitting?

Legal contracts have structure — sections, subsections, clauses. Naive splitting (e.g., RecursiveCharacterTextSplitter with 1000-char chunks) breaks mid-clause, losing context. Section-aware chunking keeps each clause whole and attaches metadata (document name, section number, parties) so the LLM knows exactly where each piece of evidence comes from.

### Why ChromaDB over Pinecone / Weaviate?

For a demo repo that anyone can clone and run: ChromaDB is local, free, requires zero API keys for the vector DB layer, and persists to disk. In production, you'd swap this for a managed vector DB — the `VectorStore` class abstracts the interface, so the rest of the pipeline doesn't change.

### Why metadata filtering before similarity search?

When a user asks "What are the payment terms in the SaaS agreement?", naive similarity search might return payment terms from unrelated contracts too. Metadata filtering narrows the search space first (`document_type: "SaaS Agreement"` or `document_name: "saas_subscription_agreement_acme"`), then runs similarity search within that subset. This is both faster and more precise.

### Why temperature=0.1 for generation?

Legal analysis needs precision, not creativity. Low temperature keeps the model close to the retrieved evidence rather than generating plausible-sounding but fabricated contract terms. The system prompt reinforces this by requiring `[Source N]` citations.

### Why SQLite for query logging?

For an audit trail in a demo context, SQLite is zero-config and file-based. In production, this would be a proper database (Postgres) or an observability platform (LangSmith, Helicone). The `QueryLogger` class makes swapping straightforward.

### Why separate the retrieval layer from the vector store?

The `ContractRetriever` wraps `VectorStore` and adds context building, citation extraction, and deduplication. This separation means the vector store handles storage and search (infrastructure), while the retriever handles how results become LLM input (application logic). Testing is also easier — the retriever's formatting logic can be tested without a real database.

## License

MIT
