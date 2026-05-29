"""Word frequency analyzer for .md and .txt files."""
import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

STOPWORDS = frozenset({
    "a", "about", "above", "after", "again", "against", "all", "also", "am",
    "an", "and", "any", "are", "aren", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can",
    "could", "couldn", "did", "didn", "do", "does", "doesn", "doing", "don",
    "down", "during", "each", "even", "few", "for", "from", "further", "get",
    "got", "had", "hadn", "has", "hasn", "have", "haven", "having", "he",
    "her", "here", "hers", "herself", "him", "himself", "his", "how", "i",
    "if", "in", "into", "is", "isn", "it", "its", "itself", "just", "let",
    "may", "me", "might", "more", "most", "much", "mustn", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "shan", "she", "should", "shouldn", "so", "some", "still", "such",
    "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn", "we", "well", "were",
    "weren", "what", "when", "where", "which", "while", "who", "whom",
    "why", "will", "with", "won", "would", "wouldn", "you", "your", "yours",
    "yourself", "yourselves", "shall", "need",
    "ll", "ve", "re", "nt", "em", "er", "ed",
})


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Analyze word frequencies in .md and .txt files."
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        type=Path,
        default=Path("input"),
        help="Directory to scan (default: ./input). Ignored when --file or --folder is given.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--csv", action="store_true", help="Output as CSV")
    group.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--file",
        nargs="+",
        type=Path,
        metavar="FILE",
        dest="files",
        help="Specific files to analyze. Non-.md/.txt paths are silently ignored.",
    )
    parser.add_argument(
        "--folder",
        nargs="+",
        type=Path,
        metavar="DIR",
        dest="folders",
        help="Folders to scan for .md and .txt files.",
    )
    return parser.parse_args(argv)


def discover_files(input_dir: Path) -> list:
    if not input_dir.is_dir():
        print(f"Error: directory '{input_dir}' not found.", file=sys.stderr)
        sys.exit(1)
    files = sorted(
        p for p in input_dir.iterdir()
        if p.suffix in (".md", ".txt") and p.is_file()
    )
    if not files:
        print(f"Warning: no .md or .txt files found in '{input_dir}'.", file=sys.stderr)
    return files


def read_file(path: Path):
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            print(f"Warning: could not read '{path}': {exc}", file=sys.stderr)
            return None
    print(f"Warning: could not decode '{path}'.", file=sys.stderr)
    return None


def clean_text(text: str, suffix: str) -> str:
    """Strip markdown syntax from .md files; pass .txt files through unchanged."""
    if suffix != ".md":
        return text
    # YAML frontmatter
    text = re.sub(r"^---\n.*?\n---\n?", "", text, flags=re.DOTALL)
    # Fenced code blocks
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    # Inline code
    text = re.sub(r"`[^`]+`", " ", text)
    # URLs
    text = re.sub(r"https?://\S+", " ", text)
    # HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Remaining markdown syntax characters
    text = re.sub(r"[#*_\[\]()!|>~]", " ", text)
    return text


def tokenize(text: str) -> list:
    return re.findall(r"[a-z]+", text.lower())


def compute_reading_time(word_count: int) -> int:
    if word_count == 0:
        return 0
    return math.ceil(word_count / 238)


def compute_top_words(tokens: list) -> list:
    filtered = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    counts = Counter(filtered)
    # Deterministic tie-breaking: frequency desc, then alphabetical
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:10]


def analyze_file(path: Path) -> dict:
    text = read_file(path)
    if text is None:
        return {"file": path.name, "word_count": 0, "reading_time_min": 0, "top_words": []}
    return analyze_content(path.name, path.suffix, text)


def analyze_content(filename: str, suffix: str, text: str) -> dict:
    """Analyze already-read text content — use this when file I/O is handled externally."""
    cleaned = clean_text(text, suffix)
    tokens = tokenize(cleaned)
    return {
        "file": filename,
        "word_count": len(tokens),
        "reading_time_min": compute_reading_time(len(tokens)),
        "top_words": compute_top_words(tokens),
    }


