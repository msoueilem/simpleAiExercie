# PDF Reviewer — Design & Architecture

## What It Does

A Streamlit web app (and embeddable tab) that:
- Accepts PDF uploads via `st.file_uploader`
- Converts the first page to a PNG in memory (PyMuPDF)
- Extracts machine-readable text (pdfplumber) and sends both image + text to an LLM
- Displays a side-by-side view: rendered PDF page on the left, flagged issues on the right
- Highlights flagged text directly on the PDF preview using coloured bounding boxes
- Supports multiple LLM backends: Anthropic Claude, OpenAI GPT-4o, Google Gemini

---

## Stack

| Layer | Library |
|---|---|
| UI | `streamlit` |
| PDF → Image | `PyMuPDF` (`fitz`) |
| Text extraction | `pdfplumber` |
| LLM backends | `anthropic`, `openai`, `google-genai` |
| Env management | `python-dotenv` |

---

## File Structure

```
pdfReviewer/
├── core.py              # Pure functions — no Streamlit dependency
│   ├── render_pdf_first_page()
│   ├── extract_text()
│   ├── build_prompt()
│   └── parse_issues()
├── pdf_reviewer.py      # Streamlit UI — exposes render_pdf_tab()
└── llm_providers/
    ├── base.py          # LLMProvider ABC + ProviderError
    ├── __init__.py      # get_provider() factory
    ├── anthropic.py
    ├── openai.py
    └── gemini.py
```

`core.py` contains all logic with no Streamlit imports — importable anywhere.
`pdf_reviewer.py` can be run standalone (`streamlit run pdf_reviewer.py`) or embedded in the unified app via `render_pdf_tab()`.

---

## LLM Provider Selection

Set `PROVIDER` in `.env` to switch backends. Three vars cover all providers:

| `.env` var | Purpose | Example |
|---|---|---|
| `PROVIDER` | Which backend to use | `anthropic` \| `openai` \| `gemini` |
| `MODEL` | Model name (default pre-filled) | `claude-sonnet-4-6` |
| `API_KEY` | API key for the selected provider | `sk-ant-...` |

The `get_provider()` factory raises `ValueError` on an unknown provider name, which the UI catches and shows as a configuration error banner.

---

## Data Flow

```
[User uploads PDF]
       ↓
[st.session_state stores raw bytes]
       ↓
[PyMuPDF: bytes → first page PNG (2× zoom)]
       ↓
[pdfplumber: bytes → extracted text string]
       ↓
[Image base64-encoded + text appended to prompt]
       ↓
[LLM API call → raw JSON string response]
       ↓
[parse_issues(): strip fences → json.loads()]
       ↓
[render_pdf_first_page(): draw coloured rects for each quoted snippet]
       ↓
[Two-column Streamlit layout]
  Left:  highlighted PDF image
  Right: sorted issue cards (HIGH → MEDIUM → LOW)
```

---

## Session State Keys

All keys are namespaced with a prefix (default `"pdf_"`) so multiple instances can coexist in the same app without collision.

| Key | Type | Purpose |
|---|---|---|
| `{prefix}pdf_bytes` | `bytes` | Raw uploaded PDF — survives reruns |
| `{prefix}page_image` | `bytes` | Rendered + highlighted PNG |
| `{prefix}issues` | `list[dict]` | Parsed LLM response |
| `{prefix}last_filename` | `str` | Detect when a new file is uploaded |
| `{prefix}upload_key` | `int` | Incremented to reset the file uploader widget |
| `{prefix}raw_response` | `str` | Raw LLM text — shown on JSON parse failure |

---

## Issue Data Structure

The LLM is prompted to return a strict JSON array:

```json
[
  {
    "issue": "Invoice total does not match line items",
    "severity": "HIGH",
    "location": "Bottom-right totals section",
    "description": "Subtotal shows $1,240 but line items sum to $1,180",
    "quote": "Total: $1,240.00"
  }
]
```

Severity levels:
- **HIGH** — math errors, contradictory data, missing critical fields → red border
- **MEDIUM** — date format mismatches, suspicious values → orange border
- **LOW** — typos, style issues, minor formatting → blue border

The `quote` field is matched against the rendered page with `page.search_for()` and boxed in the corresponding colour. If the quote is empty or not found, the issue card still appears — just without a visual highlight.

---

## Error Handling

| Condition | Behaviour |
|---|---|
| API key missing | `st.error()` banner on startup; `render_pdf_tab()` returns early |
| Invalid API key (401) | `ProviderError` caught; error shown in progress area |
| Rate limit | `ProviderError` caught; retry message shown |
| Empty PDF | `ValueError("empty_pdf")` from `render_pdf_first_page`; `st.error()` |
| Corrupt / password-protected PDF | Generic exception caught; `st.error()` |
| Malformed LLM response (non-JSON) | `json.JSONDecodeError` caught; raw response shown in `st.code()` |

---

## Storage

Everything is handled in memory. No files are written to disk at any point.
`pdfplumber` and `fitz` both accept raw bytes / `BytesIO` directly.
