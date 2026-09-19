# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""JS generators for DOM overlays: title, annotation panel, footer."""

from __future__ import annotations

import json


def js_title_overlay(
    *,
    title: str,
    container_expr: str,
    positioning: str = "fixed",
    show_title: bool = True,
    z_index: int = 5,
) -> str:
    """Generate JS for creating a title DOM element.

    Args:
        title: Title text (raw, will be safely embedded via ``json.dumps``).
        container_expr: JS expression for the parent container.
        positioning: ``"fixed"`` for full-page or ``"absolute"`` for figure.
        show_title: If False, returns an empty string regardless of content.
        z_index: CSS z-index for the overlay.

    Returns:
        JS code string, or empty string if title is empty or hidden.
    """
    if not show_title or not title:
        return ""

    safe_title = json.dumps(title)
    return f"""// Title
const titleEl = document.createElement('div');
titleEl.innerHTML = {safe_title};
if (typeof renderMathInElement !== 'undefined') {{
    try {{
        renderMathInElement(titleEl, {{
            delimiters: [
                {{ left: '$$', right: '$$', display: true }},
                {{ left: '$', right: '$', display: false }},
            ],
            throwOnError: false,
        }});
    }} catch (e) {{ /* ignore rendering errors */ }}
}}
titleEl.style.position = '{positioning}';
titleEl.style.top = '10px';
titleEl.style.left = '50%';
titleEl.style.transform = 'translateX(-50%)';
titleEl.style.color = '#ffffff';
titleEl.style.fontFamily = 'sans-serif';
titleEl.style.fontSize = '20px';
titleEl.style.fontWeight = 'bold';
titleEl.style.background = 'rgba(0, 0, 0, 0.6)';
titleEl.style.padding = '6px 20px';
titleEl.style.borderRadius = '4px';
titleEl.style.pointerEvents = 'none';
titleEl.style.zIndex = '{z_index}';
{container_expr}.appendChild(titleEl);"""


def js_annotation_panel(
    *,
    annotation_md: str,
    container_expr: str,
    positioning: str = "fixed",
    show_annotation: bool = True,
    z_index: int = 5,
    reposition_controls: bool = False,
) -> str:
    """Generate JS for creating a markdown annotation panel.

    Uses ``marked.parse()`` + ``renderMathInElement()`` if available.
    The markdown text is embedded safely via ``json.dumps``.

    Args:
        annotation_md: Markdown text (raw).
        container_expr: JS expression for the parent container.
        positioning: ``"fixed"`` for full-page or ``"absolute"`` for figure.
        show_annotation: If False, returns an empty string.
        z_index: CSS z-index.
        reposition_controls: If True, also emit a ``ResizeObserver`` that
            repositions the ``#tanga-controls`` bar relative to the annotation
            height.  Used by animated exports.

    Returns:
        JS code string, or empty string if annotation is empty or hidden.
    """
    if not show_annotation or not annotation_md:
        return ""

    safe_md = json.dumps(annotation_md)

    reposition_block = ""
    if reposition_controls:
        reposition_block = """
if (typeof ResizeObserver !== 'undefined') {
    new ResizeObserver(function() {
        var ctrl = document.getElementById('tanga-controls');
        if (ctrl) {
            ctrl.style.bottom = Math.min(annContainer.scrollHeight, 250) + 8 + 'px';
        }
    }).observe(annContainer);
}
var _reposition = function() {
    var ctrl = document.getElementById('tanga-controls');
    if (ctrl) {
        ctrl.style.bottom = Math.min(annContainer.scrollHeight, 250) + 8 + 'px';
    }
};
_reposition();
"""

    return f"""// Annotation
const annContainer = document.createElement('div');
if (typeof marked !== 'undefined') {{
    annContainer.innerHTML = marked.parse({safe_md}, {{ breaks: true }});
}} else {{
    annContainer.textContent = {safe_md};
}}
if (typeof renderMathInElement !== 'undefined') {{
    try {{
        renderMathInElement(annContainer, {{
            delimiters: [
                {{ left: '$$', right: '$$', display: true }},
                {{ left: '$', right: '$', display: false }},
            ],
            throwOnError: false,
        }});
    }} catch (e) {{ /* ignore rendering errors */ }}
}}
annContainer.style.position = '{positioning}';
annContainer.style.bottom = '0px';
annContainer.style.left = '0px';
annContainer.style.right = '0px';
annContainer.style.maxHeight = '120px';
annContainer.style.overflowY = 'auto';
annContainer.style.fontFamily = 'sans-serif';
annContainer.style.fontSize = '11px';
annContainer.style.color = '#ccc';
annContainer.style.backgroundColor = 'rgba(0,0,0,0.7)';
annContainer.style.padding = '6px 12px';
annContainer.style.zIndex = '{z_index}';
annContainer.style.lineHeight = '1.4';
{container_expr}.appendChild(annContainer);{reposition_block}"""


