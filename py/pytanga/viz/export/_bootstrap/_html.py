# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""HTML template helpers and bootstrap concatenation utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pytanga.viz.export._bootstrap._errors import (
    js_cdn_check_script,
    js_loading_overlay_html,
)
from pytanga.viz.export._bootstrap._utils import _escape_html

_CDN_CHECK_SCRIPT = js_cdn_check_script()
_LOADING_OVERLAY_HTML = js_loading_overlay_html()

# ── CDN / shared HTML constants ────────────────────────────────────

_CDN_MARKED_JS = (
    '<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>\n'
)

_CDN_KATEX_JS = (
    '<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js">'
    "</script>\n"
)

_CDN_KATEX_AUTORENDER_JS = (
    '<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js">'
    "</script>\n"
)

_CDN_HTML2CANVAS_JS = (
    '<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js">'
    "</script>\n"
)

_CDN_SCRIPTS = (
    _CDN_MARKED_JS + _CDN_KATEX_JS + _CDN_KATEX_AUTORENDER_JS + _CDN_HTML2CANVAS_JS
)

_THREEJS_IMPORT_MAP = (
    '<script type="importmap">\n'
    "  {\n"
    '    "imports": {\n'
    '      "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",\n'
    '      "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"\n'
    "    }\n"
    "  }\n"
    "</script>\n"
)

_KATEX_CSS_LINK = (
    '<link rel="stylesheet" '
    'href="https://cdn.jsdelivr.net/npm/katex'
    '@0.16.11/dist/katex.min.css">\n'
)

# ── Renderer file list ─────────────────────────────────────────────

_RENDERERS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "templates" / "renderers"
)

_RENDERER_FILES: list[Path] = [
    _RENDERERS_DIR / "style-diff.js",
    _RENDERERS_DIR / "utils.js",
    _RENDERERS_DIR / "point.js",
    _RENDERERS_DIR / "crosshair_point.js",
    _RENDERERS_DIR / "direction.js",
    _RENDERERS_DIR / "line.js",
    _RENDERERS_DIR / "plane.js",
    _RENDERERS_DIR / "arc.js",
    _RENDERERS_DIR / "circle.js",
    _RENDERERS_DIR / "cylinder.js",
    _RENDERERS_DIR / "box.js",
    _RENDERERS_DIR / "disk.js",
    _RENDERERS_DIR / "ellipse.js",
    _RENDERERS_DIR / "ellipsoid.js",
    _RENDERERS_DIR / "partial_disk.js",
    _RENDERERS_DIR / "regular_polygon.js",
    _RENDERERS_DIR / "sphere.js",
    _RENDERERS_DIR / "space.js",
    _RENDERERS_DIR / "operators" / "point_pair.js",
    _RENDERERS_DIR / "operators" / "inversion.js",
    _RENDERERS_DIR / "operators" / "rotor.js",
    _RENDERERS_DIR / "operators" / "translator.js",
    _RENDERERS_DIR / "operators" / "dilator.js",
    _RENDERERS_DIR / "operators" / "motor.js",
    _RENDERERS_DIR / "operators" / "general_rotor.js",
    _RENDERERS_DIR / "operators" / "reflection_line.js",
    _RENDERERS_DIR / "operators" / "reflection_plane.js",
    _RENDERERS_DIR / "operators" / "reflection_point.js",
    _RENDERERS_DIR / "point_path.js",
    _RENDERERS_DIR / "axis.js",
    _RENDERERS_DIR / "axes2d.js",
    _RENDERERS_DIR / "axes3d.js",
    _RENDERERS_DIR / "grid.js",
    _RENDERERS_DIR / "group.js",
    _RENDERERS_DIR / "factory.js",
    _RENDERERS_DIR / "sdf.js",
    _RENDERERS_DIR / "sdf" / "lighting.js",
    _RENDERERS_DIR / "sdf" / "glsl.js",
]

_TEMPLATES_DIR = _RENDERERS_DIR.parent

# Shared (non-renderer) JS modules bundled alongside the renderer modules.
# ``scene-builder.js`` provides the scene-graph construction shared by the
# live viewer and the export bootstrap.
_SHARED_JS_FILES: list[Path] = [
    _TEMPLATES_DIR / "scene-builder.js",
    _TEMPLATES_DIR / "fit_camera.js",
    # SDF tree emitters used by the per-object SDF proxy renderer (`sdf.js`).
    _TEMPLATES_DIR / "sdf" / "objects" / "transform.js",
    _TEMPLATES_DIR / "sdf" / "objects" / "primitives.js",
    _TEMPLATES_DIR / "sdf" / "objects" / "combinators.js",
]


