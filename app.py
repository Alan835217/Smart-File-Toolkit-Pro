
from __future__ import annotations

import streamlit as st

from config import APP_ICON, APP_NAME, APP_TAGLINE, APP_VERSION, NAV_ITEMS
from utils.ui_utils import configure_page, inject_custom_css

from pages_ import home, pdf_page, image_page, ocr_page, security_page, batch_page, about_page


PAGE_RENDERERS = {
    "home": home.render,
    "pdf": pdf_page.render,
    "image": image_page.render,
    "ocr": ocr_page.render,
    "security": security_page.render,
    "batch": batch_page.render,
    "about": about_page.render,
}


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            f"<div class='sft-brand'>{APP_ICON} {APP_NAME}</div>"
            f"<div class='sft-brand-sub'>v{APP_VERSION} · {APP_TAGLINE}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        labels = [f"{item['icon']}  {item['label']}" for item in NAV_ITEMS]
        keys = [item["key"] for item in NAV_ITEMS]

        if "nav_key" not in st.session_state:
            st.session_state["nav_key"] = "home"

        default_index = keys.index(st.session_state["nav_key"]) if st.session_state["nav_key"] in keys else 0
        choice_label = st.radio("Navigate", labels, index=default_index, label_visibility="collapsed")
        selected_key = keys[labels.index(choice_label)]
        st.session_state["nav_key"] = selected_key

        st.markdown("---")
        st.caption("🔒 Files are processed in-memory for this session and are not uploaded to any third party.")

    return selected_key


def main() -> None:
    configure_page()
    inject_custom_css()

    page_key = render_sidebar()
    renderer = PAGE_RENDERERS.get(page_key, home.render)
    renderer()


if __name__ == "__main__":
    main()
