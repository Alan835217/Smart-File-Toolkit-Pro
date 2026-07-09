"""
pages_/batch_page.py
----------------------
Batch Processing page: apply one operation to many files at once and
download everything as a single zip. Covers the most common bulk needs:
batch image conversion/compression and batch PDF compression/protection.
"""

from __future__ import annotations

import streamlit as st

from modules import image_tools, pdf_tools, security_tools
from modules.image_tools import ImageToolError
from modules.pdf_tools import PDFToolError
from modules.security_tools import SecurityToolError
from utils.file_utils import bytes_to_zip, cleanup_dir, human_readable_size, new_session_dir, save_uploaded_files
from utils.ui_utils import empty_state, info_card, page_header, result_metric_row


def render() -> None:
    page_header("Batch Processing", "Run one operation across many files at once.", "📦")

    operation = st.selectbox(
        "Choose a batch operation",
        [
            "Convert images to a format",
            "Compress images",
            "Compress PDFs",
            "Password-protect PDFs",
        ],
        key="batch_op",
    )

    if operation == "Convert images to a format":
        _batch_convert_images()
    elif operation == "Compress images":
        _batch_compress_images()
    elif operation == "Compress PDFs":
        _batch_compress_pdfs()
    else:
        _batch_protect_pdfs()


def _batch_convert_images() -> None:
    info_card("How it works", "Upload several images and convert them all to the same target format.")
    files = st.file_uploader(
        "Upload images", type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"],
        accept_multiple_files=True, key="batch_conv_upl",
    )
    if not files:
        empty_state("Upload one or more images.")
        return

    col1, col2 = st.columns(2)
    with col1:
        target_format = st.selectbox("Target format", ["PNG", "JPEG", "WEBP", "BMP", "TIFF"], key="batch_conv_fmt")
    with col2:
        quality = st.slider("Quality", 10, 100, 85, key="batch_conv_quality")

    if st.button(f"Convert {len(files)} image(s)", type="primary", key="batch_conv_btn"):
        outputs: dict[str, bytes] = {}
        errors: list[str] = []
        ext = target_format.lower().replace("jpeg", "jpg")

        progress = st.progress(0.0)
        for i, f in enumerate(files, start=1):
            try:
                result = image_tools.convert_format(f.getvalue(), target_format, quality=quality)
                outputs[f"{f.name.rsplit('.', 1)[0]}.{ext}"] = result
            except ImageToolError as exc:
                errors.append(f"{f.name}: {exc}")
            progress.progress(i / len(files))

        _report_batch_result(outputs, errors)


def _batch_compress_images() -> None:
    info_card("How it works", "Upload several images and shrink them all at the same quality setting.")
    files = st.file_uploader(
        "Upload images", type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"],
        accept_multiple_files=True, key="batch_compress_upl",
    )
    if not files:
        empty_state("Upload one or more images.")
        return

    quality = st.slider("Quality", 10, 95, 60, key="batch_compress_quality")

    if st.button(f"Compress {len(files)} image(s)", type="primary", key="batch_compress_btn"):
        outputs: dict[str, bytes] = {}
        errors: list[str] = []
        total_before = total_after = 0

        progress = st.progress(0.0)
        for i, f in enumerate(files, start=1):
            try:
                data = f.getvalue()
                result = image_tools.compress_image(data, quality=quality)
                outputs[f.name] = result
                total_before += len(data)
                total_after += len(result)
            except ImageToolError as exc:
                errors.append(f"{f.name}: {exc}")
            progress.progress(i / len(files))

        if outputs:
            saved_pct = max(0, round((1 - total_after / total_before) * 100)) if total_before else 0
            result_metric_row({
                "Before": human_readable_size(total_before),
                "After": human_readable_size(total_after),
                "Saved": f"{saved_pct}%",
            })
        _report_batch_result(outputs, errors)


def _batch_compress_pdfs() -> None:
    info_card("How it works", "Upload several PDFs and compress embedded images in each at once.")
    files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True, key="batch_pdf_compress_upl")
    if not files:
        empty_state("Upload one or more PDFs.")
        return

    quality = st.slider("Image quality", 10, 95, 60, key="batch_pdf_quality")

    if st.button(f"Compress {len(files)} PDF(s)", type="primary", key="batch_pdf_compress_btn"):
        session_dir = new_session_dir()
        outputs: dict[str, bytes] = {}
        errors: list[str] = []
        try:
            paths = save_uploaded_files(files, session_dir)
            progress = st.progress(0.0)
            for i, path in enumerate(paths, start=1):
                try:
                    result = pdf_tools.compress_pdf(path, image_quality=quality)
                    outputs[f"{path.stem}_compressed.pdf"] = result
                except PDFToolError as exc:
                    errors.append(f"{path.name}: {exc}")
                progress.progress(i / len(paths))
            _report_batch_result(outputs, errors)
        finally:
            cleanup_dir(session_dir)


def _batch_protect_pdfs() -> None:
    info_card("How it works", "Upload several PDFs and protect them all with the same password.")
    files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True, key="batch_pdf_protect_upl")
    if not files:
        empty_state("Upload one or more PDFs.")
        return

    password = st.text_input("Password for all files", type="password", key="batch_pdf_protect_pw")

    if st.button(f"Protect {len(files)} PDF(s)", type="primary", key="batch_pdf_protect_btn"):
        if not password:
            st.error("Please enter a password.")
            return

        session_dir = new_session_dir()
        try:
            paths = save_uploaded_files(files, session_dir)
            with st.spinner("Encrypting all files..."):
                try:
                    outputs, errors = security_tools.batch_protect_pdfs(paths, password)
                except SecurityToolError as exc:
                    st.error(str(exc))
                    return
            _report_batch_result(outputs, errors)
        finally:
            cleanup_dir(session_dir)


def _report_batch_result(outputs: dict[str, bytes], errors: list[str]) -> None:
    if outputs:
        zip_bytes = bytes_to_zip(outputs)
        st.success(f"Successfully processed {len(outputs)} file(s).")
        st.download_button(
            "⬇️ Download all as .zip", data=zip_bytes, file_name="batch_output.zip",
            mime="application/zip", type="primary",
        )
    if errors:
        with st.expander(f"⚠️ {len(errors)} file(s) failed"):
            for e in errors:
                st.write(f"- {e}")
    if not outputs and not errors:
        st.info("Nothing to process.")
