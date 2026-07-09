"""
pages_/home.py
---------------
Landing page: hero section + grid of tool cards linking (via session
state) into each feature page.
"""

from __future__ import annotations

import streamlit as st

from config import APP_NAME, APP_TAGLINE
from utils.ui_utils import page_header, section_divider, tool_grid_card

TOOLS = [
    {"icon": "🔗", "title": "Merge PDFs", "desc": "Combine multiple PDFs into one document, in any order.", "nav": "pdf"},
    {"icon": "✂️", "title": "Split PDFs", "desc": "Extract page ranges or split every page into its own file.", "nav": "pdf"},
    {"icon": "🗜️", "title": "Compress PDF/Image", "desc": "Shrink file sizes by re-encoding embedded images.", "nav": "pdf"},
    {"icon": "🔄", "title": "Convert Images", "desc": "Convert between PNG, JPEG, WEBP, BMP, and TIFF.", "nav": "image"},
    {"icon": "🖌️", "title": "Watermark PDFs", "desc": "Stamp diagonal text watermarks onto every page.", "nav": "pdf"},
    {"icon": "🔎", "title": "OCR Text Extraction", "desc": "Pull text out of scanned PDFs and photographed documents.", "nav": "ocr"},
    {"icon": "🔒", "title": "Password Protect", "desc": "Encrypt PDFs, or any file, with a password.", "nav": "security"},
    {"icon": "🖼️", "title": "Image Editing", "desc": "Resize, crop, rotate, filter, and enhance images.", "nav": "image"},
    {"icon": "📦", "title": "Batch Processing", "desc": "Run one operation across many files at once.", "nav": "batch"},
]


def render() -> None:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 1.5rem 0 0.5rem 0;">
            <div style="font-size:2.4rem; font-weight:800; color:#1F2937;">
                🗂️ {APP_NAME}
            </div>
            <div style="font-size:1.15rem; color:#6B7280; margin-top:0.4rem;">
                {APP_TAGLINE}
            </div>
            <div style="font-size:0.95rem; color:#9CA3AF; margin-top:0.6rem;">
                Merge, split, compress, watermark, and secure PDFs · Edit and convert images · Extract text with OCR — all in one place, no uploads to third-party sites.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    section_divider()

    st.markdown("#### Everything you need, in one workspace")

    cols_per_row = 3
    for row_start in range(0, len(TOOLS), cols_per_row):
        row_tools = TOOLS[row_start: row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, tool in zip(cols, row_tools):
            with col:
                st.markdown(
                    tool_grid_card(tool["icon"], tool["title"], tool["desc"]),
                    unsafe_allow_html=True,
                )
                if st.button("Open →", key=f"home_btn_{tool['title']}", use_container_width=True):
                    st.session_state["nav_key"] = tool["nav"]
                    st.rerun()

    section_divider()

    with st.expander("Why Smart File Toolkit Pro?"):
        st.markdown(
            """
- **One interface** instead of a dozen different websites and apps.
- **Privacy-minded**: files are processed in memory for your session; nothing is sent to a third-party conversion service.
- **Offline-capable**: once installed, the core tools run entirely on your own machine.
- **Built for everyone**: students, teachers, HR & recruiting, freelancers, designers, developers, and small businesses.
            """
        )
