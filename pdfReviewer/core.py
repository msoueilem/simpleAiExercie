"""Pure, UI-free functions for PDF analysis — importable without Streamlit."""
import io
import json
import re

import fitz  # PyMuPDF
import pdfplumber


SEVERITY_CONFIG = {
    "HIGH":   {"color": "#c0392b", "bg": "#fdecea", "icon": "🔴"},
    "MEDIUM": {"color": "#d35400", "bg": "#fef3e2", "icon": "🟠"},
    "LOW":    {"color": "#2980b9", "bg": "#eaf4fb", "icon": "🔵"},
}

ANALYSIS_STEPS = [
    "Extract text from document",
    "Encode page image",
    "Connecting to AI provider",
    "Receiving AI response",
    "Parse AI response",
    "Apply highlights to PDF",
]


def render_pdf_first_page(pdf_bytes: bytes, highlights: list[dict] | None = None) -> bytes:
    """Render the first PDF page to a PNG (2× zoom), optionally drawing highlight boxes."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if len(doc) == 0:
        raise ValueError("empty_pdf")
    page = doc[0]

    if highlights:
        for item in highlights:
            quote = item.get("quote", "").strip()
            if not quote:
                continue
            sev = item.get("severity", "LOW").upper()
            color = (1, 0, 0) if sev == "HIGH" else (1, 0.5, 0) if sev == "MEDIUM" else (0, 0, 1)
            for rect in page.search_for(quote):
                page.draw_rect(rect, color=color, width=1.5)

    return page.get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes("png")


def extract_text(pdf_bytes: bytes) -> str:
    """Extract plain text from the first PDF page via pdfplumber."""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return pdf.pages[0].extract_text() or "" if pdf.pages else ""
    except Exception:
        return ""


def build_prompt(extracted_text: str) -> str:
    text_section = (
        f"\n\nExtracted text from the document:\n{extracted_text}"
        if extracted_text.strip()
        else "\n\n(No machine-readable text could be extracted — rely on the image.)"
    )
    return (
        "You are a document quality reviewer. Analyze the PDF page shown in the image"
        " and the extracted text below for errors, inconsistencies, or quality issues.\n\n"
        "Check for:\n"
        "- Math errors (totals that don't add up, calculation mistakes)\n"
        "- Date inconsistencies (conflicting dates, wrong formats, impossible dates)\n"
        "- Typos and spelling errors\n"
        "- Data mismatches (values that contradict each other)\n"
        "- Missing required fields (blank fields that should have values)\n"
        "- Formatting problems (inconsistent formatting, alignment issues)\n\n"
        "Return ONLY a valid JSON array — no prose, no markdown fences, no explanation.\n"
        "Each element must have exactly these fields:\n"
        '{"issue": "brief title", "severity": "HIGH|MEDIUM|LOW", '
        '"location": "where in the document", "description": "detailed explanation", '
        '"quote": "the EXACT text snippet from the document where the error is located. '
        'Must be an exact match of the text so it can be highlighted. '
        'Leave empty if no specific text can be highlighted."}\n\n'
        "Severity guide:\n"
        "- HIGH: math errors, contradictory data, missing critical fields\n"
        "- MEDIUM: date format inconsistencies, suspicious values, minor data mismatches\n"
        "- LOW: typos, style issues, minor formatting problems\n\n"
        "If no issues are found return an empty array: []"
        + text_section
    )


def parse_issues(raw: str) -> list[dict]:
    """Strip markdown fences if present, then JSON-parse the LLM response."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)
