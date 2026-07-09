"""
pages_/image_page.py
----------------------
Image Tools page: format conversion, compression, resizing, rotate/flip/
crop, and filters/enhancements — each in its own tab.
"""

from __future__ import annotations

import streamlit as st

from modules import image_tools
from modules.image_tools import ImageToolError
from utils.file_utils import human_readable_size
from utils.ui_utils import empty_state, info_card, page_header, result_metric_row


def _preview_and_download(original_bytes: bytes, result_bytes: bytes, filename: str, mime: str) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Original")
        st.image(original_bytes, use_container_width=True)
    with col2:
        st.caption("Result")
        st.image(result_bytes, use_container_width=True)

    result_metric_row({
        "Original size": human_readable_size(len(original_bytes)),
        "New size": human_readable_size(len(result_bytes)),
    })
    st.download_button("⬇️ Download result", data=result_bytes, file_name=filename, mime=mime, type="primary")


def render() -> None:
    page_header("Image Tools", "Convert formats, compress, resize, crop, rotate, and apply filters.", "🖼️")

    tabs = st.tabs(["🔄 Convert & Compress", "📐 Resize & Crop", "🔃 Rotate & Flip", "🎨 Filters & Enhance", "✂️ Background"])

    with tabs[0]:
        _render_convert_compress()
    with tabs[1]:
        _render_resize_crop()
    with tabs[2]:
        _render_rotate_flip()
    with tabs[3]:
        _render_filters()
    with tabs[4]:
        _render_background()


