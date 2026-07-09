"""
modules/image_tools.py
-----------------------
Pure image-processing logic: format conversion, compression, resizing,
rotation/flipping, filters, and cropping. Built on Pillow for I/O and
straightforward transforms, and OpenCV for filters that are awkward or
slow to express in pure Pillow (denoising, sharpening, edge detection).

Every function accepts and returns bytes or PIL Images so it stays fully
decoupled from Streamlit and is easy to reuse or test standalone.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from config import DEFAULT_IMAGE_MAX_DIM


class ImageToolError(Exception):
    """Raised for any user-facing image processing failure."""


@dataclass
class ImageInfo:
    width: int
    height: int
    format: str
    mode: str
    size_bytes: int


# ---------------------------------------------------------------------------
# Loading / inspection
# ---------------------------------------------------------------------------
def load_image(data: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        return img
    except Exception as exc:
        raise ImageToolError(f"Could not read image: {exc}") from exc


def get_image_info(data: bytes) -> ImageInfo:
    img = load_image(data)
    return ImageInfo(
        width=img.width,
        height=img.height,
        format=img.format or "UNKNOWN",
        mode=img.mode,
        size_bytes=len(data),
    )


def image_to_bytes(img: Image.Image, fmt: str = "PNG", quality: int = 90) -> bytes:
    """Serialize a PIL image back to bytes in the requested format."""
    fmt = fmt.upper().replace("JPG", "JPEG")
    buffer = io.BytesIO()

    save_kwargs = {}
    if fmt == "JPEG":
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        save_kwargs = {"quality": quality, "optimize": True}
    elif fmt == "WEBP":
        save_kwargs = {"quality": quality}
    elif fmt == "PNG":
        save_kwargs = {"optimize": True}

    img.save(buffer, format=fmt, **save_kwargs)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Format conversion
# ---------------------------------------------------------------------------
def convert_format(data: bytes, target_format: str, quality: int = 90) -> bytes:
    img = load_image(data)
    return image_to_bytes(img, fmt=target_format, quality=quality)


# ---------------------------------------------------------------------------
# Compression / resizing
# ---------------------------------------------------------------------------
def compress_image(data: bytes, quality: int = 70, target_format: str | None = None) -> bytes:
    """Re-encode an image at a lower quality to shrink file size.

    If target_format is omitted, the original format is kept (falls back
    to JPEG for formats without a meaningful quality parameter, e.g. BMP).
    """
    img = load_image(data)
    fmt = (target_format or img.format or "JPEG").upper()
    if fmt not in ("JPEG", "JPG", "WEBP", "PNG"):
        fmt = "JPEG"
    return image_to_bytes(img, fmt=fmt, quality=quality)


def resize_image(
    data: bytes,
    width: int | None = None,
    height: int | None = None,
    maintain_aspect: bool = True,
    target_format: str | None = None,
    quality: int = 90,
) -> bytes:
    img = load_image(data)

    if not width and not height:
        raise ImageToolError("Provide at least a target width or height.")

    orig_w, orig_h = img.size
    if maintain_aspect:
        if width and not height:
            height = round(orig_h * (width / orig_w))
        elif height and not width:
            width = round(orig_w * (height / orig_h))
        else:
            # Both given: fit within the box, preserving aspect ratio.
            ratio = min(width / orig_w, height / orig_h)
            width, height = round(orig_w * ratio), round(orig_h * ratio)

    width = max(1, min(width or orig_w, DEFAULT_IMAGE_MAX_DIM))
    height = max(1, min(height or orig_h, DEFAULT_IMAGE_MAX_DIM))

    resized = img.resize((width, height), Image.LANCZOS)
    return image_to_bytes(resized, fmt=target_format or img.format or "PNG", quality=quality)


def resize_by_percentage(data: bytes, percent: float, target_format: str | None = None, quality: int = 90) -> bytes:
    img = load_image(data)
    w, h = img.size
    new_w = max(1, round(w * percent / 100))
    new_h = max(1, round(h * percent / 100))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    return image_to_bytes(resized, fmt=target_format or img.format or "PNG", quality=quality)


# ---------------------------------------------------------------------------
# Rotate / flip / crop
# ---------------------------------------------------------------------------
def rotate_image(data: bytes, angle: float, expand: bool = True) -> bytes:
    img = load_image(data)
    rotated = img.rotate(-angle, expand=expand, fillcolor=(255, 255, 255) if img.mode == "RGB" else None)
    return image_to_bytes(rotated, fmt=img.format or "PNG")


def flip_image(data: bytes, direction: str) -> bytes:
    img = load_image(data)
    if direction == "horizontal":
        flipped = ImageOps.mirror(img)
    elif direction == "vertical":
        flipped = ImageOps.flip(img)
    else:
        raise ImageToolError("Direction must be 'horizontal' or 'vertical'.")
    return image_to_bytes(flipped, fmt=img.format or "PNG")


def crop_image(data: bytes, left: int, top: int, right: int, bottom: int) -> bytes:
    img = load_image(data)
    w, h = img.size
    left, top = max(0, left), max(0, top)
    right, bottom = min(w, right), min(h, bottom)
    if left >= right or top >= bottom:
        raise ImageToolError("Invalid crop box.")
    cropped = img.crop((left, top, right, bottom))
    return image_to_bytes(cropped, fmt=img.format or "PNG")


# ---------------------------------------------------------------------------
# Enhancements & filters
# ---------------------------------------------------------------------------
def adjust_enhancements(
    data: bytes,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sharpness: float = 1.0,
) -> bytes:
    """Apply Pillow enhancement factors; 1.0 means "no change" for each."""
    img = load_image(data)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Color(img).enhance(saturation)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)
    return image_to_bytes(img, fmt=img.format or "PNG")


def to_grayscale(data: bytes) -> bytes:
    img = load_image(data)
    gray = ImageOps.grayscale(img)
    return image_to_bytes(gray, fmt=img.format or "PNG")


def apply_blur(data: bytes, radius: float = 2.0) -> bytes:
    img = load_image(data)
    blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
    return image_to_bytes(blurred, fmt=img.format or "PNG")


def apply_sharpen(data: bytes) -> bytes:
    """Unsharp-mask style sharpening via OpenCV for a crisper result."""
    img = load_image(data).convert("RGB")
    arr = np.array(img)
    blurred = cv2.GaussianBlur(arr, (0, 0), sigmaX=3)
    sharpened = cv2.addWeighted(arr, 1.5, blurred, -0.5, 0)
    out_img = Image.fromarray(sharpened)
    return image_to_bytes(out_img, fmt="PNG")


def apply_edge_detection(data: bytes) -> bytes:
    img = load_image(data).convert("RGB")
    arr = np.array(img)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    out_img = Image.fromarray(edges)
    return image_to_bytes(out_img, fmt="PNG")


def denoise_image(data: bytes) -> bytes:
    img = load_image(data).convert("RGB")
    arr = np.array(img)
    denoised = cv2.fastNlMeansDenoisingColored(arr, None, 8, 8, 7, 21)
    out_img = Image.fromarray(denoised)
    return image_to_bytes(out_img, fmt="PNG")


def remove_background_naive(data: bytes, threshold: int = 240) -> bytes:
    """Lightweight, non-ML background removal: turns near-white pixels
    transparent. Works well for scanned documents / flat product shots
    on a white background; not a substitute for an ML matting model.
    """
    img = load_image(data).convert("RGBA")
    arr = np.array(img)
    mask = (arr[:, :, 0] > threshold) & (arr[:, :, 1] > threshold) & (arr[:, :, 2] > threshold)
    arr[:, :, 3] = np.where(mask, 0, 255)
    out_img = Image.fromarray(arr, mode="RGBA")
    return image_to_bytes(out_img, fmt="PNG")
