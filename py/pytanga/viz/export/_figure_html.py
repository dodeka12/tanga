# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Figure HTML snippet export for embedding in presentations (Phase 13).

Generates a self-contained ``<div>`` + ``<script type="module">`` block ---
no ``<html>``, no ``<head>``, no global style resets.  Suitable for direct
inclusion in reveal.js, Slidev, Marp, or any HTML-based presentation.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List
from uuid import uuid4

from pytanga.viz.export._bootstrap import (
    contains_math,
    generate_bootstrap_js,
    html_snippet_template,
    js_annotation_panel,
    js_apply_camera,
    js_autofit_camera,
    js_footer,
    js_imports,
    js_render_loop,
    js_resize_handler,
    js_scene_build,
    js_scene_setup,
    js_title_overlay,
    katex_css_if_needed,
)


def render_figure(
    objects: List[Dict[str, Any]],
    scene_config: Dict[str, Any],
    figure_style: Dict[str, Any],
    figure_config: Dict[str, Any],
) -> str:
    """Render a figure HTML snippet from the unified scene objects."""
    fig_id = "tanga-fig-" + uuid4().hex[:8]
    scene_json = json.dumps({"objects": objects}, indent=0)

    bootstrap = generate_bootstrap_js(
        _build_static_figure_adapter(
            fig_id, scene_json, scene_config, figure_style, figure_config
        )
    )

    w = figure_style.get("width", 800)
    h = figure_style.get("height", 600)
    bg = figure_style.get("background", "transparent")
    br = figure_style.get("border_radius", "0")
    responsive = figure_style.get("responsive", False)

    config_json = json.dumps(
        {
            "title": figure_config.get("title", ""),
            "annotation": figure_config.get("annotation", ""),
            "footer": figure_config.get("footer", ""),
            "background": figure_config.get("background", "#1a1a2e"),
        }
    )

    has_math = (
        contains_math(scene_json)
        or contains_math(figure_config.get("annotation", ""))
        or contains_math(figure_config.get("footer", ""))
        or contains_math(figure_config.get("title", ""))
    )

    katex_css = ""
    if has_math:
        katex_css = katex_css_if_needed(
            annotation=figure_config.get("annotation", ""),
            footer=figure_config.get("footer", ""),
        )
        if not katex_css:
            katex_css = (
                '<link rel="stylesheet" '
                'href="https://cdn.jsdelivr.net/npm/katex'
                '@0.16.11/dist/katex.min.css">\n'
            )

    if responsive:
        container_style = (
            f"width:100%;height:100%;position:relative;overflow:hidden;"
            f"background:{bg};border-radius:{br};"
        )
    else:
        container_style = (
            f"width:{w}px;height:{h}px;position:relative;overflow:hidden;"
            f"background:{bg};border-radius:{br};"
        )

    responsive_style_block = ""
    if responsive:
        responsive_style_block = (
            "<style>\n"
            "html, body { margin: 0; padding: 0; width: 100%; height: 100%; "
            "overflow: hidden; }\n"
            "</style>\n"
        )

    return html_snippet_template(
        fig_id=fig_id,
        container_style=container_style,
        katex_css=katex_css,
        responsive_style_block=responsive_style_block,
        bootstrap_js=bootstrap,
        config_data_json=config_json,
    )


def render_export_figure(
    objects: List[Dict[str, Any]],
    scene_config: Dict[str, Any],
    figure_style: Dict[str, Any],
    figure_config: Dict[str, Any],
) -> str:
    """Deprecated: use :func:`render_figure`."""
    import warnings

    warnings.warn(
        "render_export_figure() is deprecated; use render_figure()",
        DeprecationWarning,
        stacklevel=2,
    )
    return render_figure(objects, scene_config, figure_style, figure_config)


# ======================================================================
# Figure bootstrap adapter (composed from shared JS generators)
# ======================================================================


def _build_static_figure_adapter(
    fig_id: str,
    scene_json: str,
    scene_config: Dict[str, Any],
    figure_style: Dict[str, Any],
    figure_config: Dict[str, Any],
) -> str:
    """Generate the JS bootstrap adapter for a figure export."""
    w = figure_style.get("width", 800)
    h = figure_style.get("height", 600)
    responsive = figure_style.get("responsive", False)
    bg = figure_config.get("background", "#1a1a2e")
    title_raw = figure_config.get("title", "")
    annotation_raw = figure_config.get("annotation", "")
    footer_raw = figure_config.get("footer", "")
    auto_rotate = figure_style.get("auto_rotate", False)
    show_title = figure_style.get("show_title", True)
    show_annotation = figure_style.get("show_annotation", True)

    # Camera config from scene_config (if present)
    cam_cfg = scene_config.get("camera") or {}
    cam_explicit = bool(cam_cfg.get("position") or cam_cfg.get("target"))

    # ── Dimension helpers ─────────────────────────────────────
    space_dim = scene_config.get("space_dim", 3)
    if responsive:
        dim_w = "(figContainer.clientWidth || window.innerWidth)"
        dim_h = "(figContainer.clientHeight || window.innerHeight)"
    else:
        dim_w = str(w)
        dim_h = str(h)

    parts = [
        "window.__tanga_ready = true;",
        "// Figure bootstrap for Tanga 3D figure export",
        "",
        js_imports(),
        "",
        js_apply_camera(),
        "",
        f"const figContainer = document.getElementById('{fig_id}');",
        f"const figData = {scene_json};",
        "const figObjects = figData.objects || [];",
        f"const sceneConfig = {json.dumps(scene_config)};",
        "",
        js_scene_setup(
            bg_color=bg,
            container_expr="figContainer",
            append_to="figContainer",
            renderer_var="figRenderer",
            label_renderer_var="figLabelRenderer",
            camera_var="figCamera",
            controls_var="figControls",
            scene_var="figScene",
            width_expr=dim_w,
            height_expr=dim_h,
            auto_rotate=auto_rotate,
            space_dim=space_dim,
            explicit_mouse_buttons=True,
        ),
        js_resize_handler(
            renderer_var="figRenderer",
            label_renderer_var="figLabelRenderer",
            camera_var="figCamera",
            width_expr=dim_w,
            height_expr=dim_h,
            conditional=not responsive,
            container_expr="figContainer" if responsive else "",
        ),
        "",
        js_title_overlay(
            title=title_raw,
            container_expr="figContainer",
            positioning="absolute",
            show_title=show_title,
        ),
        "",
        js_scene_build(
            objects_expr="figObjects",
            scene_var="figScene",
            registry_var="figRegistry",
            mesh_map_var="figMeshMap",
            build_done_var="figBuildDone",
        ),
        "",
        "(async () => {\n"
        "    await figBuildDone;\n"
        "    applyCameraConfig(figCamera, figControls, sceneConfig.camera, "
        + dim_w
        + ", "
        + dim_h
        + ");\n"
        + js_autofit_camera(
            registry_var="figRegistry",
            camera_var="figCamera",
            controls_var="figControls",
            cam_explicit=cam_explicit,
            space_dim=space_dim,
            width_expr=dim_w,
            height_expr=dim_h,
        )
        + "\n})();",
        "",
        js_annotation_panel(
            annotation_md=annotation_raw,
            container_expr="figContainer",
            positioning="absolute",
            show_annotation=show_annotation,
        ),
        js_footer(
            footer_md=footer_raw,
            container_expr="figContainer",
        ),
        "",
        js_render_loop(
            renderer_var="figRenderer",
            label_renderer_var="figLabelRenderer",
            scene_var="figScene",
            camera_var="figCamera",
            controls_var="figControls",
        ),
    ]

    return "\n\n".join(parts)
