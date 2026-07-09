"""
utils/file_utils.py
--------------------
Low-level filesystem helpers shared across every module: writing uploaded
files to a scratch directory, bundling multiple outputs into a single zip
for download, human-readable formatting, and cleanup.

Keeping this logic out of the Streamlit pages means the same functions can
be unit-tested without spinning up a Streamlit runtime.
"""

from __future__ import annotations

import io
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Iterable, Union

from config import TEMP_DIR

BytesLike = Union[bytes, bytearray, io.BytesIO]


def new_session_dir() -> Path:
    """Create a fresh, uniquely named scratch directory under TEMP_DIR.

    Each user "job" (e.g. one merge operation) gets its own folder so
    concurrent users / operations never collide or overwrite each other.
    """
    session_dir = TEMP_DIR / uuid.uuid4().hex
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def save_uploaded_file(uploaded_file, destination_dir: Path) -> Path:
    """Persist a Streamlit UploadedFile object to disk and return its path."""
    destination_dir.mkdir(parents=True, exist_ok=True)
    out_path = destination_dir / uploaded_file.name
    with open(out_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return out_path


def save_uploaded_files(uploaded_files: Iterable, destination_dir: Path) -> list[Path]:
    """Persist several UploadedFile objects, preserving upload order."""
    return [save_uploaded_file(uf, destination_dir) for uf in uploaded_files]


def bytes_to_zip(named_bytes: dict[str, bytes]) -> bytes:
    """Pack a {filename: file_bytes} mapping into an in-memory zip file.

    Returns the raw zip bytes, ready to hand to st.download_button.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, data in named_bytes.items():
            zf.writestr(filename, data)
    buffer.seek(0)
    return buffer.getvalue()


def files_to_zip(paths: Iterable[Path], arcnames: Iterable[str] | None = None) -> bytes:
    """Pack files already on disk into an in-memory zip file."""
    paths = list(paths)
    arcnames = list(arcnames) if arcnames is not None else [p.name for p in paths]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, arcname in zip(paths, arcnames):
            zf.write(path, arcname=arcname)
    buffer.seek(0)
    return buffer.getvalue()


def human_readable_size(num_bytes: float) -> str:
    """Convert a byte count into a friendly string, e.g. '3.2 MB'."""
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024.0:
            return f"{num_bytes:,.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:,.1f} TB"


def cleanup_dir(path: Path) -> None:
    """Best-effort recursive delete of a scratch directory. Never raises."""
    try:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


def unique_output_path(directory: Path, filename: str) -> Path:
    """Return a path guaranteed not to collide with an existing file.

    Appends '(1)', '(2)', ... to the stem if needed, mirroring the
    behavior most desktop file managers use.
    """
    directory.mkdir(parents=True, exist_ok=True)
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    stem, suffix = Path(filename).stem, Path(filename).suffix
    counter = 1
    while True:
        candidate = directory / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
