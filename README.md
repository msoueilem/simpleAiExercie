# AI Tools Suite

![Python](https://img.shields.io/badge/Python-3.11+-1F4E79?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-EAF2FB?style=flat&logo=streamlit&logoColor=FF4B4B)
![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-D97706?style=flat)
![CI](https://github.com/msoueilem/simpleAiExercie/actions/workflows/ci.yml/badge.svg)

> Built entirely with **Claude Code** — zero manual edits. Every file was produced through
> AI-assisted development guided by natural language prompts.

A unified Streamlit web app combining two independent tools:

- **PDF Reviewer** — upload a PDF, let an LLM flag errors and inconsistencies, see them highlighted directly on the page
- **Word Counter** — upload `.md` / `.txt` files, get word counts, top-10 frequent words, reading time, and CSV/JSON export

---

## Quick start

```bash
# 1. Install
make install          # pip install -r requirements.txt

# 2. Configure
cp .env.template .env
# Set PROVIDER and API_KEY inside .env (MODEL is optional — each provider has a default)

# 3. Run
make run              # streamlit run app.py
```

Open **http://localhost:4600** in your browser.

---

## Navigating the app

When you open the app you'll see two tabs at the top:

### 📄 PDF Reviewer tab

1. **Upload a PDF** using the file picker at the top
2. The first page renders instantly on the left side
3. Click **Analyze PDF** — a live progress bar tracks each step:
   - Extract text from document
   - Encode page image
   - Send to AI for analysis
   - Parse AI response
   - Apply highlights to PDF
4. Issues appear on the right, sorted by severity: 🔴 HIGH · 🟠 MEDIUM · 🔵 LOW
5. Flagged text is boxed in the matching colour directly on the PDF image
6. Click **Re-analyze** to run again, or **Upload New PDF** to start over

### 📝 Word Counter tab

1. **Upload one or more `.md` or `.txt` files** using the multi-file picker
2. Summary metrics appear immediately: file count, total words, total reading time
3. Expand any file card to see its top-10 most frequent words
4. Use **Download CSV** or **Download JSON** to export the full results

---

## Project structure

```
.
├── app.py                        # Unified entry point — tabs only, no logic
├── Makefile                      # Dev commands (see below)
├── requirements.txt              # All dependencies including dev tools
├── .env.template                 # Copy to .env — 2 required vars, 1 optional
│
├── CLAUDE.md                     # AI coding rules for this repo
├── AGENTS.md                     # Guidance for any AI agent working here
│
├── .github/
│   └── workflows/ci.yml          # Lint + security audit + import check on every push
│
├── .streamlit/
│   └── config.toml               # App theme and upload size limit
│
├── docs/
│   ├── pdf_reviewer.md           # Architecture, data flow, session state reference
│   └── word_counter.md           # Architecture, data flow, CLI reference
│
├── pdfReviewer/
│   ├── core.py                   # Pure functions — no Streamlit, fully testable
│   ├── pdf_reviewer.py           # Streamlit UI — exposes render_pdf_tab()
│   └── llm_providers/
│       ├── base.py               # LLMProvider ABC + ProviderError
│       ├── __init__.py           # get_provider() factory
│       ├── anthropic.py
│       ├── openai.py
│       └── gemini.py
│
└── wordCount/
    ├── word_analyzer.py          # Core logic + CLI entry point
    └── word_counter_ui.py        # Streamlit UI — exposes render_word_counter_tab()
```

---

## Configuration

Copy `.env.template` to `.env` and fill in two values:

```bash
PROVIDER=anthropic      # anthropic | openai | gemini
API_KEY=your-key-here   # API key for the selected provider

# MODEL is optional — defaults per provider:
#   anthropic → claude-sonnet-4-6
#   openai    → gpt-4o
#   gemini    → gemini-2.5-flash
# MODEL=
```

---

## Make commands

| Command | What it does | Equivalent |
|---------|-------------|------------|
| `make install` | Install all dependencies | `pip install -r requirements.txt` |
| `make run` | Launch the unified web app | `streamlit run app.py` |
| `make run-pdf` | Launch PDF Reviewer standalone | `streamlit run pdfReviewer/pdf_reviewer.py` |
| `make run-wc ARGS="--json"` | Run Word Counter CLI | `python -m wordCount.word_analyzer --json` |
| `make lint` | Check code style | `ruff check .` |
| `make security` | Audit dependencies for CVEs | `pip-audit -r requirements.txt` |
| `make audit` | Scan source for hardcoded secrets | `grep` across all `.py` files |
| `make check` | Run lint + security + audit + import validation | — |

---

## PDF Reviewer — what it checks

| Category | Examples |
|----------|---------|
| Math errors | Totals that don't match line items |
| Date issues | Conflicting dates, wrong formats, impossible dates |
| Typos | Spelling errors in any field |
| Data mismatches | Values that contradict each other |
| Missing fields | Blank fields that should have values |
| Formatting | Inconsistent alignment or number formats |

---

## Architecture docs

Detailed design decisions, data flows, and session state references live in `docs/`:

- [`docs/pdf_reviewer.md`](docs/pdf_reviewer.md)
- [`docs/word_counter.md`](docs/word_counter.md)

---

## Development

```bash
make check      # run all checks before committing
```

CI runs automatically on every push to `main` via GitHub Actions:
lint → dependency security audit → hardcoded secrets scan → import validation.
