# AGENTS.md — Agent Guidance

Instructions for any AI agent (Claude Code, GitHub Copilot, Cursor, etc.) working in this repository.

---

## What This Repo Is

A unified Streamlit web app combining two independent tools:
- **PDF Reviewer** — uploads a PDF, calls an LLM vision API, flags errors with coloured highlights
- **Word Counter** — uploads `.md`/`.txt` files, reports word frequency, reading time, and top words

Built entirely with **Claude Code**. No manual edits were made to any source file.

---

## Repository Map

```
app.py                        ← unified entry point only; no logic here
CLAUDE.md                     ← AI coding rules for this repo (read this first)
requirements.txt              ← all deps; audit before adding new ones
.env.template                 ← safe to commit; contains placeholder values only

pdfReviewer/
  core.py                     ← pure functions, no Streamlit; safe to unit-test
  pdf_reviewer.py             ← Streamlit UI; exposes render_pdf_tab()
  llm_providers/              ← one file per LLM backend; implement LLMProvider ABC

wordCount/
  word_analyzer.py            ← pure Python CLI + analysis functions; no Streamlit
  word_counter_ui.py          ← Streamlit UI; exposes render_word_counter_tab()

docs/
  pdf_reviewer.md             ← architecture, data flow, session state reference
  word_counter.md             ← architecture, data flow, CLI reference
```

---

## Hard Rules

1. **Security first** — read `CLAUDE.md` in full before writing any code
2. **No new dependency without `pip-audit`** — run it, check the output, only proceed if clean
3. **No secrets in source** — `.env` is gitignored; `.env.template` has placeholders only
4. **No cross-boundary imports** — `core.py` and `word_analyzer.py` must never import Streamlit
5. **No logic in `app.py`** — it is an orchestration file only
6. **No manual HTML construction with user-supplied data** — XSS risk
7. **Conventional commits** — `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:`

---

## Before You Write Code

1. Read the relevant architecture doc in `docs/`
2. Check `requirements.txt` — use what's already there before adding anything new
3. Confirm the module boundary you're working in (see table in `CLAUDE.md`)
4. If adding a dep: `pip-audit <package>` first, document the result

## Before You Commit

```bash
make check   # runs lint + pip-audit + import validation
```

Grep for accidental secrets:
```bash
grep -rn "sk-ant-\|sk-proj-\|AIza" --include="*.py" .
```

---

## What Not To Do

- Do not add a Streamlit import to `core.py` or `word_analyzer.py`
- Do not hardcode a model name — use env vars with defaults inside provider files
- Do not flatten the folder structure — each tool lives in its own directory
- Do not add new session state keys without namespacing them (`pdf_*` or `wc_*`)
- Do not skip `pip-audit` because "it's a well-known library"
- Do not commit `.env`, any `*.pdf`, or any file in `input/`
