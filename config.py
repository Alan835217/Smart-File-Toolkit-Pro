"""
config.py
---------
Centralized configuration and constants for Smart File Toolkit Pro.
Keeping these values in one place makes the app easy to re-theme,
re-brand, or reconfigure without touching business logic.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------------
APP_NAME = "Smart File Toolkit Pro"
APP_TAGLINE = "Your all-in-one workspace for PDFs, images, and OCR."
APP_ICON = "🗂️"
APP_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Filesystem
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
ASSETS_DIR = BASE_DIR / "assets"
STYLE_SHEET = ASSETS_DIR / "style.css"

TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Limits / defaults
# ---------------------------------------------------------------------------
MAX_UPLOAD_MB = 200                     # soft guidance shown in UI
DEFAULT_JPEG_QUALITY = 80
DEFAULT_IMAGE_MAX_DIM = 4096             # px, safety cap for resize operations
SUPPORTED_IMAGE_FORMATS = ["PNG", "JPEG", "JPG", "WEBP", "BMP", "TIFF"]
SUPPORTED_OCR_LANGS = {
    "English": "eng",
    "Hindi": "hin",
    "French": "fra",
    "German": "deu",
    "Spanish": "spa",
}

# ---------------------------------------------------------------------------
# Navigation — single source of truth for the sidebar menu.
# Each entry maps a page key to display label + icon; app.py uses this
# to build the sidebar and dispatch to the right render function.
# ---------------------------------------------------------------------------
NAV_ITEMS = [
    {"key": "home", "label": "Home", "icon": "🏠"},
    {"key": "pdf", "label": "PDF Tools", "icon": "📄"},
    {"key": "image", "label": "Image Tools", "icon": "🖼️"},
    {"key": "ocr", "label": "OCR / Text Extraction", "icon": "🔎"},
    {"key": "security", "label": "Security", "icon": "🔒"},
    {"key": "batch", "label": "Batch Processing", "icon": "📦"},
    {"key": "about", "label": "About", "icon": "ℹ️"},
]
