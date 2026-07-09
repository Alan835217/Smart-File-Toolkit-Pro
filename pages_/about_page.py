"""
pages_/about_page.py
----------------------
Static About page describing the project, its architecture, and roadmap.
"""

from __future__ import annotations

import streamlit as st

from config import APP_NAME, APP_VERSION
from utils.ui_utils import page_header, section_divider


def render() -> None:
    page_header("About", f"{APP_NAME} v{APP_VERSION}", "ℹ️")

    st.markdown(
        """
Smart File Toolkit Pro is a unified workspace for everyday document tasks —
merging and splitting PDFs, compressing files, converting images, extracting
text with OCR, and securing documents — so you don't need a dozen different
websites to get through a day's paperwork.
        """
    )

    section_divider()
    st.markdown("#### 🎯 Target users")
    st.markdown(
        "Students · Teachers · Office employees · HR professionals · Recruiters · "
        "Freelancers · Designers · Developers · Small businesses"
    )

    section_divider()
    st.markdown("#### 🏗️ Architecture")
    st.markdown(
        """
The app follows a **service-oriented, modular architecture**:

- **`app.py`** — routing and sidebar navigation only.
- **`pages_/`** — one file per feature area (PDF, Image, OCR, Security, Batch); presentation and orchestration only.
- **`modules/`** — pure business logic (`pdf_tools`, `image_tools`, `ocr_tools`, `security_tools`); no Streamlit imports, fully reusable/testable on their own.
- **`utils/`** — shared helpers for filesystem operations and UI components.
- **`config.py`** — single source of truth for constants, limits, and navigation.

This separation means new tools can be added by dropping in a new module + page,
without touching existing code, and the core logic could power a CLI or API in the future.
        """
    )

    section_divider()
    st.markdown("#### 🧰 Technology stack")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
**Frontend**
- Streamlit
- Custom CSS

**PDF processing**
- pypdf
- ReportLab (watermarks)
- pdf2image / poppler (rasterization)
            """
        )
    with col2:
        st.markdown(
            """
**Image processing**
- Pillow (PIL)
- OpenCV

**OCR**
- Tesseract OCR
- pytesseract

**Data / utilities**
- Pandas, io, zipfile, pathlib, shutil
            """
        )

    section_divider()
    st.markdown("#### 🗺️ Roadmap")
    st.markdown(
        """
- [ ] User accounts (SQLAlchemy + SQLite + bcrypt) for saved preferences and history
- [ ] ML-based background removal
- [ ] Digital signatures for PDFs
- [ ] Drag-and-drop page reordering for merge/split
- [ ] Dark mode theme
        """
    )

    section_divider()
    st.caption("Built with Python, Streamlit, and open-source document/image libraries.")
