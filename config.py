
from pathlib import Path

APP_NAME = "Smart File Toolkit Pro"
APP_TAGLINE = "Your all-in-one workspace for PDFs, images, and OCR."
APP_ICON = "🗂️"
APP_VERSION = "1.0.0"

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
ASSETS_DIR = BASE_DIR / "assets"
STYLE_SHEET = ASSETS_DIR / "style.css"

TEMP_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_MB = 200                     
DEFAULT_JPEG_QUALITY = 80
DEFAULT_IMAGE_MAX_DIM = 4096            
SUPPORTED_IMAGE_FORMATS = ["PNG", "JPEG", "JPG", "WEBP", "BMP", "TIFF"]
SUPPORTED_OCR_LANGS = {
    "English": "eng",
    "Hindi": "hin",
    "French": "fra",
    "German": "deu",
    "Spanish": "spa",
}

NAV_ITEMS = [
    {"key": "home", "label": "Home", "icon": "🏠"},
    {"key": "pdf", "label": "PDF Tools", "icon": "📄"},
    {"key": "image", "label": "Image Tools", "icon": "🖼️"},
    {"key": "ocr", "label": "OCR / Text Extraction", "icon": "🔎"},
    {"key": "security", "label": "Security", "icon": "🔒"},
    {"key": "batch", "label": "Batch Processing", "icon": "📦"},
    {"key": "about", "label": "About", "icon": "ℹ️"},
]
