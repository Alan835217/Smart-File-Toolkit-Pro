# 🗂️ Smart File Toolkit Pro

A modern, all-in-one document and image processing platform built with
Python and Streamlit. Merge, split, compress, watermark, and secure
PDFs; convert, resize, and filter images; extract text with OCR — all
from a single app, without uploading your files to third-party sites.

## ✨ Features

| Category | Tools |
|---|---|
| **PDF** | Merge, split (by range or into single pages), rotate, compress, watermark, extract text |
| **Image** | Convert format (PNG/JPEG/WEBP/BMP/TIFF), compress, resize/crop, rotate/flip, filters (blur, sharpen, edge detection, denoise, grayscale), enhancements (brightness/contrast/saturation/sharpness), naive background removal |
| **OCR** | Extract text from images and scanned PDFs (Tesseract, multi-language) |
| **Security** | Password-protect/unlock PDFs (AES-256), encrypt/decrypt any file type |
| **Batch** | Run any of the above operations across many files at once, download as a single zip |

## 🏗️ Architecture

```
smart_file_toolkit/
├── app.py                 # Entry point: page config + sidebar routing only
├── config.py               # Constants, limits, navigation config
├── requirements.txt
├── modules/                 # Pure business logic (no Streamlit imports)
│   ├── pdf_tools.py          # merge/split/rotate/compress/watermark/protect/extract
│   ├── image_tools.py        # convert/resize/crop/rotate/filters/enhance
│   ├── ocr_tools.py          # Tesseract OCR for images & scanned PDFs
│   └── security_tools.py     # password strength, batch protect, generic file encryption
├── pages_/                  # One file per feature page (UI + orchestration only)
│   ├── home.py
│   ├── pdf_page.py
│   ├── image_page.py
│   ├── ocr_page.py
│   ├── security_page.py
│   ├── batch_page.py
│   └── about_page.py
├── utils/
│   ├── file_utils.py         # temp dirs, zipping, human-readable sizes
│   └── ui_utils.py           # shared Streamlit UI components
└── assets/
    └── style.css              # custom theme
```

This is a **service-oriented, modular architecture**: `modules/` contains
zero Streamlit imports, so the same logic could power a CLI or a REST API
in the future. New tools can be added by dropping in a new module +
page without touching existing code.

## 🚀 Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install system dependencies

These are required by `pytesseract` (OCR) and `pdf2image` (PDF rendering)
and are **not** installed via pip:

**Tesseract OCR**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows: https://github.com/UB-Mannheim/tesseract/wiki
```

**Poppler** (for `pdf2image`)
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler

# Windows: https://github.com/oschwartz10612/poppler-windows
```

To OCR languages other than English, install the matching Tesseract
language pack, e.g. `sudo apt-get install tesseract-ocr-hin` for Hindi.

### 3. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## 🔒 Privacy

Uploaded files are written to a per-operation temp folder for processing
and deleted immediately after each operation completes — nothing is sent
to a third-party server. Once installed, the app runs entirely on your
own machine.

## 🗺️ Roadmap

- User accounts (SQLAlchemy + SQLite + bcrypt) for saved history/preferences
- ML-based background removal
- Digital signatures for PDFs
- Drag-and-drop page reordering
- Dark mode

## 📄 License

MIT — use it, extend it, ship it.
