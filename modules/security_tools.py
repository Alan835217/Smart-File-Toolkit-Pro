"""
modules/security_tools.py
--------------------------
Security-focused utilities that sit above modules.pdf_tools:
- Password strength scoring (simple heuristic, no external dependency)
- Batch protect/unlock across multiple PDFs
- Generic symmetric file encryption/decryption for non-PDF files, so a
  user can secure any document type (not just PDFs) before sharing it.

The generic encryption uses PBKDF2-derived AES-like stream cipher built
from Python's hashlib + hmac only, avoiding a hard dependency on
`cryptography`, which may not be present in every environment. For
production use, swapping in `cryptography`'s Fernet is recommended and
noted below.
"""

from __future__ import annotations

import hashlib
import hmac
import io
import os
from pathlib import Path

from modules import pdf_tools
from modules.pdf_tools import PDFToolError  # re-exported for callers


class SecurityToolError(Exception):
    """Raised for any user-facing security-tool failure."""


# ---------------------------------------------------------------------------
# Password strength
# ---------------------------------------------------------------------------
def password_strength(password: str) -> tuple[str, int]:
    """Return (label, score 0-100) using a simple, dependency-free heuristic.

    This is intentionally conservative UI guidance, not a formal entropy
    calculation — good enough to nudge users away from weak passwords.
    """
    if not password:
        return "Empty", 0

    score = 0
    score += min(len(password), 16) * 4          # length, capped
    score += 10 if any(c.islower() for c in password) else 0
    score += 10 if any(c.isupper() for c in password) else 0
    score += 10 if any(c.isdigit() for c in password) else 0
    score += 15 if any(not c.isalnum() for c in password) else 0
    score = min(score, 100)

    if score < 30:
        label = "Weak"
    elif score < 60:
        label = "Fair"
    elif score < 85:
        label = "Strong"
    else:
        label = "Very strong"

    return label, score


# ---------------------------------------------------------------------------
# Batch PDF protect / unlock
# ---------------------------------------------------------------------------
def batch_protect_pdfs(paths: list[Path], password: str) -> tuple[dict[str, bytes], list[str]]:
    """Protect several PDFs with the same password. Returns
    {filename: pdf_bytes}; failures are collected and re-raised together
    so the caller can report exactly which files failed and why.
    """
    outputs: dict[str, bytes] = {}
    errors: list[str] = []

    for path in paths:
        try:
            outputs[f"{Path(path).stem}_protected.pdf"] = pdf_tools.protect_pdf(path, password)
        except PDFToolError as exc:
            errors.append(f"{Path(path).name}: {exc}")

    if errors and not outputs:
        raise SecurityToolError("All files failed:\n" + "\n".join(errors))
    return outputs, errors


def batch_unlock_pdfs(paths: list[Path], password: str) -> tuple[dict[str, bytes], list[str]]:
    outputs: dict[str, bytes] = {}
    errors: list[str] = []

    for path in paths:
        try:
            outputs[f"{Path(path).stem}_unlocked.pdf"] = pdf_tools.unlock_pdf(path, password)
        except PDFToolError as exc:
            errors.append(f"{Path(path).name}: {exc}")

    if errors and not outputs:
        raise SecurityToolError("All files failed:\n" + "\n".join(errors))
    return outputs, errors


# ---------------------------------------------------------------------------
# Generic file encryption (any file type) — lightweight, dependency-free
# ---------------------------------------------------------------------------
_SALT_LEN = 16
_KEY_LEN = 32
_PBKDF2_ITERATIONS = 200_000
_MAGIC = b"SFTP1"  # format marker so decrypt() can validate the file


def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS, dklen=_KEY_LEN)


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    """Generate a keystream via HMAC-SHA256 counter mode (a simple,
    dependency-free stream cipher). Suitable for casual document
    protection; swap in `cryptography`'s Fernet/AES-GCM for
    production-grade guarantees.
    """
    blocks = []
    counter = 0
    produced = 0
    while produced < length:
        block = hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
        blocks.append(block)
        produced += len(block)
        counter += 1
    return b"".join(blocks)[:length]


def encrypt_file_bytes(data: bytes, password: str) -> bytes:
    """Encrypt arbitrary file bytes with a password. Output layout:
    MAGIC (5B) | salt (16B) | nonce (16B) | hmac_tag (32B) | ciphertext
    """
    if not password:
        raise SecurityToolError("A password is required to encrypt this file.")

    salt = os.urandom(_SALT_LEN)
    nonce = os.urandom(16)
    key = _derive_key(password, salt)
    stream = _keystream(key, nonce, len(data))
    ciphertext = bytes(a ^ b for a, b in zip(data, stream))
    tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()

    return _MAGIC + salt + nonce + tag + ciphertext


def decrypt_file_bytes(blob: bytes, password: str) -> bytes:
    if not blob.startswith(_MAGIC):
        raise SecurityToolError("This file was not encrypted with Smart File Toolkit Pro.")

    offset = len(_MAGIC)
    salt = blob[offset: offset + _SALT_LEN]; offset += _SALT_LEN
    nonce = blob[offset: offset + 16]; offset += 16
    tag = blob[offset: offset + 32]; offset += 32
    ciphertext = blob[offset:]

    key = _derive_key(password, salt)
    expected_tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected_tag):
        raise SecurityToolError("Incorrect password or corrupted file.")

    stream = _keystream(key, nonce, len(ciphertext))
    return bytes(a ^ b for a, b in zip(ciphertext, stream))
