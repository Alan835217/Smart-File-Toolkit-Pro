"""
utils/ui_utils.py
------------------
Reusable Streamlit UI building blocks: page configuration, CSS injection,
page headers, and small presentational widgets. Centralizing these keeps
every module's page visually consistent without copy-pasted markup.
"""

from __future__ import annotations

import streamlit as st

from config import APP_ICON, APP_NAME, STYLE_SHEET


def configure_page(page_title: str | None = None) -> None:
    """Set Streamlit page config. Must be the first Streamlit call made."""
    st.set_page_config(
        page_title=page_title or APP_NAME,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_custom_css() -> None:
    """Load and inject the shared stylesheet, if present."""
    if STYLE_SHEET.exists():
        st.markdown(f"<style>{STYLE_SHEET.read_text()}</style>", unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    """Render a consistent large page title + subtitle block."""
    st.markdown(
        f"""
        <div class="sft-page-header">
            <div class="sft-page-title">{icon} {title}</div>
            <div class="sft-page-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_divider() -> None:
    st.markdown("<hr class='sft-divider'/>", unsafe_allow_html=True)


def info_card(title: str, body: str, icon: str = "💡") -> None:
    """A soft, rounded info callout used for tips/help text."""
    st.markdown(
        f"""
        <div class="sft-card">
            <div class="sft-card-title">{icon} {title}</div>
            <div class="sft-card-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def result_metric_row(metrics: dict[str, str]) -> None:
    """Render a row of st.metric-like KPIs, e.g. before/after file size."""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label, value)


def empty_state(message: str = "Upload a file above to get started.") -> None:
    st.markdown(
        f"<div class='sft-empty-state'>📂 {message}</div>",
        unsafe_allow_html=True,
    )


def tool_grid_card(icon: str, title: str, description: str) -> str:
    """Return HTML markup for one card in the home page tool grid."""
    return f"""
        <div class="sft-tool-card">
            <div class="sft-tool-icon">{icon}</div>
            <div class="sft-tool-title">{title}</div>
            <div class="sft-tool-desc">{description}</div>
        </div>
    """
