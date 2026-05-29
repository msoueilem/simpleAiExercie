# CLAUDE.md — AI Coding Guidelines

This repository was built entirely with **Claude Code** (zero manual edits).
Every file, refactor, and commit was produced through AI-assisted development.

---

## Project Context

Two tools, one unified Streamlit app:
- **PDF Reviewer** (`pdfReviewer/`) — LLM vision API analyzes uploaded PDFs for errors
- **Word Counter** (`wordCount/`) — CLI + Streamlit tab for `.md`/`.txt` frequency analysis

Entry point: `streamlit run app.py`

---

## Security Requirements — Non-Negotiable

### Before adding any dependency
1. Check PyPI for last release date, download count, and maintainer activity
2. Run `pip-audit <package>` — do not proceed if unpatched CVEs exist
3. Check the package's GitHub for open security issues
4. Prefer the standard library when the task can be done in <30 lines without a third-party lib
5. Never add a transitive dependency without reviewing what it pulls in

### Secrets and credentials
- API keys, tokens, and passwords go in `.env` only — never in source code
- `.env` is gitignored; `.env.template` (with placeholder values only) is the only credentials file committed
- Validate all required env vars at startup, before any UI renders or API calls are made
- Fail loudly with a clear error message — never silently fall back to an empty key

### Input validation
- All file uploads: validate MIME type, check for empty content, handle decode errors gracefully
- Never pass raw user input to shell commands or `eval()`
- Any `st.markdown(..., unsafe_allow_html=True)` call must be reviewed — only static, developer-controlled strings are allowed there; never render user-supplied content as HTML
- JSON from LLM responses is untrusted input — always wrap `json.loads()` in try/except

### Dependency hygiene
- `requirements.txt` uses `>=` minimum bounds — acceptable for local dev tools
- For production promotion: switch to pinned `==` versions with a lock file (`pip-compile`)
- Run `pip-audit -r requirements.txt` before every release

---

## Module Boundaries — Do Not Cross

| File | Allowed imports | Forbidden |
|---|---|---|
| `pdfReviewer/core.py` | stdlib, fitz, pdfplumber | `streamlit`, any UI lib |
| `pdfReviewer/pdf_reviewer.py` | streamlit, pdfReviewer.core, llm_providers | business logic |
| `wordCount/word_analyzer.py` | stdlib only | streamlit, third-party |
| `wordCount/word_counter_ui.py` | streamlit, wordCount.word_analyzer | business logic |
| `app.py` | streamlit, dotenv, the two UI modules | business logic |

Keeping core logic free of Streamlit imports ensures it is testable, reusable, and not coupled to the UI lifecycle.

### Adding a new LLM provider
1. Create `pdfReviewer/llm_providers/<name>.py` implementing `LLMProvider` (see `base.py`)
2. Register it in the `get_provider()` factory in `llm_providers/__init__.py`
3. Add the required env vars to `.env.template` with placeholder values
4. Do not modify `core.py` or `pdf_reviewer.py`
5. Run `pip-audit` on the new provider's SDK before adding it to `requirements.txt`

### Session state
- All `st.session_state` keys must be namespaced with a prefix (`pdf_`, `wc_`)
- Document new keys in the relevant architecture doc under `docs/`

---

## Code Quality Rules

- No `print()` statements in production paths — raise exceptions or use `st.error()`
- No hardcoded model names outside of provider files — use env vars with documented defaults
- Functions stay under 50 lines; files stay under 400 lines
- No deep nesting — use early returns
- Type hints on all public functions
- One short comment max, only when the WHY is non-obvious

---

## Pre-Commit Checklist

Run before every commit:

```bash
make check   # lint + security audit + import validation
```

Manual checks:
- [ ] `grep -rn "sk-ant-\|sk-proj-\|AIza\|api_key\s*=\s*['\"][^'\"]" --include="*.py" .` returns nothing
- [ ] No `print()` debug statements in non-CLI code
- [ ] New dependencies vetted with `pip-audit`
- [ ] `docs/` updated if module structure changed
- [ ] `.env.template` updated if new env vars were added
