"""
modules/ocr_tools.py
---------------------
OCR (Optical Character Recognition) helpers built on Tesseract via
pytesseract. Handles both plain images and scanned PDFs (by rasterizing
pages first through modules.pdf_tools.pdf_pages_to_images).

A light OpenCV preprocessing pass (grayscale + adaptive threshold) is
applied before OCR, which meaningfully improves accuracy on scanned or
photographed documents with uneven lighting.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image

from modules.pdf_tools import PDFToolError, pdf_pages_to_images


class OCRToolError(Exception):
    """Raised for any user-facing OCR failure."""


def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    """Grayscale + adaptive threshold to sharpen text against its
    background, which materially improves Tesseract's accuracy on
    scans and photos.
    """
    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
    )
    return Image.fromarray(thresh)


def extract_text_from_image(
    data: bytes,
    lang: str = "eng",
    preprocess: bool = True,
) -> str:
    """Run OCR on a single image and return the recognized text."""
    import io

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as exc:
        raise OCRToolError(f"Could not read image: {exc}") from exc

    if preprocess:
        img = _preprocess_for_ocr(img)

    try:
        return pytesseract.image_to_string(img, lang=lang)
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRToolError(
            "Tesseract OCR engine is not installed or not on PATH. "
            "See requirements.txt for install instructions."
        ) from exc
    except pytesseract.TesseractError as exc:
        raise OCRToolError(f"OCR failed: {exc}") from exc


def extract_text_from_pdf(
    path: Path,
    lang: str = "eng",
    dpi: int = 200,
    password: str | None = None,
    preprocess: bool = True,
) -> dict[int, str]:
    """Run OCR over every page of a (typically scanned) PDF.

    Use this when modules.pdf_tools.extract_text returns empty strings,
    which indicates the PDF has no embedded text layer.
    """
    try:
        pages = pdf_pages_to_images(path, dpi=dpi, password=password)
    except PDFToolError as exc:
        raise OCRToolError(str(exc)) from exc

    results: dict[int, str] = {}
    for i, page_img in enumerate(pages, start=1):
        img = _preprocess_for_ocr(page_img) if preprocess else page_img
        try:
            results[i] = pytesseract.image_to_string(img, lang=lang)
        except pytesseract.TesseractNotFoundError as exc:
            raise OCRToolError(
                "Tesseract OCR engine is not installed or not on PATH."
            ) from exc
    return results


def get_available_languages() -> list[str]:
    """Return the Tesseract language packs actually installed on this
    machine, so the UI can hide options the user hasn't installed.
    """
    try:
        return pytesseract.get_languages(config="")
    except Exception:
        return ["eng"]
