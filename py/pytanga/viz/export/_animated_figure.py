# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Animated HTML figure export — self-contained HTML with JS playback engine.

Provides two generators:
- ``render_export_animated_figure()`` — HTML snippet (``<div>`` + ``<script>``)
  for embedding in presentations.
- ``render_export_animated_html()`` — full-page document (``<!DOCTYPE html>``
  to ``</html>``) for standalone viewing.

Both embed the recorded animation data and a ~150-line JS playback engine
with play/pause/scrub/speed/loop controls.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from pytanga.viz.export._bootstrap import (
    embed_animation_data,
    generate_bootstrap_js,
    get_anim_data_js,
    get_anim_decompress_js,
    html_fullpage_template,
    html_snippet_template,
    js_animated_render_loop,
    js_animation_data_init,
    js_animation_state,
    js_annotation_panel,
    js_apply_camera,
    js_autofit_camera,
    js_controls_html,
    js_controls_ui,
    js_footer,
    js_imports,
    js_reconcile_frame,
    js_resize_handler,
    js_scene_setup,
    js_title_overlay,
    katex_css_if_needed,
)

# ── Public API ──────────────────────────────────────────────────


def render_export_animated_figure(
    recording_data: dict[str, Any],
    *,
    figure_style: dict[str, Any] | None = None,
    figure_config: dict[str, Any] | None = None,
    scene_config: dict[str, Any] | None = None,
    anim_style: dict[str, Any] | None = None,
) -> str:
    """Render an animated figure HTML snippet for embedding.

    Args:
        recording_data: Dict with ``frames``, ``frame_count``
            from ``AnimationRecording.to_dict()``.
        figure_style: ``FigureStyle.to_dict()`` result.
        figure_config: ``FigureConfig.to_dict()`` result.
        scene_config: ``SceneConfig.to_dict()`` result (background, space_dim,
            camera).
        anim_style: ``AnimStyle.to_dict()`` result with ``fps``, ``loop``,
            ``show_controls``, ``compress`` keys.
    """
    as_ = anim_style or {}
    fps = as_.get("fps", 30)
    loop = as_.get("loop", True)
    show_controls = as_.get("show_controls", True)
    compress = as_.get("compress", False)

    fig_style = figure_style or {}
    fig_cfg = figure_config or {}

    w = fig_style.get("width", 800)
    h = fig_style.get("height", 600)
    bg = fig_style.get("background", "transparent")
    br = fig_style.get("border_radius", "0")
    responsive = fig_style.get("responsive", False)

    fig_id = "tanga-fig-" + uuid4().hex[:8]

    anim_data_json = json.dumps(
        {**recording_data, "fps": fps, "loop": loop},
        separators=(",", ":"),
    )
    anim_embed = embed_animation_data(anim_data_json, compress=compress)
    decompress_js = get_anim_decompress_js(compress)

    bootstrap = generate_bootstrap_js(
        _build_animated_figure_adapter(
            fig_id,
            recording_data,
            fps,
            loop,
            fig_style,
            fig_cfg,
            show_controls,
            scene_config or {},
        )
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

    katex_css = katex_css_if_needed(recording_data, fig_cfg)

    config_json = json.dumps(
        {
            "title": fig_cfg.get("title", ""),
            "annotation": fig_cfg.get("annotation", ""),
            "footer": fig_cfg.get("footer", ""),
            "background": fig_cfg.get("background", "#1a1a2e"),
        }
    )

    return html_snippet_template(
        fig_id=fig_id,
        container_style=container_style,
        katex_css=katex_css,
        anim_embed=anim_embed,
        decompress_js=decompress_js,
        responsive_style_block=responsive_style_block,
        controls_html=js_controls_html(show_controls),
        bootstrap_js=bootstrap,
        config_data_json=config_json,
    )


def render_export_animated_html(
    recording_data: dict[str, Any],
    *,
    scene_config: dict[str, Any] | None = None,
    anim_style: dict[str, Any] | None = None,
    title: str = "Tanga 3D Viewer",
) -> str:
    """Render a full-page animated HTML document for standalone viewing.

    Args:
        recording_data: Dict with ``frames``, ``frame_count``
            from ``AnimationRecording.to_dict()``.
        scene_config: ``SceneConfig.to_dict()`` result (background, grid, axes,
            camera).
        anim_style: ``AnimStyle.to_dict()`` result with ``fps``, ``loop``,
            ``show_controls``, ``compress`` keys.
        title: HTML ``<title>`` tag content.
    """
    as_ = anim_style or {}
    fps = as_.get("fps", 30)
    loop = as_.get("loop", True)
    show_controls = as_.get("show_controls", True)
    compress = as_.get("compress", False)

    sc = scene_config or {}
    bg_color = sc.get("background_color", "#1a1a2e")
    fig_id = "tanga-fig-" + uuid4().hex[:8]

    anim_data_json = json.dumps(
        {**recording_data, "fps": fps, "loop": loop},
        separators=(",", ":"),
    )
    anim_embed = embed_animation_data(anim_data_json, compress=compress)
    decompress_js = get_anim_decompress_js(compress)

    bootstrap = generate_bootstrap_js(
        _build_animated_fullpage_adapter(
            fig_id, recording_data, fps, loop, sc, show_controls
        )
    )

    controls_html = js_controls_html(show_controls)
    katex_css = katex_css_if_needed(recording_data)

    body_div = (
        f'<div id="{fig_id}" style="width:100%;height:100%;position:relative;'
        'overflow:hidden;"></div>\n'
    )

    return html_fullpage_template(
        title=title,
        bg_color=bg_color,
        katex_css=katex_css,
        anim_embed=anim_embed,
        decompress_js=decompress_js,
        title_html="",
        annotation_html="",
        controls_html=controls_html,
        annotation_controls_reposition_js="",
        body_div=body_div,
        bootstrap_js=bootstrap,
    )


def _js_frame0_bootstrap(autofit_js: str, camera_apply_js: str = "") -> str:
    """Apply the initial camera, reify frame 0, then auto-fit.

    The initial camera is applied before ``_playFrame(0)`` so a per-frame
    camera (when present) can override it.  The auto-fit JS must run after
    frame-0 meshes exist; ``js_autofit_camera`` is synchronous, so it is
    embedded inside this async IIFE.
    """
    return f"""(async () => {{
{camera_apply_js}    await _playFrame(0);
{autofit_js}}})();"""


# ── JS adapter builders (composed from shared JS generators) ──


def _build_animated_figure_adapter(
    fig_id: str,
    recording_data: dict[str, Any],
    fps: int,
    loop: bool,
    figure_style: dict[str, Any],
    figure_config: dict[str, Any],
    show_controls: bool,
    scene_config: dict[str, Any],
) -> str:
    """Generate the JS bootstrap adapter for an animated figure snippet."""
    w = figure_style.get("width", 800)
    h = figure_style.get("height", 600)
    responsive = figure_style.get("responsive", False)
    bg = figure_style.get("background", "#1a1a2e")
    auto_rotate = figure_style.get("auto_rotate", False)
    space_dim = scene_config.get("space_dim", 3)
    show_title = figure_style.get("show_title", True)
    show_annotation = figure_style.get("show_annotation", True)

    cam_cfg = scene_config.get("camera") or {}
    cam_explicit = bool(cam_cfg.get("position") or cam_cfg.get("target"))

    title_raw = figure_config.get("title", "")
    annotation_raw = figure_config.get("annotation", "")
    footer_raw = figure_config.get("footer", "")

    loop_js = "true" if loop else "false"

    autofit_js = js_autofit_camera(
        registry_var="figRegistry",
        camera_var="figCamera",
        controls_var="figControls",
        cam_explicit=cam_explicit,
        space_dim=space_dim,
    )

    if responsive:
        dim_w = "(figContainer.clientWidth || window.innerWidth)"
        dim_h = "(figContainer.clientHeight || window.innerHeight)"
    else:
        dim_w = str(w)
        dim_h = str(h)

    parts = [
        "window.__tanga_ready = true;",
        "// Animated figure bootstrap",
        "",
        js_imports(),
        "",
        js_apply_camera(),
        "",
        f"const figContainer = document.getElementById('{fig_id}');",
        f"const sceneConfig = {json.dumps(scene_config)};",
        get_anim_data_js(),
        js_animation_data_init(
            fps,
            extra_map_vars="\nconst labelObjects = new Map();\nconst figRegistry = new Map();",
        ),
        "",
        js_animation_state(),
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
        js_reconcile_frame(
            scene_var="figScene",
            label_objects_map_var="labelObjects",
            camera_var="figCamera",
            controls_var="figControls",
            camera_size_w_expr=dim_w,
            camera_size_h_expr=dim_h,
        ),
        "",
        _js_frame0_bootstrap(
            autofit_js,
            camera_apply_js=(
                "    applyCameraConfig(figCamera, figControls, sceneConfig.camera, "
                + dim_w
                + ", "
                + dim_h
                + ");\n"
            ),
        ),
        "",
        js_annotation_panel(
            annotation_md=annotation_raw,
            container_expr="figContainer",
            positioning="absolute",
            show_annotation=show_annotation,
            reposition_controls=True,
        ),
        js_footer(
            footer_md=footer_raw,
            container_expr="figContainer",
        ),
        "",
        js_controls_ui(show_controls=show_controls),
        "",
        js_animated_render_loop(
            fps=fps,
            loop_js_bool=loop_js,
            scene_var="figScene",
            label_objects_map_var="labelObjects",
        ),
    ]

    return "\n\n".join(p for p in parts if p)


def _build_animated_fullpage_adapter(
    fig_id: str,
    recording_data: dict[str, Any],
    fps: int,
    loop: bool,
    scene_config: dict[str, Any],
    show_controls: bool,
) -> str:
    """Generate the JS bootstrap adapter for a full-page animated document."""
    bg = scene_config.get("background_color", "#1a1a2e")
    space_dim = scene_config.get("space_dim", 3)

    title_raw = scene_config.get("title", "")
    annotation_raw = scene_config.get("annotation", "")

    cam_cfg = scene_config.get("camera") or {}
    cam_explicit = bool(cam_cfg.get("position") or cam_cfg.get("target"))

    loop_js = "true" if loop else "false"

    autofit_js = js_autofit_camera(
        registry_var="figRegistry",
        camera_var="figCamera",
        controls_var="figControls",
        cam_explicit=cam_explicit,
        space_dim=space_dim,
    )

    parts = [
        "window.__tanga_ready = true;",
        "// Animated full-page bootstrap",
        "",
        js_imports(),
        "",
        js_apply_camera(),
        "",
        f"const figContainer = document.getElementById('{fig_id}');",
        f"const sceneConfig = {json.dumps(scene_config)};",
        get_anim_data_js(),
        js_animation_data_init(
            fps,
            extra_map_vars="\nconst labelObjects = new Map();\nconst figRegistry = new Map();",
        ),
        "",
        js_animation_state(),
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
            width_expr="window.innerWidth",
            height_expr="window.innerHeight",
            auto_rotate=False,
            space_dim=space_dim,
            explicit_mouse_buttons=True,
        ),
        js_resize_handler(
            renderer_var="figRenderer",
            label_renderer_var="figLabelRenderer",
            camera_var="figCamera",
            width_expr="window.innerWidth",
            height_expr="window.innerHeight",
        ),
        "",
        js_title_overlay(
            title=title_raw,
            container_expr="document.body",
            positioning="fixed",
            show_title=bool(title_raw),
        ),
        "",
        js_reconcile_frame(
            scene_var="figScene",
            label_objects_map_var="labelObjects",
            camera_var="figCamera",
            controls_var="figControls",
            camera_size_w_expr="window.innerWidth",
            camera_size_h_expr="window.innerHeight",
        ),
        "",
        _js_frame0_bootstrap(
            autofit_js,
            camera_apply_js=(
                "    applyCameraConfig(figCamera, figControls, sceneConfig.camera, window.innerWidth, window.innerHeight);\n"
            ),
        ),
        "",
        js_annotation_panel(
            annotation_md=annotation_raw,
            container_expr="document.body",
            positioning="fixed",
            show_annotation=bool(annotation_raw),
            reposition_controls=True,
        ),
        "",
        js_controls_ui(show_controls=show_controls),
        "",
        js_animated_render_loop(
            fps=fps,
            loop_js_bool=loop_js,
            scene_var="figScene",
            label_objects_map_var="labelObjects",
        ),
    ]

    return "\n\n".join(p for p in parts if p)
