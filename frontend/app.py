"""
Streamlit frontend for ContractIQ.

Provides an interactive UI for:
  - Asking questions about contracts
  - Filtering by document type or name
  - Viewing cited answers with source details
  - Browsing ingested documents
  - Triggering ingestion
"""

import streamlit as st
import requests
import json

API_URL = "http://api:8000"

st.set_page_config(
    page_title="ContractIQ",
    page_icon="📄",
    layout="wide",
)


def query_api(
    question: str,
    document_type: str | None = None,
    document_name: str | None = None,
    top_k: int = 5,
) -> dict | None:
    """Send a question to the API and return the response."""
    payload = {"question": question, "top_k": top_k}
    if document_type:
        payload["document_type"] = document_type
    if document_name:
        payload["document_name"] = document_name

    try:
        resp = requests.post(f"{API_URL}/query", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the API. Is the backend running?")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API error: {e.response.text}")
        return None


def fetch_documents() -> list[dict]:
    """Fetch the list of ingested documents."""
    try:
        resp = requests.get(f"{API_URL}/documents", timeout=10)
        resp.raise_for_status()
        return resp.json().get("documents", [])
    except Exception:
        return []


def fetch_health() -> dict | None:
    """Fetch system health info."""
    try:
        resp = requests.get(f"{API_URL}/health", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def trigger_ingestion(clear: bool = False) -> dict | None:
    """Trigger contract ingestion."""
    try:
        resp = requests.post(
            f"{API_URL}/ingest",
            params={"clear_existing": clear},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Ingestion failed: {e}")
        return None


# ── Sidebar ──────────────────────────────────────────────────────────

with st.sidebar:
    st.title("ContractIQ")
    st.caption("AI-Powered Contract Analysis")

    st.divider()

    # Document filters
    st.subheader("Filters")

    documents = fetch_documents()
    doc_types = sorted(set(d["document_type"] for d in documents)) if documents else []
    doc_names = sorted(d["document_name"] for d in documents) if documents else []

    selected_type = st.selectbox(
        "Document Type",
        options=["All Types"] + doc_types,
        index=0,
    )

    selected_name = st.selectbox(
        "Specific Document",
        options=["All Documents"] + doc_names,
        index=0,
    )

    top_k = st.slider("Chunks to retrieve", min_value=1, max_value=15, value=5)

    st.divider()

    # System info
    st.subheader("System")

    if documents:
        st.metric("Documents Ingested", len(documents))
        total_chunks = sum(d.get("chunk_count", 0) for d in documents)
        st.metric("Total Chunks", total_chunks)
    else:
        st.warning("No documents ingested yet.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ingest", use_container_width=True):
            with st.spinner("Ingesting contracts..."):
                result = trigger_ingestion(clear=False)
                if result:
                    st.success(f"Done! {result['summary'].get('total_chunks', 0)} chunks indexed.")
                    st.rerun()
    with col2:
        if st.button("Re-ingest", use_container_width=True):
            with st.spinner("Clearing and re-ingesting..."):
                result = trigger_ingestion(clear=True)
                if result:
                    st.success("Re-ingested from scratch.")
                    st.rerun()

    health = fetch_health()
    if health and health.get("status") == "healthy":
        with st.expander("Config"):
            config = health.get("config", {})
            st.json(config)


# ── Main area ────────────────────────────────────────────────────────

st.header("Ask a Question About Your Contracts")

# Sample questions for quick start
sample_questions = [
    "What are the termination clauses across all agreements?",
    "Which contracts have liability caps, and what are the limits?",
    "Compare the confidentiality obligations in the NDA vs the consulting agreement.",
    "What are the data protection obligations in the Data Processing Agreement?",
    "What is the uptime SLA commitment from HostPro?",
    "What non-compete restrictions apply to Jordan Rivera?",
    "What are the payment terms in the Master Services Agreement?",
    "How is intellectual property handled across the SaaS and software license agreements?",
]

with st.expander("Sample questions to try"):
    for q in sample_questions:
        if st.button(q, key=f"sample_{hash(q)}"):
            st.session_state["question"] = q

question = st.text_area(
    "Your question",
    value=st.session_state.get("question", ""),
    height=80,
    placeholder="e.g., What are the termination notice periods across all agreements?",
)

if st.button("Ask", type="primary", use_container_width=True) and question:
    # Build filters
    doc_type_filter = None if selected_type == "All Types" else selected_type
    doc_name_filter = None if selected_name == "All Documents" else selected_name

    with st.spinner("Searching contracts and generating answer..."):
        result = query_api(
            question=question,
            document_type=doc_type_filter,
            document_name=doc_name_filter,
            top_k=top_k,
        )

    if result:
        # Answer section
        st.subheader("Answer")
        st.markdown(result["answer"])

        # Metadata
        metadata = result.get("metadata", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Chunks Retrieved", metadata.get("chunks_retrieved", 0))
        with col2:
            score = metadata.get("top_relevance_score", 0)
            st.metric("Top Relevance", f"{score:.2%}" if score else "N/A")
        with col3:
            latency = metadata.get("latency_ms", 0)
            st.metric("Latency", f"{latency:.0f} ms")

        # Sources
        sources = result.get("sources", [])
        if sources:
            st.subheader("Sources")
            for src in sources:
                with st.expander(
                    f"[Source {src['source_number']}] "
                    f"{src['document_type']}: {src['document']}"
                    + (f" — Section {src['section_number']}: {src['section']}" if src.get("section") else "")
                ):
                    st.write(f"**Document:** {src['document']}")
                    st.write(f"**Type:** {src['document_type']}")
                    if src.get("section"):
                        st.write(f"**Section:** {src['section_number']} — {src['section']}")
                    st.write(f"**Relevance:** {src['relevance_score']:.2%}")

# ── Documents tab ────────────────────────────────────────────────────

st.divider()

with st.expander("Ingested Documents"):
    if documents:
        for doc in documents:
            cols = st.columns([3, 2, 1])
            with cols[0]:
                st.write(f"**{doc['document_name']}**")
            with cols[1]:
                st.write(doc["document_type"])
            with cols[2]:
                st.write(f"{doc['chunk_count']} chunks")
    else:
        st.info("No documents ingested. Click 'Ingest' in the sidebar to get started.")
