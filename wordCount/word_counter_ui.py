"""Streamlit UI for the Word Counter tab."""
import csv
import io
import json

import streamlit as st

from .word_analyzer import analyze_content


def render_word_counter_tab(prefix: str = "wc_") -> None:
    """Render the Word Counter UI inside a Streamlit tab or page."""

    uploaded_files = st.file_uploader(
        "Upload .md or .txt files",
        type=["md", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if not uploaded_files:
        st.info("Upload one or more `.md` or `.txt` files above to get started.")
        return

    results = []
    for f in uploaded_files:
        suffix = "." + f.name.rsplit(".", 1)[-1].lower()
        try:
            text = f.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            f.seek(0)
            try:
                text = f.read().decode("latin-1")
            except Exception:
                st.warning(f"Could not decode `{f.name}` — skipping.")
                continue
        results.append(analyze_content(f.name, suffix, text))

    if not results:
        return

    # ── Summary metrics ───────────────────────────────────────────────────────

    total_words = sum(r["word_count"] for r in results)
    total_time  = sum(r["reading_time_min"] for r in results)

    m1, m2, m3 = st.columns(3)
    m1.metric("Files analyzed", len(results))
    m2.metric("Total words", f"{total_words:,}")
    m3.metric("Est. reading time", f"{total_time} min")

    st.divider()

    # ── Per-file cards ────────────────────────────────────────────────────────

    for result in results:
        with st.expander(f"📄 {result['file']}  —  {result['word_count']:,} words · {result['reading_time_min']} min read"):
            top = result["top_words"]
            if top:
                cols = st.columns(5)
                for i, (word, freq) in enumerate(top):
                    cols[i % 5].metric(word, freq)
            else:
                st.caption("No significant words found.")

    st.divider()

    # ── Export ────────────────────────────────────────────────────────────────

    dl_col1, dl_col2 = st.columns([1, 1])

    with dl_col1:
        # CSV export
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["file", "word_count", "reading_time_min", "rank", "word", "frequency"])
        for r in results:
            top_words = r["top_words"]
            if not top_words:
                writer.writerow([r["file"], r["word_count"], r["reading_time_min"], "", "", ""])
            else:
                for rank, (word, freq) in enumerate(top_words, start=1):
                    writer.writerow([r["file"], r["word_count"], r["reading_time_min"], rank, word, freq])
        st.download_button(
            "Download CSV",
            data=buf.getvalue().encode(),
            file_name="word_analysis.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with dl_col2:
        json_data = json.dumps(
            [
                {
                    "file": r["file"],
                    "word_count": r["word_count"],
                    "reading_time_min": r["reading_time_min"],
                    "top_words": [{"word": w, "frequency": f} for w, f in r["top_words"]],
                }
                for r in results
            ],
            indent=2,
        )
        st.download_button(
            "Download JSON",
            data=json_data.encode(),
            file_name="word_analysis.json",
            mime="application/json",
            use_container_width=True,
        )
