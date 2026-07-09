"""
modules/pdf_tools.py
---------------------
Pure PDF processing logic: merge, split, rotate, compress, watermark,
password protect/unlock, metadata, and text/image extraction.

Design notes:
- Every public function takes/returns file paths or raw bytes rather than
  Streamlit objects, so this module can be imported and unit-tested (or
  reused in a CLI / API) completely independently of the web UI.
- pypdf handles structural operations (merge/split/rotate/encrypt).
- reportlab renders watermark overlays, which pypdf then merges onto pages.
- pdf2image (poppler) rasterizes pages to images for previews and for
  feeding scanned pages into the OCR module.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class PDFToolError(Exception):
    """Raised for any user-facing PDF processing failure."""


@dataclass
class PDFInfo:
    num_pages: int
    encrypted: bool
    title: Optional[str]
    author: Optional[str]
    file_size_bytes: int


# ---------------------------------------------------------------------------
# Inspection
# ---------------------------------------------------------------------------
def get_pdf_info(path: Path) -> PDFInfo:
    """Return basic metadata about a PDF without fully decrypting it."""
    reader = PdfReader(str(path))
    meta = reader.metadata or {}
    return PDFInfo(
        num_pages=len(reader.pages) if not reader.is_encrypted else 0,
        encrypted=reader.is_encrypted,
        title=getattr(meta, "title", None),
        author=getattr(meta, "author", None),
        file_size_bytes=Path(path).stat().st_size,
    )


def get_page_count(path: Path, password: str | None = None) -> int:
    """Return the number of pages in a PDF, decrypting first if needed."""
    reader = _open_reader(path, password)
    return len(reader.pages)


def _open_reader(path: Path, password: str | None = None) -> PdfReader:
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        if not password:
            raise PDFToolError(
                f"'{Path(path).name}' is password protected. Please supply the password."
            )
        result = reader.decrypt(password)
        if result == 0:
            raise PDFToolError(f"Incorrect password for '{Path(path).name}'.")
    return reader


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------
def merge_pdfs(paths: list[Path], passwords: dict[str, str] | None = None) -> bytes:
    """Concatenate multiple PDFs, in the given order, into one document."""
    if len(paths) < 2:
        raise PDFToolError("Select at least two PDF files to merge.")

    passwords = passwords or {}
    writer = PdfWriter()
    for path in paths:
        reader = _open_reader(path, passwords.get(Path(path).name))
        for page in reader.pages:
            writer.add_page(page)

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Split
# ---------------------------------------------------------------------------
def parse_page_ranges(range_str: str, num_pages: int) -> list[int]:
    """Parse a human string like '1-3,5,8-10' into a sorted list of
    zero-indexed page numbers, validated against the document length.
    """
    pages: set[int] = set()
    range_str = range_str.strip()
    if not range_str:
        raise PDFToolError("Please enter at least one page or page range.")

    for chunk in range_str.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start_s, _, end_s = chunk.partition("-")
            try:
                start, end = int(start_s), int(end_s)
            except ValueError:
                raise PDFToolError(f"Invalid range: '{chunk}'")
            if start < 1 or end > num_pages or start > end:
                raise PDFToolError(
                    f"Range '{chunk}' is out of bounds for a {num_pages}-page document."
                )
            pages.update(range(start - 1, end))
        else:
            try:
                page_num = int(chunk)
            except ValueError:
                raise PDFToolError(f"Invalid page number: '{chunk}'")
            if page_num < 1 or page_num > num_pages:
                raise PDFToolError(
                    f"Page {page_num} is out of bounds for a {num_pages}-page document."
                )
            pages.add(page_num - 1)

    return sorted(pages)


def split_pdf_by_ranges(path: Path, range_str: str, password: str | None = None) -> bytes:
    """Extract the given page range(s) into a single new PDF."""
    reader = _open_reader(path, password)
    page_indices = parse_page_ranges(range_str, len(reader.pages))

    writer = PdfWriter()
    for idx in page_indices:
        writer.add_page(reader.pages[idx])

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def split_pdf_to_pages(path: Path, password: str | None = None) -> dict[str, bytes]:
    """Split every page of a PDF into its own single-page PDF file.

    Returns a dict of {filename: pdf_bytes} suitable for zipping.
    """
    reader = _open_reader(path, password)
    stem = Path(path).stem
    outputs: dict[str, bytes] = {}

    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        buffer = io.BytesIO()
        writer.write(buffer)
        outputs[f"{stem}_page_{i:03d}.pdf"] = buffer.getvalue()

    return outputs


# ---------------------------------------------------------------------------
# Rotate
# ---------------------------------------------------------------------------
def rotate_pdf(path: Path, angle: int, password: str | None = None) -> bytes:
    """Rotate every page by `angle` degrees (must be a multiple of 90)."""
    if angle % 90 != 0:
        raise PDFToolError("Rotation angle must be a multiple of 90 degrees.")

    reader = _open_reader(path, password)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Compress
# ---------------------------------------------------------------------------
def compress_pdf(path: Path, image_quality: int = 60, password: str | None = None) -> bytes:
    """Best-effort PDF compression.

    Strategy: recompress embedded raster images to the given JPEG quality
    and strip redundant content-stream data. This is a lossy operation on
    images only — vector content and text remain crisp.
    """
    from PIL import Image

    reader = _open_reader(path, password)
    writer = PdfWriter()

    for page in reader.pages:
        try:
            for img in page.images:
                try:
                    pil_img = Image.open(io.BytesIO(img.data))
                    out = io.BytesIO()
                    fmt = "JPEG" if pil_img.mode in ("RGB", "L") else "PNG"
                    if fmt == "JPEG" and pil_img.mode not in ("RGB", "L"):
                        pil_img = pil_img.convert("RGB")
                    save_kwargs = {"quality": image_quality, "optimize": True} if fmt == "JPEG" else {"optimize": True}
                    pil_img.save(out, format=fmt, **save_kwargs)
                    img.replace(out.getvalue())
                except Exception:
                    # Skip images that can't be safely re-encoded.
                    continue
        except Exception:
            pass

        writer.add_page(page)

    # compress_content_streams requires pages to already belong to a
    # PdfWriter, so this runs as a second pass over the writer's own pages.
    for page in writer.pages:
        try:
            page.compress_content_streams()
        except Exception:
            continue

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Watermark
# ---------------------------------------------------------------------------
def _make_text_watermark_pdf(
    text: str,
    page_width: float,
    page_height: float,
    opacity: float = 0.3,
    font_size: int = 40,
    rotation: int = 45,
) -> PdfReader:
    """Render a single-page PDF containing diagonal, tiled watermark text."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    c.saveState()
    c.setFillColorRGB(0.5, 0.5, 0.5, alpha=opacity)
    c.setFont("Helvetica-Bold", font_size)
    c.translate(page_width / 2, page_height / 2)
    c.rotate(rotation)
    c.drawCentredString(0, 0, text)
    c.restoreState()
    c.save()
    buffer.seek(0)
    return PdfReader(buffer)