# ── Bootstrap concatenation ────────────────────────────────────────


def _strip_imports(source: str) -> str:
    """Remove ``import`` statements and strip ``export`` keywords from a JS module.

    ``import`` statements are removed entirely — both single-line and
    multi-line forms (``import { a, b } from '...'``).

    ``export`` **keywords** are stripped so the functions become locally
    scoped within the single ``<script type="module">`` block, but the
    function/class/const declarations themselves are kept.
    """
    import re

    lines = source.splitlines()
    stripped: list[str] = []
    in_import = False
    brace_depth = 0

    for line in lines:
        s = line.strip()

        # Enter multi-line import
        if not in_import and s.startswith("import "):
            if s.endswith(";"):
                # Single-line import — skip entirely
                continue
            # Multi-line import starts with { on same or next line
            brace_depth = s.count("{") - s.count("}")
            if brace_depth > 0:
                in_import = True
            continue

        if in_import:
            brace_depth += s.count("{") - s.count("}")
            if brace_depth <= 0 and s.rstrip().endswith(";"):
                in_import = False
            continue

        # Strip 'export default ' or 'export ' keyword prefix
        line = re.sub(r"^(\s*)export\s+default\s+", r"\1", line)
        line = re.sub(r"^(\s*)export\s+", r"\1", line)
        stripped.append(line)

    # Collapse consecutive blank lines.
    cleaned: list[str] = []
    prev_blank = False
    for line in stripped:
        is_blank = line.strip() == ""
        if is_blank:
            if not prev_blank and cleaned:
                cleaned.append("")
            prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False

    # Strip leading/trailing blanks.
    while cleaned and cleaned[0].strip() == "":
        cleaned.pop(0)
    while cleaned and cleaned[-1].strip() == "":
        cleaned.pop()
    return "\n".join(cleaned)


def generate_bootstrap_js(adapter_js: str) -> str:
    """Concatenate stripped renderer modules + an adapter JS string.

    This replaces the duplicated 10-line pattern that appeared in every
    ``_generate_*_bootstrap()`` function across ``_html.py``,
    ``_figure_html.py``, and ``_animated_figure.py``.
    """
    parts: list[str] = []
    parts.append("import * as THREE from 'three';")
    parts.append(_sdf_shader_injection())

    for path in _RENDERER_FILES + _SHARED_JS_FILES:
        src = path.read_text(encoding="utf-8")
        src = _strip_imports(src)
        parts.append(src)

    parts.append(adapter_js)
    return "\n\n".join(parts)


def _sdf_shader_injection() -> str:
    """Inline the SDF proxy GLSL as a global for standalone HTML exports.

    The live viewer fetches these ``.glsl`` files from the server; a standalone
    export has no server, so ``sdf.js`` falls back to this inlined global.
    """
    parts = {
        "common": (_TEMPLATES_DIR / "sdf" / "shaders" / "sdf_common.glsl").read_text(
            encoding="utf-8"
        ),
        "primitives": (
            _TEMPLATES_DIR / "sdf" / "shaders" / "primitives.glsl"
        ).read_text(encoding="utf-8"),
        "combinators": (
            _TEMPLATES_DIR / "sdf" / "shaders" / "combinators.glsl"
        ).read_text(encoding="utf-8"),
        "proxy": (_RENDERERS_DIR / "sdf" / "proxy.glsl").read_text(encoding="utf-8"),
    }
    return "window.__tanga_sdf_shaders = " + json.dumps(parts) + ";"


# ── KaTeX CSS helper ──────────────────────────────────────────────


def katex_css_if_needed(
    recording_data: dict[str, Any] | None = None,
    fig_config: dict[str, Any] | None = None,
    annotation: str = "",
    footer: str = "",
) -> str:
    """Return the KaTeX CSS link if any text contains math delimiters (``$``).

    Checks label texts in recording_data, annotation/footer from fig_config,
    or explicit annotation/footer strings.
    """
    if recording_data:
        for frame in recording_data.get("frames", []):
            for obj in frame or []:
                text = obj.get("text", "")
                if text and "$" in text:
                    return _KATEX_CSS_LINK

    if fig_config:
        for key in ("annotation", "footer"):
            val = fig_config.get(key, "")
            if val and "$" in val:
                return _KATEX_CSS_LINK

    if annotation and "$" in annotation:
        return _KATEX_CSS_LINK
    if footer and "$" in footer:
        return _KATEX_CSS_LINK

    return ""


