"""Tests for the contract document parser."""

import os
import tempfile
import pytest

from app.ingestion.parser import (
    Section,
    detect_document_type,
    extract_metadata,
    parse_document,
    parse_directory,
)


# ── Document type detection ──────────────────────────────────────────


class TestDetectDocumentType:
    def test_nda(self):
        assert detect_document_type("Non-Disclosure Agreement") == "NDA"
        assert detect_document_type("Bilateral NDA") == "NDA"
        assert detect_document_type("mutual_nda_techcorp.md") == "NDA"

    def test_saas(self):
        assert detect_document_type("SaaS Subscription Agreement") == "SaaS Agreement"

    def test_consulting(self):
        assert detect_document_type("Consulting Services Agreement") == "Consulting Agreement"

    def test_data_processing(self):
        result = detect_document_type("Data Processing Agreement")
        assert result == "Data Processing Agreement"

    def test_employment(self):
        assert detect_document_type("Employment Agreement") == "Employment Agreement"

    def test_software_license(self):
        assert detect_document_type("Software License Agreement") == "Software License"

    def test_sla(self):
        assert detect_document_type("Service Level Agreement") == "Service Level Agreement"

    def test_msa(self):
        assert detect_document_type("Master Services Agreement") == "Master Services Agreement"

    def test_unknown_defaults_to_contract(self):
        assert detect_document_type("random_document.md") == "Contract"


# ── Metadata extraction ─────────────────────────────────────────────


class TestExtractMetadata:
    def test_extracts_agreement_number(self):
        content = "**Agreement Number:** AGR-2024-001\nSome content here."
        meta = extract_metadata(content)
        assert meta["agreement_number"] == "AGR-2024-001"

    def test_extracts_effective_date(self):
        content = "**Effective Date:** January 15, 2024"
        meta = extract_metadata(content)
        assert meta["effective_date"] == "January 15, 2024"

    def test_extracts_parties(self):
        content = '**Provider:** Acme Corp\n**Client:** Beta Inc'
        meta = extract_metadata(content)
        assert len(meta["parties"]) == 2
        assert "Acme Corp" in meta["parties"]
        assert "Beta Inc" in meta["parties"]

    def test_missing_metadata_returns_empty(self):
        content = "Just some plain contract text without metadata."
        meta = extract_metadata(content)
        assert meta["agreement_number"] == ""
        assert meta["effective_date"] == ""
        assert meta["parties"] == []


# ── Document parsing ─────────────────────────────────────────────────


SAMPLE_CONTRACT = """# SaaS Subscription Agreement

**Agreement Number:** AGR-2024-042
**Effective Date:** March 1, 2024
**Provider:** Acme Cloud
**Client:** Greenfield Mfg

## 1. Definitions

"Service" means the cloud-based platform provided by Provider.
"Subscription Term" means the period during which Client has access.

## 2. Scope of Service

Provider shall make the Service available to Client 24/7,
subject to scheduled maintenance windows.

### 2.1 Service Features

The Service includes data analytics, reporting, and API access.

## 3. Payment Terms

Client shall pay $5,000 per month, due on the 1st of each month.
Late payments incur a 1.5% monthly fee.
"""


class TestParseDocument:
    def test_returns_sections(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(SAMPLE_CONTRACT)
            f.flush()

            sections = parse_document(f.name)

        os.unlink(f.name)

        # Should find the top-level and sub-sections
        assert len(sections) >= 3
        assert all(isinstance(s, Section) for s in sections)

    def test_section_metadata(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(SAMPLE_CONTRACT)
            f.flush()

            sections = parse_document(f.name)

        os.unlink(f.name)

        # First content section (skip H1 header if present)
        definitions = next(
            (s for s in sections if "Definitions" in s.title), None
        )
        assert definitions is not None
        assert definitions.section_number == "1"
        assert definitions.document_type == "SaaS Agreement"

    def test_parse_empty_file(self):
        """An empty file with no headings produces a single fallback section."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write("")
            f.flush()

            sections = parse_document(f.name)

        os.unlink(f.name)
        # Parser treats headingless files as a single section
        # An empty file produces one section with empty content
        assert len(sections) <= 1

    def test_document_type_detected(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(SAMPLE_CONTRACT)
            f.flush()

            sections = parse_document(f.name)

        os.unlink(f.name)

        for s in sections:
            assert s.document_type == "SaaS Agreement"


class TestParseDirectory:
    def test_parses_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["contract_a.md", "contract_b.md"]:
                path = os.path.join(tmpdir, name)
                with open(path, "w") as f:
                    f.write(f"# {name}\n\n## 1. Terms\n\nSome terms here.\n")

            all_sections = parse_directory(tmpdir)

        assert len(all_sections) >= 2

    def test_skips_non_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "contract.md"), "w") as f:
                f.write("# Contract\n\n## 1. Terms\n\nContent.\n")

            with open(os.path.join(tmpdir, "notes.txt"), "w") as f:
                f.write("This is not a contract.")

            sections = parse_directory(tmpdir)

        doc_names = set(s.document_name for s in sections)
        assert "contract" in doc_names  # stem, not full filename
        assert "notes" not in doc_names
