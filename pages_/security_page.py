"""
pages_/security_page.py
-------------------------
Security page: PDF password protect/unlock, plus generic file
encryption/decryption for any file type.
"""

from __future__ import annotations

import streamlit as st

from modules import pdf_tools, security_tools
from modules.pdf_tools import PDFToolError
from modules.security_tools import SecurityToolError
from utils.file_utils import cleanup_dir, new_session_dir, save_uploaded_file
from utils.ui_utils import empty_state, info_card, page_header


def render() -> None:
    page_header("Security", "Password-protect or unlock PDFs, or encrypt any file for safe sharing.", "🔒")

    tabs = st.tabs(["🔐 Protect PDF", "🔓 Unlock PDF", "🗝️ Encrypt Any File", "🔑 Decrypt File"])

    with tabs[0]:
        _render_protect_pdf()
    with tabs[1]:
        _render_unlock_pdf()
    with tabs[2]:
        _render_encrypt_file()
    with tabs[3]:
        _render_decrypt_file()


def _password_strength_widget(password: str) -> None:
    if not password:
        return
    label, score = security_tools.password_strength(password)
    color = {"Weak": "red", "Fair": "orange", "Strong": "blue", "Very strong": "green"}.get(label, "gray")
    st.progress(score / 100)
    st.markdown(f"Password strength: :{color}[**{label}**]")


# ---------------------------------------------------------------------------
def _render_protect_pdf() -> None:
    info_card("How it works", "Encrypt a PDF with a password so it can only be opened by someone who knows it (AES-256).")
    file = st.file_uploader("Upload a PDF to protect", type=["pdf"], key="protect_upl")
    if not file:
        empty_state("Upload a PDF to add a password.")
        return

    password = st.text_input("Set a password", type="password", key="protect_pw")
    _password_strength_widget(password)
    confirm = st.text_input("Confirm password", type="password", key="protect_pw_confirm")

    if st.button("Protect PDF", type="primary", key="protect_btn"):
        if not password:
            st.error("Please enter a password.")
            return
        if password != confirm:
            st.error("Passwords do not match.")
            return

        session_dir = new_session_dir()
        try:
            path = save_uploaded_file(file, session_dir)
            with st.spinner("Encrypting..."):
                result_bytes = pdf_tools.protect_pdf(path, password)
            st.success("PDF is now password protected.")
            st.download_button(
                "⬇️ Download protected.pdf", data=result_bytes, file_name=f"{path.stem}_protected.pdf",
                mime="application/pdf", type="primary",
            )
        except PDFToolError as exc:
            st.error(str(exc))
        finally:
            cleanup_dir(session_dir)


# ---------------------------------------------------------------------------
def _render_unlock_pdf() -> None:
    info_card("How it works", "Remove password protection from a PDF you already know the password for.")
    file = st.file_uploader("Upload a protected PDF", type=["pdf"], key="unlock_upl")
    if not file:
        empty_state("Upload a password-protected PDF.")
        return

    password = st.text_input("Current password", type="password", key="unlock_pw")

    if st.button("Unlock PDF", type="primary", key="unlock_btn"):
        if not password:
            st.error("Please enter the current password.")
            return

        session_dir = new_session_dir()
        try:
            path = save_uploaded_file(file, session_dir)
            with st.spinner("Decrypting..."):
                result_bytes = pdf_tools.unlock_pdf(path, password)
            st.success("Password protection removed.")
            st.download_button(
                "⬇️ Download unlocked.pdf", data=result_bytes, file_name=f"{path.stem}_unlocked.pdf",
                mime="application/pdf", type="primary",
            )
        except PDFToolError as exc:
            st.error(str(exc))
        finally:
            cleanup_dir(session_dir)


# ---------------------------------------------------------------------------
def _render_encrypt_file() -> None:
    info_card(
        "How it works",
        "Encrypts any file type (not just PDFs) with a password-derived key, producing a .sftenc file "
        "that can only be opened using this app and the correct password.",
    )
    file = st.file_uploader("Upload a file to encrypt", key="enc_upl")
    if not file:
        empty_state("Upload any file to encrypt it.")
        return

    password = st.text_input("Set a password", type="password", key="enc_pw")
    _password_strength_widget(password)

    if st.button("Encrypt File", type="primary", key="enc_btn"):
        if not password:
            st.error("Please enter a password.")
            return
        try:
            with st.spinner("Encrypting..."):
                result_bytes = security_tools.encrypt_file_bytes(file.getvalue(), password)
            st.success("File encrypted.")
            st.download_button(
                "⬇️ Download encrypted file", data=result_bytes, file_name=f"{file.name}.sftenc",
                mime="application/octet-stream", type="primary",
            )
        except SecurityToolError as exc:
            st.error(str(exc))


# ---------------------------------------------------------------------------
def _render_decrypt_file() -> None:
    info_card("How it works", "Decrypt a .sftenc file previously created with the Encrypt Any File tool.")
    file = st.file_uploader("Upload a .sftenc file", type=["sftenc"], key="dec_upl")
    if not file:
        empty_state("Upload a .sftenc file to decrypt.")
        return

    password = st.text_input("Password", type="password", key="dec_pw")

    if st.button("Decrypt File", type="primary", key="dec_btn"):
        if not password:
            st.error("Please enter the password.")
            return
        try:
            with st.spinner("Decrypting..."):
                result_bytes = security_tools.decrypt_file_bytes(file.getvalue(), password)
            original_name = file.name[:-len(".sftenc")] if file.name.endswith(".sftenc") else f"decrypted_{file.name}"
            st.success("File decrypted.")
            st.download_button(
                "⬇️ Download decrypted file", data=result_bytes, file_name=original_name,
                mime="application/octet-stream", type="primary",
            )
        except SecurityToolError as exc:
            st.error(str(exc))
