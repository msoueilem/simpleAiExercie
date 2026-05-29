# AI Developer — Coding Exercise

Original exercise brief for this project.

> **Constraint:** The entire implementation — every file, refactor, and commit — was produced
> using **Claude Code only**. No manual edits were made to any source file. The workflow
> demonstrates directing an AI agent from blank folder to production-ready repo purely through
> natural language prompts and review.

---

## Exercise 1 — Word Counter (~15 min)

Build a Python CLI that reads `.md` and `.txt` files in an `input/` folder and outputs:
- Per-file word counts
- Top 10 most frequent words (excluding stopwords)
- Estimated reading time

**Default output:** formatted table. **Flag:** `--json` for JSON output.

**Implemented in:** `wordCount/`

---

## Exercise 2 — Agentic PDF Reviewer (~45–60 min)

Build a web app that:
- Loads a PDF file
- Uses the Anthropic Claude API to identify questionable areas in the document
- Visually highlights them on the page
- Shows a reviewer *why* each area was flagged

**Stack available:** Python 3.13 · PyMuPDF (`fitz`) · pdfplumber · streamlit · anthropic · pillow · pydantic · python-dotenv

**API key:** provided via `ANTHROPIC_API_KEY` in a `.env` file.

```python
from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
client = Anthropic()  # picks up ANTHROPIC_API_KEY from env
```

**Implemented in:** `pdfReviewer/`

---

## Extension — Unified Web App

Both tools combined into a single Streamlit app (`app.py`) with tab-based navigation.
Each tool retains its own folder and can still be run independently.

**Architecture docs:** `docs/pdf_reviewer.md` · `docs/word_counter.md`
