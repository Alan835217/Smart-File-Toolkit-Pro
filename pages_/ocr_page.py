"""
pages_/ocr_page.py
--------------------
OCR / Text Extraction page: run Tesseract OCR on an image or a scanned
PDF and let the user copy/download the recognized text.
"""

from __future__ import annotations

import streamlit as st

from config import SUPPORTED_OCR_LANGS
from modules import ocr_tools, pdf_tools
from modules.ocr_tools import OCRToolError
from utils.file_utils import cleanup_dir, new_session_dir, save_uploaded_file
from utils.ui_utils import empty_state, info_card, page_header


def render() -> None:
    page_header("OCR / Text Extraction", "Extract text from images and scanned PDFs using Tesseract OCR.", "🔎")
    info_card(
        "Tip",
        "For scanned/photographed pages, OCR is required since there's no embedded text layer. "
        "For regular text-based PDFs, the 'Extract Text' tab under PDF Tools is faster and more accurate.",
    )

    file = st.file_uploader(
        "Upload an image or PDF",
        type=["png", "jpg", "jpeg", "webp", "bmp", "tiff", "pdf"],
        key="ocr_upl",
    )

    if not file:
        empty_state("Upload a scanned document or photo to extract its text.")
        return

    available_langs = ocr_tools.get_available_languages()
    lang_options = {name: code for name, code in SUPPORTED_OCR_LANGS.items() if code in available_langs}
    if not lang_options:
        lang_options = {"English": "eng"}

    col1, col2 = st.columns(2)
    with col1:
        lang_name = st.selectbox("Language", list(lang_options.keys()), key="ocr_lang")
    with col2:
        preprocess = st.checkbox("Enhance scan before OCR (recommended)", value=True, key="ocr_preprocess")

    is_pdf = file.name.lower().endswith(".pdf")

    if is_pdf:
        _render_pdf_ocr(file, lang_options[lang_name], preprocess)
    else:
        _render_image_ocr(file, lang_options[lang_name], preprocess)


def _render_image_ocr(file, lang_code: str, preprocess: bool) -> None:
    data = file.getvalue()
    st.image(data, caption="Preview", use_container_width=True)

    if st.button("Extract Text", type="primary", key="ocr_img_btn"):
        try:
            with st.spinner("Running OCR..."):
                text = ocr_tools.extract_text_from_image(data, lang=lang_code, preprocess=preprocess)
        except OCRToolError as exc:
            st.error(str(exc))
            return

        if not text.strip():
            st.warning("No text was detected in this image.")
        else:
            st.success("Text extracted.")

        st.text_area("Extracted text", text, height=300)
        st.download_button(
            "⬇️ Download as .txt", data=text.encode("utf-8"),
            file_name=f"{file.name.rsplit('.',1)[0]}_ocr.txt", mime="text/plain",
        )


def _render_pdf_ocr(file, lang_code: str, preprocess: bool) -> None:
    session_dir = new_session_dir()
    try:
        path = save_uploaded_file(file, session_dir)
        info = pdf_tools.get_pdf_info(path)
        password = None
        if info.encrypted:
            password = st.text_input("This PDF is password protected — enter the password", type="password", key="ocr_pdf_pw")
            if not password:
                st.stop()

        dpi = st.select_slider("Render quality (DPI)", options=[100, 150, 200, 300], value=200, key="ocr_dpi")
        st.caption("Higher DPI improves accuracy on small text but takes longer.")

        if st.button("Run OCR on all pages", type="primary", key="ocr_pdf_btn"):
            with st.spinner("Rendering pages and running OCR — this can take a moment for multi-page documents..."):
                pages_text = ocr_tools.extract_text_from_pdf(
                    path, lang=lang_code, dpi=dpi, password=password, preprocess=preprocess
                )

            full_text = "\n\n".join(f"--- Page {n} ---\n{t}" for n, t in pages_text.items())
            non_empty = sum(1 for t in pages_text.values() if t.strip())
            st.success(f"OCR complete — text found on {non_empty}/{len(pages_text)} page(s).")

            st.text_area("Extracted text", full_text, height=350)
            st.download_button(
                "⬇️ Download as .txt", data=full_text.encode("utf-8"),
                file_name=f"{path.stem}_ocr.txt", mime="text/plain",
            )
    except OCRToolError as exc:
        st.error(str(exc))
    except pdf_tools.PDFToolError as exc:
        st.error(str(exc))
    finally:
        cleanup_dir(session_dir)