def serialize_text(results: list) -> None:
    if not results:
        return

    H = "─"
    TOP_W = 50  # max chars per line in the Top 10 Words cell

    def wrap_top(items, width):
        """Wrap 'word (freq), ...' items to fit within width, breaking at item boundaries."""
        lines, current = [], ""
        for item in items:
            chunk = item if not current else f", {item}"
            if len(current) + len(chunk) <= width:
                current += chunk
            else:
                if current:
                    lines.append(current)
                current = item
        if current:
            lines.append(current)
        return lines or ["(no words found)"]

    # Column content widths
    file_w  = max(max(len(r["file"]) for r in results), 4)
    words_w = max(max(len(f"{r['word_count']:,}") for r in results), len("Word Count"))
    time_w  = max(max(len(f"{r['reading_time_min']} min") for r in results), len("Reading Time"))
    top_w   = TOP_W

    cols = (file_w + 2, words_w + 2, time_w + 2, top_w + 2)

    def hline(left, m, r):
        return left + m.join(H * w for w in cols) + r

    def row(file="", words="", time="", top=""):
        return (
            "│" + f" {file:<{file_w}} " +
            "│" + f" {words:>{words_w}} " +
            "│" + f" {time:>{time_w}} " +
            "│" + f" {top:<{top_w}} " +
            "│"
        )

    lines = [
        hline("┌", "┬", "┐"),
        row("File", "Word Count", "Reading Time", "Top 10 Words"),
        hline("├", "┼", "┤"),
    ]

    for i, result in enumerate(results):
        fname    = result["file"]
        wc       = f"{result['word_count']:,}"
        rt       = f"{result['reading_time_min']} min"
        items    = [f"{w} ({f})" for w, f in result["top_words"]]
        top_lines = wrap_top(items, top_w)

        for j, tl in enumerate(top_lines):
            if j == 0:
                lines.append(row(fname, wc, rt, tl))
            else:
                lines.append(row("", "", "", tl))

        if i < len(results) - 1:
            lines.append(hline("├", "┼", "┤"))

    lines.append(hline("└", "┴", "┘"))
    print("\n".join(lines))


def serialize_csv(results: list) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(["file", "word_count", "reading_time_min", "rank", "word", "frequency"])
    for result in results:
        top_words = result["top_words"]
        if not top_words:
            writer.writerow([result["file"], result["word_count"], result["reading_time_min"], "", "", ""])
        else:
            for rank, (word, freq) in enumerate(top_words, start=1):
                writer.writerow([
                    result["file"],
                    result["word_count"],
                    result["reading_time_min"],
                    rank,
                    word,
                    freq,
                ])


def serialize_json(results: list) -> None:
    output = [
        {
            "file": r["file"],
            "word_count": r["word_count"],
            "reading_time_min": r["reading_time_min"],
            "top_words": [{"word": w, "frequency": f} for w, f in r["top_words"]],
        }
        for r in results
    ]
    print(json.dumps(output, indent=2))


def main():
    args = parse_args()

    if args.files or args.folders:
        files = []
        if args.files:
            for p in args.files:
                if p.suffix not in (".md", ".txt"):
                    continue
                if not p.is_file():
                    print(f"Warning: '{p}' not found, skipping.", file=sys.stderr)
                    continue
                files.append(p)
        if args.folders:
            for folder in args.folders:
                if not folder.is_dir():
                    print(f"Warning: folder '{folder}' not found, skipping.", file=sys.stderr)
                    continue
                files.extend(
                    p for p in sorted(folder.iterdir())
                    if p.suffix in (".md", ".txt") and p.is_file()
                )
        # Deduplicate while preserving order
        seen = set()
        files = [p for p in files if not (p in seen or seen.add(p))]
    else:
        files = discover_files(args.input_dir)

    results = [analyze_file(path) for path in files]
    if args.json:
        serialize_json(results)
    elif args.csv:
        serialize_csv(results)
    else:
        serialize_text(results)


if __name__ == "__main__":
    main()
