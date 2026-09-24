"""
Section-aware document parser for legal contracts.

Parses markdown-formatted contracts into structured sections,
preserving document hierarchy and extracting metadata.
"""

import re
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Section:
    """A parsed section from a legal contract."""

    title: str
    content: str
    level: int  # heading level: 1 = H1, 2 = H2, etc.
    section_number: str  # e.g. "3.2", "7.1"
    document_name: str
    document_type: str  # e.g. "NDA", "SaaS Agreement", "MSA"
    parties: list[str] = field(default_factory=list)
    agreement_number: str = ""
    effective_date: str = ""


# Map document titles to normalized types for metadata filtering
DOCUMENT_TYPE_PATTERNS = {
    r"non-disclosure|nda|confidentiality agreement": "NDA",
    r"saas|subscription agreement": "SaaS Agreement",
    r"consulting|professional services": "Consulting Agreement",
    r"data processing|dpa": "Data Processing Agreement",
    r"software license|license agreement": "Software License",
    r"employment agreement|employment contract": "Employment Agreement",
    r"partnership|strategic partnership": "Partnership Agreement",
    r"service level|sla": "Service Level Agreement",
    r"master services|msa": "Master Services Agreement",
    r"vendor|supply agreement": "Vendor Agreement",
    r"independent contractor|contractor agreement": "Independent Contractor Agreement",
}


def detect_document_type(title: str) -> str:
    """Classify document type from its title using pattern matching."""
    title_lower = title.lower()
    for pattern, doc_type in DOCUMENT_TYPE_PATTERNS.items():
        if re.search(pattern, title_lower):
            return doc_type
    return "Contract"


def extract_metadata(content: str) -> dict:
    """Extract agreement number, effective date, and parties from document header."""
    metadata = {
        "agreement_number": "",
        "effective_date": "",
        "parties": [],
    }

    # Agreement number
    match = re.search(
        r"\*\*Agreement Number:\*\*\s*(.+?)(?:\s*$|\s*\n)", content, re.MULTILINE
    )
    if match:
        metadata["agreement_number"] = match.group(1).strip()

    # Effective date
    match = re.search(
        r"\*\*Effective Date:\*\*\s*(.+?)(?:\s*$|\s*\n)", content, re.MULTILINE
    )
    if match:
        metadata["effective_date"] = match.group(1).strip()

    # Parties — look for bold party names
    party_matches = re.findall(
        r"\*\*(?:Party [AB]|Provider|Subscriber|Client|Consultant|"
        r"Data Controller|Data Processor|Licensor|Licensee|Employer|Employee|"
        r"Partner [AB]|Service Provider|Customer|Buyer|Vendor|Company|Contractor):\*\*\s*(.+?)(?:\s*$|\s*\n)",
        content,
        re.MULTILINE,
    )
    metadata["parties"] = [p.strip().rstrip(",") for p in party_matches]

    return metadata


def parse_document(file_path: str | Path) -> list[Section]:
    """
    Parse a markdown contract into structured sections.

    Strategy:
    - Split on markdown headings (## Section Title)
    - Extract section numbers from content
    - Attach document-level metadata to each section
    - Preserve subsection numbering (3.1, 3.2, etc.)
    """
    file_path = Path(file_path)
    content = file_path.read_text(encoding="utf-8")
    filename = file_path.stem

    sections: list[Section] = []

    # Extract document title (first H1)
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    document_title = title_match.group(1).strip() if title_match else filename
    document_type = detect_document_type(document_title)

    # Extract metadata from header
    metadata = extract_metadata(content)

    # Split into sections by heading
    # Pattern matches ## or ### headings with optional section numbers
    heading_pattern = re.compile(
        r"^(#{1,4})\s+(?:(\d+\.?)\s+)?(.+)$", re.MULTILINE
    )

    matches = list(heading_pattern.finditer(content))

    if not matches:
        # No headings found — treat entire document as one section
        sections.append(
            Section(
                title=document_title,
                content=content.strip(),
                level=1,
                section_number="",
                document_name=filename,
                document_type=document_type,
                parties=metadata["parties"],
                agreement_number=metadata["agreement_number"],
                effective_date=metadata["effective_date"],
            )
        )
        return sections

    for i, match in enumerate(matches):
        hashes = match.group(1)
        section_num = match.group(2) or ""
        section_title = match.group(3).strip()
        level = len(hashes)

        # Get content between this heading and the next
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section_content = content[start:end].strip()

        # Skip empty sections (like the divider-only ones)
        if not section_content or section_content == "---":
            continue

        # Clean up: remove leading/trailing dividers
        section_content = re.sub(r"^---\s*", "", section_content)
        section_content = re.sub(r"\s*---$", "", section_content)
        section_content = section_content.strip()

        if not section_content:
            continue

        sections.append(
            Section(
                title=section_title,
                content=section_content,
                level=level,
                section_number=section_num.rstrip("."),
                document_name=filename,
                document_type=document_type,
                parties=metadata["parties"],
                agreement_number=metadata["agreement_number"],
                effective_date=metadata["effective_date"],
            )
        )

    return sections


def parse_directory(directory: str | Path) -> list[Section]:
    """Parse all markdown files in a directory."""
    directory = Path(directory)
    all_sections: list[Section] = []

    for md_file in sorted(directory.glob("*.md")):
        sections = parse_document(md_file)
        all_sections.extend(sections)

    return all_sections