def js_footer(
    *,
    footer_md: str,
    container_expr: str,
) -> str:
    """Generate JS for creating a footer element below the canvas.

    Args:
        footer_md: Markdown text (raw, will be safely embedded via
            ``json.dumps``).
        container_expr: JS expression for the parent container.

    Returns:
        JS code string, or empty string if footer is empty.
    """
    if not footer_md:
        return ""

    safe_md = json.dumps(footer_md)
    return f"""// Footer
const footerDiv = document.createElement('div');
if (typeof marked !== 'undefined') {{
    footerDiv.innerHTML = marked.parse({safe_md}, {{ breaks: true }});
}} else {{
    footerDiv.textContent = {safe_md};
}}
if (typeof renderMathInElement !== 'undefined') {{
    try {{ renderMathInElement(footerDiv, {{ delimiters: [
        {{ left: '$$', right: '$$', display: true }},
        {{ left: '$', right: '$', display: false }} ], throwOnError: false }}); }}
    catch (e) {{ /* ignore */ }}
}}
footerDiv.style.padding = '6px 12px';
footerDiv.style.fontFamily = 'sans-serif';
footerDiv.style.fontSize = '12px';
footerDiv.style.color = '#aaa';
footerDiv.style.lineHeight = '1.5';
{container_expr}.appendChild(footerDiv);"""


def js_coordinate_overlay_setup(
    *,
    objects_expr: str,
    container_expr: str,
    camera_var: str,
    renderer_var: str,
    label_renderer_var: str,
    width_expr: str,
    height_expr: str,
) -> str:
    """Generate JS that builds the ``axes_overlay`` + ``grid_underlay`` renderers.

    Creates the underlay container (behind the WebGL canvas) and the axes frame
    overlay, and exposes ``updateCoordinateOverlays()`` for the render loop.
    """
    return f"""// Coordinate frame (axes overlay + grid underlay)
const _axesSpec = {objects_expr}.find(o => o.kind === 'axes_overlay');
const _gridSpec = {objects_expr}.find(o => o.kind === 'grid_underlay');
let _gridUnderlay = null;
let _axesOverlay = null;

if (_gridSpec) {{
    const _underlayEl = document.createElement('div');
    _underlayEl.style.position = 'absolute';
    _underlayEl.style.top = '0';
    _underlayEl.style.left = '0';
    _underlayEl.style.width = '100%';
    _underlayEl.style.height = '100%';
    _underlayEl.style.pointerEvents = 'none';
    _underlayEl.style.zIndex = '0';
    {container_expr}.insertBefore(_underlayEl, {renderer_var}.domElement);
    {renderer_var}.domElement.style.position = 'relative';
    {renderer_var}.domElement.style.zIndex = '1';
    {label_renderer_var}.domElement.style.zIndex = '2';
    _gridUnderlay = new GridUnderlay(_gridSpec.spec);
    _gridUnderlay.mount(_underlayEl);
}}

if (_axesSpec) {{
    _axesOverlay = new AxesOverlay(_axesSpec.spec);
    _axesOverlay.mount({container_expr});
}}

function updateCoordinateOverlays() {{
    const cam = {camera_var};
    const params = {{
        left: cam.left, right: cam.right, top: cam.top, bottom: cam.bottom,
        zoom: cam.zoom || 1, x: cam.position.x, y: cam.position.y,
    }};
    if (_gridUnderlay) _gridUnderlay.update(params, {width_expr}, {height_expr});
    if (_axesOverlay) _axesOverlay.update(params, {width_expr}, {height_expr});
}}
"""

