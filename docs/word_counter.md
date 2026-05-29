# Word Counter — Design & Architecture

## What It Does

A Python CLI and embeddable Streamlit tab that:
- Reads `.md` and `.txt` files from a folder, a file list, or Streamlit upload widgets
- Strips markdown syntax before counting (YAML frontmatter, fenced code, URLs, HTML, formatting chars)
- Reports per-file word count, top 10 frequent words (stopwords excluded), and estimated reading time
- Outputs a Unicode table (default), CSV, or JSON
- In the web app: shows summary metrics, per-file expandable cards, and CSV/JSON download buttons

---

## Stack

| Layer | Detail |
|---|---|
| Language | Python 3 standard library only (no third-party deps for core logic) |
| UI | `streamlit` (web tab only) |
| Reading time | 238 WPM average — `math.ceil(word_count / 238)` |
| Word frequency | `collections.Counter` with deterministic tie-breaking (freq desc → alpha) |

---

## File Structure

```
wordCount/
├── word_analyzer.py      # Core logic + CLI entry point
│   ├── analyze_file()    # File-path-based analysis (CLI)
│   ├── analyze_content() # In-memory analysis (web / testing)
│   ├── clean_text()      # Markdown stripping
│   ├── tokenize()        # Lowercase alpha-only tokens
│   ├── compute_top_words()
│   ├── compute_reading_time()
│   ├── serialize_text()  # Unicode table output
│   ├── serialize_csv()
│   └── serialize_json()
└── word_counter_ui.py    # Streamlit UI — exposes render_word_counter_tab()
```

The CLI (`word_analyzer.py`) uses only the standard library.
The web UI (`word_counter_ui.py`) imports `analyze_content()` and handles file I/O via Streamlit's `UploadedFile` objects.

---

## Data Flow — CLI

```
[argparse: input_dir | --file | --folder | --csv | --json]
       ↓
[discover_files() or explicit file list]
       ↓
[for each file: read_file() with utf-8-sig → latin-1 fallback]
       ↓
[clean_text(): strip markdown syntax if .md]
       ↓
[tokenize(): re.findall(r"[a-z]+", text.lower())]
       ↓
[compute_top_words(): Counter → sort by (-freq, alpha) → top 10]
       ↓
[serialize_text() | serialize_csv() | serialize_json() → stdout]
```

## Data Flow — Web Tab

```
[st.file_uploader(accept_multiple_files=True, type=["md","txt"])]
       ↓
[decode bytes: utf-8-sig → latin-1 fallback]
       ↓
[analyze_content(filename, suffix, text) — same pipeline as CLI]
       ↓
[Summary metrics: file count, total words, total reading time]
       ↓
[Per-file expander: top-10 word metric grid]
       ↓
[Download buttons: CSV and JSON]
```

---

## Markdown Cleaning (`clean_text`)

Applied only to `.md` files, in this order:

| Step | Pattern removed |
|---|---|
| YAML frontmatter | `^---\n...\n---` |
| Fenced code blocks | ` ```...``` ` |
| Inline code | `` `...` `` |
| URLs | `https?://\S+` |
| HTML tags | `<[^>]+>` |
| Markdown syntax chars | `# * _ [ ] ( ) ! \| > ~ ` |

`.txt` files are passed through unchanged.

---

## Stopword List

A hardcoded `frozenset` of ~130 common English words. Also excluded:
- Contraction fragments: `ll`, `ve`, `re`, `nt`, `em`, `er`, `ed`
- Single-character tokens (filtered by `len(t) > 1`)

---

## Output Formats

### Default — Unicode table

```
┌──────────────────────────────┬────────────┬──────────────┬─────────────────────────────────────────────────────┐
│ File                         │ Word Count │ Reading Time │ Top 10 Words                                        │
├──────────────────────────────┼────────────┼──────────────┼─────────────────────────────────────────────────────┤
│ cloud_migration_architecture │        842 │        4 min │ migration (12), services (9), cloud (8), api (7)... │
└──────────────────────────────┴────────────┴──────────────┴─────────────────────────────────────────────────────┘
```

Long top-word lists wrap within the cell at item boundaries.

### CSV

```
file,word_count,reading_time_min,rank,word,frequency
notes.md,312,2,1,migration,12
notes.md,312,2,2,services,9
```

One row per word per file. Files with no significant words get a single row with blank rank/word/frequency.

### JSON

```json
[
  {
    "file": "notes.md",
    "word_count": 312,
    "reading_time_min": 2,
    "top_words": [
      {"word": "migration", "frequency": 12}
    ]
  }
]
```

---

## CLI Usage

```bash
# Default: scan ./input folder, print table
python -m wordCount.word_analyzer

# Custom folder
python -m wordCount.word_analyzer path/to/docs

# Specific files
python -m wordCount.word_analyzer --file notes.md report.txt

# Additional folders
python -m wordCount.word_analyzer --folder docs/ specs/

# Output formats
python -m wordCount.word_analyzer --csv
python -m wordCount.word_analyzer --json
```

`--csv` and `--json` are mutually exclusive. `--file` and `--folder` override the positional `input_dir` argument.