def _uploader(key: str, label: str = "Upload an image"):
    return st.file_uploader(label, type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"], key=key)


# ---------------------------------------------------------------------------
def _render_convert_compress() -> None:
    info_card("How it works", "Convert between formats and/or reduce quality to shrink file size.")
    file = _uploader("convert_upl")
    if not file:
        empty_state("Upload an image to convert or compress.")
        return

    data = file.getvalue()
    try:
        info = image_tools.get_image_info(data)
    except ImageToolError as exc:
        st.error(str(exc))
        return

    st.caption(f"{info.width}×{info.height}px · {info.format} · {human_readable_size(info.size_bytes)}")

    col1, col2 = st.columns(2)
    with col1:
        target_format = st.selectbox("Convert to format", ["PNG", "JPEG", "WEBP", "BMP", "TIFF"], key="conv_fmt")
    with col2:
        quality = st.slider("Quality (JPEG/WEBP only)", 10, 100, 85, key="conv_quality")

    if st.button("Convert / Compress", type="primary", key="conv_btn"):
        try:
            result = image_tools.convert_format(data, target_format, quality=quality)
            stem = file.name.rsplit(".", 1)[0]
            ext = target_format.lower().replace("jpeg", "jpg")
            _preview_and_download(data, result, f"{stem}.{ext}", f"image/{target_format.lower()}")
        except ImageToolError as exc:
            st.error(str(exc))


# ---------------------------------------------------------------------------
def _render_resize_crop() -> None:
    info_card("How it works", "Resize by exact dimensions or percentage, or crop to a specific box.")
    file = _uploader("resize_upl")
    if not file:
        empty_state("Upload an image to resize or crop.")
        return

    data = file.getvalue()
    info = image_tools.get_image_info(data)
    st.caption(f"Original: {info.width}×{info.height}px")

    mode = st.radio("Mode", ["Resize by dimensions", "Resize by percentage", "Crop"], horizontal=True, key="resize_mode")

    try:
        if mode == "Resize by dimensions":
            col1, col2, col3 = st.columns(3)
            with col1:
                width = st.number_input("Width (px)", min_value=0, value=info.width, key="rw")
            with col2:
                height = st.number_input("Height (px)", min_value=0, value=info.height, key="rh")
            with col3:
                maintain = st.checkbox("Maintain aspect ratio", value=True, key="rmaintain")

            if st.button("Resize", type="primary", key="resize_btn"):
                result = image_tools.resize_image(data, width=int(width) or None, height=int(height) or None, maintain_aspect=maintain)
                _preview_and_download(data, result, f"{file.name.rsplit('.',1)[0]}_resized.png", "image/png")

        elif mode == "Resize by percentage":
            pct = st.slider("Scale (%)", 5, 200, 50, key="rpct")
            if st.button("Resize", type="primary", key="resize_pct_btn"):
                result = image_tools.resize_by_percentage(data, pct)
                _preview_and_download(data, result, f"{file.name.rsplit('.',1)[0]}_resized.png", "image/png")

        else:
            col1, col2 = st.columns(2)
            with col1:
                left = st.number_input("Left", min_value=0, max_value=info.width, value=0, key="cleft")
                top = st.number_input("Top", min_value=0, max_value=info.height, value=0, key="ctop")
            with col2:
                right = st.number_input("Right", min_value=0, max_value=info.width, value=info.width, key="cright")
                bottom = st.number_input("Bottom", min_value=0, max_value=info.height, value=info.height, key="cbottom")

            if st.button("Crop", type="primary", key="crop_btn"):
                result = image_tools.crop_image(data, int(left), int(top), int(right), int(bottom))
                _preview_and_download(data, result, f"{file.name.rsplit('.',1)[0]}_cropped.png", "image/png")
    except ImageToolError as exc:
        st.error(str(exc))


# ---------------------------------------------------------------------------
def _render_rotate_flip() -> None:
    info_card("How it works", "Rotate by any angle or flip horizontally/vertically.")
    file = _uploader("rotflip_upl")
    if not file:
        empty_state("Upload an image to rotate or flip.")
        return

    data = file.getvalue()
    col1, col2 = st.columns(2)

    with col1:
        angle = st.slider("Rotate (degrees)", -180, 180, 0, key="rot_angle")
        if st.button("Rotate", type="primary", key="rot_btn"):
            try:
                result = image_tools.rotate_image(data, angle)
                _preview_and_download(data, result, f"{file.name.rsplit('.',1)[0]}_rotated.png", "image/png")
            except ImageToolError as exc:
                st.error(str(exc))

    with col2:
        direction = st.radio("Flip direction", ["horizontal", "vertical"], key="flip_dir")
        if st.button("Flip", type="primary", key="flip_btn"):
            try:
                result = image_tools.flip_image(data, direction)
                _preview_and_download(data, result, f"{file.name.rsplit('.',1)[0]}_flipped.png", "image/png")
            except ImageToolError as exc:
                st.error(str(exc))


# ---------------------------------------------------------------------------
def _render_filters() -> None:
    info_card("How it works", "Adjust brightness/contrast/saturation/sharpness, or apply a preset filter.")
    file = _uploader("filter_upl")
    if not file:
        empty_state("Upload an image to enhance or filter.")
        return

    data = file.getvalue()
    sub_tabs = st.tabs(["Enhance", "Preset filters"])

    with sub_tabs[0]:
        c1, c2, c3, c4 = st.columns(4)
        brightness = c1.slider("Brightness", 0.0, 2.0, 1.0, 0.05, key="e_bri")
        contrast = c2.slider("Contrast", 0.0, 2.0, 1.0, 0.05, key="e_con")
        saturation = c3.slider("Saturation", 0.0, 2.0, 1.0, 0.05, key="e_sat")
        sharpness = c4.slider("Sharpness", 0.0, 2.0, 1.0, 0.05, key="e_shp")

        if st.button("Apply Enhancements", type="primary", key="enhance_btn"):
            try:
                result = image_tools.adjust_enhancements(data, brightness, contrast, saturation, sharpness)
                _preview_and_download(data, result, f"{file.name.rsplit('.',1)[0]}_enhanced.png", "image/png")
            except ImageToolError as exc:
                st.error(str(exc))

    with sub_tabs[1]:
        filter_choice = st.selectbox(
            "Choose a filter",
            ["Grayscale", "Blur", "Sharpen", "Edge Detection", "Denoise"],
            key="preset_filter",
        )
        blur_radius = None
        if filter_choice == "Blur":
            blur_radius = st.slider("Blur radius", 0.5, 15.0, 2.0, 0.5, key="blur_radius")

        if st.button("Apply Filter", type="primary", key="filter_btn"):
            try:
                if filter_choice == "Grayscale":
                    result = image_tools.to_grayscale(data)
                elif filter_choice == "Blur":
                    result = image_tools.apply_blur(data, radius=blur_radius or 2.0)
                elif filter_choice == "Sharpen":
                    result = image_tools.apply_sharpen(data)
                elif filter_choice == "Edge Detection":
                    result = image_tools.apply_edge_detection(data)
                else:
                    result = image_tools.denoise_image(data)
                _preview_and_download(data, result, f"{file.name.rsplit('.',1)[0]}_{filter_choice.lower()}.png", "image/png")
            except ImageToolError as exc:
                st.error(str(exc))


# ---------------------------------------------------------------------------
def _render_background() -> None:
    info_card(
        "How it works",
        "Makes near-white background pixels transparent — great for scanned logos or product shots on white. "
        "Not a substitute for an ML-based background remover on complex photos.",
    )
    file = _uploader("bg_upl")
    if not file:
        empty_state("Upload an image with a white/light background.")
        return

    data = file.getvalue()
    threshold = st.slider("Whiteness threshold", 200, 254, 240, key="bg_threshold")

    if st.button("Remove Background", type="primary", key="bg_btn"):
        try:
            result = image_tools.remove_background_naive(data, threshold=threshold)
            st.caption("Result (checkerboard = transparent):")
            st.image(result, use_container_width=True)
            st.download_button(
                "⬇️ Download PNG (transparent)", data=result,
                file_name=f"{file.name.rsplit('.',1)[0]}_nobg.png", mime="image/png", type="primary",
            )
        except ImageToolError as exc:
            st.error(str(exc))
