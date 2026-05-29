"""Streamlit UI for the PDF Reviewer tab.

Call render_pdf_tab() from a parent app, or run this file directly as a
standalone Streamlit app (streamlit run pdf_reviewer.py).
"""
import base64

import streamlit as st

from .core import (
    ANALYSIS_STEPS,
    SEVERITY_CONFIG,
    build_prompt,
    extract_text,
    parse_issues,
    render_pdf_first_page,
)
from .llm_providers import ProviderError, get_provider


def _init_state(prefix: str) -> None:
    defaults = {
        f"{prefix}pdf_bytes": None,
        f"{prefix}page_image": None,
        f"{prefix}issues": None,
        f"{prefix}last_filename": None,
        f"{prefix}upload_key": 0,
        f"{prefix}raw_response": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _clear_state(prefix: str) -> None:
    for key in ("pdf_bytes", "page_image", "issues", "last_filename", "raw_response"):
        st.session_state[f"{prefix}{key}"] = None


def _render_steps(done: int, current_label: str | None = None) -> str:
    lines = []
    for i, step in enumerate(ANALYSIS_STEPS):
        if i < done:
            icon, style = "✅", "color:#27ae60;"
            label = step
        elif i == done:
            icon, style = "⏳", "color:#f39c12;font-weight:600;"
            label = current_label if current_label else step
        else:
            icon, style = "⬜", "color:#888;"
            label = step
        lines.append(
            f'<div style="{style}padding:5px 0;font-size:0.95em;">'
            f"{icon}&nbsp;&nbsp;{label}</div>"
        )
    return "<div style='line-height:1.8'>" + "\n".join(lines) + "</div>"


def _render_issues(issues: list[dict]) -> None:
    if not issues:
        st.success("No issues found.")
        return

    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    for item in sorted(issues, key=lambda x: severity_order.get(x.get("severity", "LOW"), 3)):
        sev = item.get("severity", "LOW").upper()
        cfg = SEVERITY_CONFIG.get(sev, SEVERITY_CONFIG["LOW"])
        st.markdown(
            f"""
            <div style="
                background:{cfg['bg']};
                border-left:4px solid {cfg['color']};
                border-radius:4px;
                padding:10px 14px;
                margin-bottom:10px;
            ">
                <span style="color:{cfg['color']};font-weight:700;">
                    {cfg['icon']} {sev}
                </span>
                &nbsp;&nbsp;<strong>{item.get('issue', '')}</strong><br>
                <small style="color:#555;">
                    <em>{item.get('location', '')}</em> — {item.get('description', '')}
                </small>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _run_analysis(placeholder, llm_provider, prefix: str) -> None:
    n = len(ANALYSIS_STEPS)

    def _update(step: int, label: str | None = None) -> None:
        with placeholder.container():
            st.progress(step / n)
            st.markdown(_render_steps(step, label), unsafe_allow_html=True)

    try:
        _update(0)
        extracted_text = extract_text(st.session_state[f"{prefix}pdf_bytes"])

        _update(1)
        image_b64 = base64.b64encode(st.session_state[f"{prefix}page_image"]).decode()
        prompt = build_prompt(extracted_text)

        _update(2)  # "Connecting to AI provider"

        # Stream the response — on_chunk fires for every incoming text chunk.
        # UI updates are throttled: only re-render every 50 chars to avoid
        # hammering Streamlit on fast-streaming models.
        chars_received = [0]
        last_render_at = [0]

        def on_chunk(text: str) -> None:
            chars_received[0] += len(text)
            if chars_received[0] - last_render_at[0] >= 50:
                last_render_at[0] = chars_received[0]
                _update(3, f"Receiving AI response… {chars_received[0]:,} chars")

        raw = llm_provider.analyze_document(
            image_b64=image_b64,
            extracted_text=extracted_text,
            prompt=prompt,
            on_chunk=on_chunk,
        )
        st.session_state[f"{prefix}raw_response"] = raw

        _update(4)
        issues = parse_issues(raw)
        st.session_state[f"{prefix}issues"] = issues

        _update(5)
        try:
            png_bytes = render_pdf_first_page(
                st.session_state[f"{prefix}pdf_bytes"],
                highlights=issues,
            )
            st.session_state[f"{prefix}page_image"] = png_bytes
        except Exception as e:
            print(f"Non-fatal error drawing highlights: {e}")

        _update(n)

    except ProviderError as e:
        placeholder.error(str(e))
    except __import__("json").JSONDecodeError:
        placeholder.warning("The model returned an unexpected format. Showing raw response.")
        st.code(st.session_state.get(f"{prefix}raw_response", ""), language="text")
    except Exception as e:
        placeholder.error(f"Unexpected error: {e}")


def render_pdf_tab(prefix: str = "pdf_") -> None:
    """Render the full PDF Reviewer UI inside a Streamlit tab or page.

    Args:
        prefix: Session-state key prefix — change this if embedding multiple
                instances in the same app to avoid key collisions.
    """
    try:
        llm_provider = get_provider()
    except ValueError as e:
        st.error(f"**Configuration Error:** {e}")
        return

    _init_state(prefix)

    uploaded_file = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
        key=f"uploader_{st.session_state[f'{prefix}upload_key']}",
        label_visibility="collapsed",
    )

    if uploaded_file is None:
        _clear_state(prefix)
        st.info("Upload a PDF above to get started.")
        return

    if uploaded_file.name != st.session_state[f"{prefix}last_filename"]:
        pdf_bytes = uploaded_file.read()
        try:
            png_bytes = render_pdf_first_page(pdf_bytes)
        except ValueError:
            st.error("This PDF appears to be empty.")
            return
        except Exception:
            st.error("Could not read this PDF. It may be corrupted or password-protected.")
            return

        st.session_state[f"{prefix}pdf_bytes"] = pdf_bytes
        st.session_state[f"{prefix}page_image"] = png_bytes
        st.session_state[f"{prefix}last_filename"] = uploaded_file.name
        st.session_state[f"{prefix}issues"] = None
        st.session_state[f"{prefix}raw_response"] = None

    col_pdf, col_issues = st.columns([1, 1], gap="large")

    with col_pdf:
        st.subheader("PDF Preview")
        st.caption(f"Page 1 of {uploaded_file.name}")
        st.image(st.session_state[f"{prefix}page_image"], use_container_width=True)

    with col_issues:
        st.subheader("Analysis")

        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            label = "Re-analyze" if st.session_state[f"{prefix}issues"] is not None else "Analyze PDF"
            analyze_clicked = st.button(label, type="primary", use_container_width=True)
        with btn_col2:
            upload_new_clicked = st.button("Upload New PDF", use_container_width=True)

        st.divider()
        progress_placeholder = st.empty()

        if st.session_state[f"{prefix}issues"] is not None:
            issues = st.session_state[f"{prefix}issues"]
            highs = sum(1 for i in issues if i.get("severity") == "HIGH")
            meds  = sum(1 for i in issues if i.get("severity") == "MEDIUM")
            lows  = sum(1 for i in issues if i.get("severity") == "LOW")
            st.caption(f"{len(issues)} issue(s) found — 🔴 {highs} HIGH · 🟠 {meds} MEDIUM · 🔵 {lows} LOW")
            st.write("")
            _render_issues(issues)
        else:
            progress_placeholder.info("Click **Analyze PDF** to begin.")

    if analyze_clicked:
        _run_analysis(progress_placeholder, llm_provider, prefix)
        st.rerun()

    if upload_new_clicked:
        _clear_state(prefix)
        st.session_state[f"{prefix}upload_key"] += 1
        st.rerun()


if __name__ == "__main__":
    # Standalone mode: run directly as `streamlit run pdf_reviewer.py`
    from dotenv import load_dotenv
    load_dotenv()
    st.set_page_config(page_title="PDF Reviewer", layout="wide")
    st.title("PDF Reviewer")
    st.caption("Upload a PDF to identify errors, inconsistencies, and quality issues.")
    render_pdf_tab()