def add_watermark(
    path: Path,
    text: str,
    opacity: float = 0.3,
    font_size: int = 40,
    rotation: int = 45,
    password: str | None = None,
) -> bytes:
    """Stamp a diagonal text watermark onto every page of a PDF."""
    if not text.strip():
        raise PDFToolError("Watermark text cannot be empty.")

    reader = _open_reader(path, password)
    writer = PdfWriter()

    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        watermark_reader = _make_text_watermark_pdf(
            text, width, height, opacity=opacity, font_size=font_size, rotation=rotation
        )
        page.merge_page(watermark_reader.pages[0])
        writer.add_page(page)

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Security: protect / unlock
# ---------------------------------------------------------------------------
def protect_pdf(path: Path, user_password: str, owner_password: str | None = None) -> bytes:
    """Encrypt a PDF with a user (open) password, using AES-256 where supported."""
    if not user_password:
        raise PDFToolError("Please provide a password to protect the file.")

    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise PDFToolError("This PDF is already encrypted.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    writer.encrypt(
        user_password=user_password,
        owner_password=owner_password or user_password,
        algorithm="AES-256",
    )

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def unlock_pdf(path: Path, password: str) -> bytes:
    """Remove password protection from a PDF, given the correct password."""
    reader = PdfReader(str(path))
    if not reader.is_encrypted:
        raise PDFToolError("This PDF is not password protected.")

    result = reader.decrypt(password)
    if result == 0:
        raise PDFToolError("Incorrect password.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------
def extract_text(path: Path, password: str | None = None) -> dict[int, str]:
    """Extract embedded (non-OCR) text per page. Empty pages likely mean
    the PDF is a scanned image and should go through the OCR module instead.
    """
    reader = _open_reader(path, password)
    return {i + 1: (page.extract_text() or "") for i, page in enumerate(reader.pages)}


def pdf_pages_to_images(path: Path, dpi: int = 200, password: str | None = None):
    """Rasterize each PDF page to a PIL Image, for previews or OCR input.

    Uses pdf2image (poppler) rather than a PDF-native renderer so this
    works purely from image bytes for pages with no extractable text.
    """
    from pdf2image import convert_from_path

    try:
        return convert_from_path(str(path), dpi=dpi, userpw=password)
    except Exception as exc:
        raise PDFToolError(f"Could not render PDF pages to images: {exc}") from exc
