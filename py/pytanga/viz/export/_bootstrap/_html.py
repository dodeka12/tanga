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
from pytanga.viz.export._bootstrap._scene import (
    js_runtime_imports,
    js_tanga_bridge,
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
# live viewer and the export bootstrap.  ``camera-fit.js`` is the shared,
# pure ortho/aspect math used by ``fit_camera.js`` and ``js_apply_camera``.
_SHARED_JS_FILES: list[Path] = [
    _TEMPLATES_DIR / "camera-fit.js",
    _TEMPLATES_DIR / "scene-builder.js",
    _TEMPLATES_DIR / "fit_camera.js",
    # SDF tree emitters used by the per-object SDF proxy renderer (`sdf.js`).
    _TEMPLATES_DIR / "sdf" / "objects" / "transform.js",
    _TEMPLATES_DIR / "sdf" / "objects" / "primitives.js",
    _TEMPLATES_DIR / "sdf" / "objects" / "combinators.js",
]

_SDF_SHADER_KEYS = ("common", "primitives", "combinators", "proxy")

_SDF_SHADER_FILES: list[Path] = [
    _TEMPLATES_DIR / "sdf" / "shaders" / "sdf_common.glsl",
    _TEMPLATES_DIR / "sdf" / "shaders" / "primitives.glsl",
    _TEMPLATES_DIR / "sdf" / "shaders" / "combinators.glsl",
    _RENDERERS_DIR / "sdf" / "proxy.glsl",
]


def third_party_scripts(delivery: str) -> str:
    """Return the marked/KaTeX/html2canvas script block for *delivery*."""
    if delivery == "offline":
        from pytanga.viz.export._offline import offline_third_party_html

        return offline_third_party_html()
    return _CDN_SCRIPTS


def offline_katex_css() -> str:
    """Return the offline KaTeX CSS as an inlined ``<style>`` block."""
    from pytanga.viz.export._offline import offline_katex_css as _offline_katex_css

    return _offline_katex_css()


def three_import_map(delivery: str) -> str:
    """Return the Three.js import map (empty for the offline bundle)."""
    return "" if delivery == "offline" else _THREEJS_IMPORT_MAP


def katex_css_for_delivery(delivery: str, cdn_css: str) -> str:
    """Adapt a conditional KaTeX CSS link for *delivery*."""
    if not cdn_css:
        return ""
    if delivery == "offline":
        return offline_katex_css()
    return cdn_css


def static_third_party(delivery: str) -> str:
    """Return the static snapshot's full third-party block (KaTeX CSS always)."""
    if delivery == "offline":
        return third_party_scripts("offline") + offline_katex_css()
    return _CDN_SCRIPTS + _KATEX_CSS_LINK


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


def library_source_files() -> list[Path]:
    """Return the ordered list of every file that feeds :func:`generate_library_js`."""
    return list(_RENDERER_FILES) + list(_SHARED_JS_FILES) + list(_SDF_SHADER_FILES)


def generate_library_js() -> str:
    """Return the shared viewer library (runtime imports, renderer modules, bridge).

    This is the scene-independent part of an export: the ``three``/addons
    imports, the inlined SDF shaders, a no-op ``sendLog``/``sendEvent`` stub,
    the stripped renderer + shared modules, and the ``window.__tanga`` bridge.
    """
    parts: list[str] = [
        js_runtime_imports(),
        _sdf_shader_injection(),
        "function sendLog() {}\nfunction sendEvent() {}",
    ]
    for path in _RENDERER_FILES + _SHARED_JS_FILES:
        parts.append(_strip_imports(path.read_text(encoding="utf-8")))
    parts.append(js_tanga_bridge())
    return "\n\n".join(parts)


def generate_bootstrap_js(adapter_js: str) -> str:
    """Concatenate the shared library with an adapter JS string.

    Composes :func:`generate_library_js` (the scene-independent runtime +
    renderer modules) with the scene-specific adapter for the inline delivery
    path.
    """
    return generate_library_js() + "\n\n" + adapter_js


def generate_theme_css(theme_id: str) -> str:
    """Return the active theme's CSS inlined into a single ``<style>`` block.

    Symmetric to :func:`generate_bootstrap_js`: reads the resolved CSS files
    (via the theme registry) and concatenates them in order, so standalone HTML
    exports carry the active theme with no external ``<link>``.
    """
    from pytanga.viz._themes import registry

    parts = [p.read_text(encoding="utf-8") for p in registry.theme_css_paths(theme_id)]
    css = "\n".join(parts)
    return f"<style>\n{css}\n</style>\n"


def _sdf_shader_injection() -> str:
    """Inline the SDF proxy GLSL as a global for standalone HTML exports.

    The live viewer fetches these ``.glsl`` files from the server; a standalone
    export has no server, so ``sdf.js`` falls back to this inlined global.
    """
    parts = {
        key: path.read_text(encoding="utf-8")
        for key, path in zip(_SDF_SHADER_KEYS, _SDF_SHADER_FILES, strict=True)
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
    library_script: str = "",
    adapter_js: str = "",
    third_party_html: str = "",
    import_map_html: str = "",
    theme_css: str = "",
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
        library_script: The viewer library ``<script>`` tag (src or inlined).
        adapter_js: The scene-specific adapter JS (destructures ``window.__tanga``).
        third_party_html: Marked/KaTeX/html2canvas ``<script>``/``<style>`` block.
        import_map_html: The Three.js import map (empty for offline).
        theme_css: Inlined theme CSS ``<style>`` block (``generate_theme_css``).

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
        + third_party_html
        + import_map_html
        + theme_css
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
        + library_script
        + '<script type="module">\n'
        + adapter_js
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
    library_script: str = "",
    adapter_js: str = "",
    third_party_html: str = "",
    import_map_html: str = "",
    config_data_json: str = "{}",
    theme_css: str = "",
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
        library_script: The viewer library ``<script>`` tag (src or inlined).
        adapter_js: The scene-specific adapter JS (destructures ``window.__tanga``).
        third_party_html: Marked/KaTeX/html2canvas ``<script>``/``<style>`` block.
        import_map_html: The Three.js import map (empty for offline).
        config_data_json: JSON string for ``data-figure-config`` attribute.
        theme_css: Inlined theme CSS ``<style>`` block (``generate_theme_css``).

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
        + third_party_html
        + katex_css
        + responsive_style_block
        + theme_css
        + import_map_html
        + anim_embed
        + decompress_js
        + f'<div id="{fig_id}"'
        + f' style="{container_style}"'
        + f" data-figure-config='{escaped_config}'>"
        + controls_html
        + "</div>\n"
        + library_script
        + '<script type="module">\n'
        + adapter_js
        + "\n</script>"
    )