# ── HTML template helpers ──────────────────────────────────────────


def html_fullpage_template(
    *,
    title: str,
    bg_color: str,
    katex_css: str = "",
    anim_embed: str = "",
    decompress_js: str = "",
    title_html: str = "",
    annotation_html: str = "",
    controls_html: str = "",
    annotation_controls_reposition_js: str = "",
    body_div: str = "",
    bootstrap_js: str = "",
) -> str:
    """Return a full-page HTML document (``<!DOCTYPE html>`` ... ``</html>``).

    Args:
        title: HTML ``<title>`` tag content.
        bg_color: Page background color.
        katex_css: KaTeX CSS ``<link>`` tag or empty string.
        anim_embed: Animation data ``<script>`` tag(s).
        decompress_js: Decompression bootstrapper ``<script>`` or empty.
        title_html: Title overlay HTML (injected into ``<body>``).
        annotation_html: Annotation panel HTML (injected into ``<body>``).
        controls_html: Playback controls HTML (injected into ``<body>``).
        annotation_controls_reposition_js: Repositioning script block.
        body_div: The main container ``<div>`` for the 3D viewport.
        bootstrap_js: The concatenated renderer modules + adapter JS.

    Returns:
        Full HTML document string.
    """
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n" + _CDN_CHECK_SCRIPT + '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f"<title>{_escape_html(title)}</title>\n"
        "<style>\n"
        "* { margin: 0; padding: 0; box-sizing: border-box; }\n"
        "html, body { width: 100%; height: 100%; overflow: hidden; "
        f"background: {bg_color}; }}\n"
        "canvas { display: block; }\n"
        "#tanga-controls { z-index: 10; }\n"
        "</style>\n"
        + katex_css
        + _CDN_SCRIPTS
        + _THREEJS_IMPORT_MAP
        + anim_embed
        + decompress_js
        + "</head>\n"
        "<body>\n"
        + _LOADING_OVERLAY_HTML
        + title_html
        + annotation_html
        + body_div
        + controls_html
        + "\n"
        + annotation_controls_reposition_js
        + '<script type="module">\n'
        + bootstrap_js
        + "\n</script>\n"
        "</body>\n"
        "</html>"
    )


def html_snippet_template(
    *,
    fig_id: str,
    container_style: str,
    katex_css: str = "",
    anim_embed: str = "",
    decompress_js: str = "",
    responsive_style_block: str = "",
    controls_html: str = "",
    bootstrap_js: str = "",
    config_data_json: str = "{}",
) -> str:
    """Return an HTML snippet (``<div>`` + ``<script type="module">``) for embedding.

    Args:
        fig_id: Unique figure container ID.
        container_style: CSS style string for the container div.
        katex_css: KaTeX CSS ``<link>`` tag or empty string.
        anim_embed: Animation data ``<script>`` tag(s).
        decompress_js: Decompression bootstrapper.
        responsive_style_block: ``<style>`` block for responsive sizing.
        controls_html: Playback controls HTML (injected inside the container
            div for animated figures).
        bootstrap_js: Concatenated renderer modules + adapter JS.
        config_data_json: JSON string for ``data-figure-config`` attribute.

    Returns:
        HTML snippet string.
    """
    escaped_config = (
        config_data_json.replace("&", "&").replace("'", "&#39;").replace("<", "<")
    )

    return (
        "<!DOCTYPE html>\n"
        "<!-- Tanga 3D Figure -->\n"
        + _CDN_CHECK_SCRIPT
        + _LOADING_OVERLAY_HTML
        + _CDN_SCRIPTS
        + katex_css
        + responsive_style_block
        + _THREEJS_IMPORT_MAP
        + anim_embed
        + decompress_js
        + f'<div id="{fig_id}"'
        + f' style="{container_style}"'
        + f" data-figure-config='{escaped_config}'>"
        + controls_html
        + "</div>\n"
        + '<script type="module">\n'
        + bootstrap_js
        + "\n</script>"
    )
