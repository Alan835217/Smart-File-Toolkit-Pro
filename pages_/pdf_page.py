"""
pages_/pdf_page.py
--------------------
PDF Tools page: merge, split, rotate, compress, watermark, and extract
text — each in its own tab. All heavy lifting happens in
modules.pdf_tools; this file is purely presentational/orchestration.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from modules import pdf_tools
from modules.pdf_tools import PDFToolError
from utils.file_utils import (
    bytes_to_zip,
    cleanup_dir,
    human_readable_size,
    new_session_dir,
    save_uploaded_file,
    save_uploaded_files,
)
from utils.ui_utils import empty_state, info_card, page_header, result_metric_row, section_divider


def render() -> None:
    page_header("PDF Tools", "Merge, split, rotate, compress, watermark, and extract text from PDFs.", "📄")

    tabs = st.tabs(["🔗 Merge", "✂️ Split", "🔄 Rotate", "🗜️ Compress", "🖌️ Watermark", "📝 Extract Text"])

    with tabs[0]:
        _render_merge()
    with tabs[1]:
        _render_split()
    with tabs[2]:
        _render_rotate()
    with tabs[3]:
        _render_compress()
    with tabs[4]:
        _render_watermark()
    with tabs[5]:
        _render_extract_text()


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------
def _render_merge() -> None:
    info_card("How it works", "Upload two or more PDFs. Drag to reorder them in the list below before merging.")
    files = st.file_uploader("Upload PDFs to merge", type=["pdf"], accept_multiple_files=True, key="merge_upl")

    if not files:
        empty_state("Upload 2+ PDF files to merge them into one document.")
        return

    if len(files) < 2:
        st.warning("Please upload at least two PDF files.")
        return

    names = [f.name for f in files]
    st.write("**Merge order** (edit the list below, top to bottom):")
    ordered_names = st.multiselect(
        "Order of files", names, default=names, label_visibility="collapsed"
    )
    if set(ordered_names) != set(names):
        st.warning("Please keep all uploaded files selected — remove a file by re-uploading without it.")
        return

    if st.button("Merge PDFs", type="primary"):
        session_dir = new_session_dir()
        try:
            name_to_file = {f.name: f for f in files}
            ordered_files = [name_to_file[n] for n in ordered_names]
            paths = save_uploaded_files(ordered_files, session_dir)

            with st.spinner("Merging..."):
                result_bytes = pdf_tools.merge_pdfs(paths)

            st.success(f"Merged {len(paths)} files into one PDF.")
            result_metric_row({"Output size": human_readable_size(len(result_bytes))})
            st.download_button(
                "⬇️ Download merged.pdf",
                data=result_bytes,
                file_name="merged.pdf",
                mime="application/pdf",
                type="primary",
            )
        except PDFToolError as exc:
            st.error(str(exc))
        finally:
            cleanup_dir(session_dir)


# ---------------------------------------------------------------------------
# Split
# ---------------------------------------------------------------------------
def _render_split() -> None:
    info_card(
        "How it works",
        "Upload one PDF. Either extract a specific page range, or split every page into its own file.",
    )
    file = st.file_uploader("Upload a PDF to split", type=["pdf"], key="split_upl")

    if not file:
        empty_state("Upload a PDF to split.")
        return

    session_dir = new_session_dir()
    try:
        path = save_uploaded_file(file, session_dir)
        info = pdf_tools.get_pdf_info(path)
        password = None
        if info.encrypted:
            password = st.text_input("This PDF is password protected — enter the password", type="password", key="split_pw")
            if not password:
                st.stop()
            info = pdf_tools.PDFInfo(
                num_pages=pdf_tools.get_page_count(path, password),
                encrypted=True, title=info.title, author=info.author, file_size_bytes=info.file_size_bytes,
            )

        st.caption(f"Document has **{info.num_pages}** page(s).")
        mode = st.radio("Split mode", ["Extract a page range", "Split every page into a separate file"], key="split_mode")

        if mode == "Extract a page range":
            range_str = st.text_input("Pages to extract (e.g. 1-3,5,8-10)", key="split_range")
            if st.button("Split PDF", type="primary", key="split_range_btn"):
                with st.spinner("Splitting..."):
                    result_bytes = pdf_tools.split_pdf_by_ranges(path, range_str, password)
                st.success("Done!")
                result_metric_row({"Output size": human_readable_size(len(result_bytes))})
                st.download_button(
                    "⬇️ Download split.pdf", data=result_bytes, file_name=f"{path.stem}_split.pdf",
                    mime="application/pdf", type="primary",
                )
        else:
            if st.button("Split into individual pages", type="primary", key="split_pages_btn"):
                with st.spinner("Splitting..."):
                    pages = pdf_tools.split_pdf_to_pages(path, password)
                zip_bytes = bytes_to_zip(pages)
                st.success(f"Split into {len(pages)} single-page PDFs.")
                result_metric_row({"Files": str(len(pages)), "Zip size": human_readable_size(len(zip_bytes))})
                st.download_button(
                    "⬇️ Download all pages (.zip)", data=zip_bytes, file_name=f"{path.stem}_pages.zip",
                    mime="application/zip", type="primary",
                )
    except PDFToolError as exc:
        st.error(str(exc))
    finally:
        cleanup_dir(session_dir)


# ---------------------------------------------------------------------------
# Rotate
# ---------------------------------------------------------------------------
def _render_rotate() -> None:
    info_card("How it works", "Rotate every page in a PDF by 90, 180, or 270 degrees.")
    file = st.file_uploader("Upload a PDF to rotate", type=["pdf"], key="rotate_upl")

    if not file:
        empty_state("Upload a PDF to rotate.")
        return

    angle = st.select_slider("Rotation angle", options=[90, 180, 270], value=90, key="rotate_angle")

    if st.button("Rotate PDF", type="primary"):
        session_dir = new_session_dir()
        try:
            path = save_uploaded_file(file, session_dir)
            info = pdf_tools.get_pdf_info(path)
            password = None
            if info.encrypted:
                password = st.text_input("Password required", type="password", key="rotate_pw")

            with st.spinner("Rotating..."):
                result_bytes = pdf_tools.rotate_pdf(path, angle, password)
            st.success("Done!")
            st.download_button(
                "⬇️ Download rotated.pdf", data=result_bytes, file_name=f"{path.stem}_rotated.pdf",
                mime="application/pdf", type="primary",
            )
        except PDFToolError as exc:
            st.error(str(exc))
        finally:
            cleanup_dir(session_dir)


# ---------------------------------------------------------------------------
# Compress
# ---------------------------------------------------------------------------
def _render_compress() -> None:
    info_card(
        "How it works",
        "Re-encodes embedded images at a lower quality to shrink file size. Text and vector content stay crisp.",
    )
    file = st.file_uploader("Upload a PDF to compress", type=["pdf"], key="compress_upl")

    if not file:
        empty_state("Upload a PDF to compress.")
        return

    quality = st.slider("Image quality", min_value=10, max_value=95, value=60, step=5, key="compress_quality")

    if st.button("Compress PDF", type="primary"):
        session_dir = new_session_dir()
        try:
            path = save_uploaded_file(file, session_dir)
            original_size = path.stat().st_size

            with st.spinner("Compressing..."):
                result_bytes = pdf_tools.compress_pdf(path, image_quality=quality)

            new_size = len(result_bytes)
            saved_pct = max(0, round((1 - new_size / original_size) * 100)) if original_size else 0

            st.success("Done!")
            result_metric_row({
                "Original size": human_readable_size(original_size),
                "New size": human_readable_size(new_size),
                "Saved": f"{saved_pct}%",
            })
            st.download_button(
                "⬇️ Download compressed.pdf", data=result_bytes, file_name=f"{path.stem}_compressed.pdf",
                mime="application/pdf", type="primary",
            )
        except PDFToolError as exc:
            st.error(str(exc))
        finally:
            cleanup_dir(session_dir)


# ---------------------------------------------------------------------------
# Watermark
# ---------------------------------------------------------------------------
def _render_watermark() -> None:
    info_card("How it works", "Stamp a diagonal, semi-transparent text watermark onto every page.")
    file = st.file_uploader("Upload a PDF to watermark", type=["pdf"], key="wm_upl")

    if not file:
        empty_state("Upload a PDF to add a watermark.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        text = st.text_input("Watermark text", value="CONFIDENTIAL", key="wm_text")
    with col2:
        opacity = st.slider("Opacity", 0.05, 1.0, 0.3, 0.05, key="wm_opacity")
    with col3:
        font_size = st.slider("Font size", 10, 100, 40, 2, key="wm_font")

    rotation = st.slider("Rotation (degrees)", -90, 90, 45, 5, key="wm_rotation")

    if st.button("Add Watermark", type="primary"):
        session_dir = new_session_dir()
        try:
            path = save_uploaded_file(file, session_dir)
            with st.spinner("Applying watermark..."):
                result_bytes = pdf_tools.add_watermark(
                    path, text, opacity=opacity, font_size=font_size, rotation=rotation
                )
            st.success("Done!")
            st.download_button(
                "⬇️ Download watermarked.pdf", data=result_bytes, file_name=f"{path.stem}_watermarked.pdf",
                mime="application/pdf", type="primary",
            )
        except PDFToolError as exc:
            st.error(str(exc))
        finally:
            cleanup_dir(session_dir)


# ---------------------------------------------------------------------------
# Extract text
# ---------------------------------------------------------------------------
def _render_extract_text() -> None:
    info_card(
        "How it works",
        "Extracts the embedded text layer. If a PDF is a scanned image with no text layer, use the OCR page instead.",
    )
    file = st.file_uploader("Upload a PDF to extract text from", type=["pdf"], key="extract_upl")

    if not file:
        empty_state("Upload a PDF to extract its text.")
        return

    session_dir = new_session_dir()
    try:
        path = save_uploaded_file(file, session_dir)
        info = pdf_tools.get_pdf_info(path)
        password = None
        if info.encrypted:
            password = st.text_input("Password required", type="password", key="extract_pw")
            if not password:
                st.stop()

        if st.button("Extract Text", type="primary"):
            with st.spinner("Extracting..."):
                pages_text = pdf_tools.extract_text(path, password)

            full_text = "\n\n".join(f"--- Page {n} ---\n{t}" for n, t in pages_text.items())
            non_empty = sum(1 for t in pages_text.values() if t.strip())

            if non_empty == 0:
                st.warning(
                    "No embedded text found — this looks like a scanned PDF. "
                    "Try the OCR / Text Extraction page instead."
                )
            else:
                st.success(f"Extracted text from {non_empty}/{len(pages_text)} page(s).")

            st.text_area("Extracted text", full_text, height=350)
            st.download_button(
                "⬇️ Download as .txt", data=full_text.encode("utf-8"),
                file_name=f"{path.stem}_text.txt", mime="text/plain",
            )
    except PDFToolError as exc:
        st.error(str(exc))
    finally:
        cleanup_dir(session_dir)
