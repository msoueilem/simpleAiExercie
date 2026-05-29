"""Unified AI Tools web app — PDF Reviewer + Word Counter."""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Tools Suite", layout="wide")
st.title("AI Tools Suite")

tab_pdf, tab_wc = st.tabs(["📄 PDF Reviewer", "📝 Word Counter"])

with tab_pdf:
    from pdfReviewer.pdf_reviewer import render_pdf_tab
    render_pdf_tab()

with tab_wc:
    from wordCount.word_counter_ui import render_word_counter_tab
    render_word_counter_tab()
