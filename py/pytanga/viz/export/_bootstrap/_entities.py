# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""JS generators for the shared scene-graph construction loop."""

from __future__ import annotations


def js_scene_build(
    *,
    objects_expr: str,
    scene_var: str,
    registry_var: str,
    mesh_map_var: str,
    build_done_var: str,
) -> str:
    """Generate JS that builds all scene objects via the shared scene-builder.

    Emits a single async IIFE (assigned to *build_done_var*) that constructs
    scene-layer objects (``buildSceneObject``) and overlay objects
    (``buildOverlay``) in DFS order, then derives the entity ``meshMap``
    (``id`` -> node) used by camera auto-fit.  Callers ``await``
    *build_done_var* before auto-fitting the camera.

    Args:
        objects_expr: JS expression yielding the unified ``objects`` array
            (``Scene.full_state()`` output).
        scene_var: JS variable name for the three.js Scene.
        registry_var: JS variable name for the ``id`` -> entry registry Map.
        mesh_map_var: JS variable name for the ``id`` -> node Map.
        build_done_var: JS variable name for the build-completion Promise.

    Returns:
        JS code string.
    """
    return f"""// Scene construction (shared scene-builder)
const {registry_var} = new Map();
const {mesh_map_var} = new Map();
const {build_done_var} = (async () => {{
    for (const obj of {objects_expr}) {{
        if (obj.layer === 'scene') {{
            await buildSceneObject(obj, {scene_var}, {registry_var});
        }} else if (obj.layer === 'overlay') {{
            buildOverlay(obj, {scene_var}, {registry_var});
        }} else if (obj.layer === 'underlay') {{
            // Skip — handled by the coordinate-frame setup (`grid_underlay`).
        }}
    }}
    for (const [id, entry] of {registry_var}) {{
        if (entry.layer === 'scene') {mesh_map_var}.set(id, entry.obj);
    }}
}})();"""


def js_image_assets_hydration(assets_expr: str) -> str:
    """Hydrate ``image-frames.js`` frames from embedded asset data.

    Emits a synchronous loop (run before the scene builds) that decodes each
    asset's base64 bytes and calls ``storeImageFrame``, so
    ``createImage``/``createImageBackground`` can claim the frames via
    ``takeImageFrame``.
    """
    return f"""// Hydrate image pixel frames (raw / jpeg) before the scene builds.
for (const a of ({assets_expr} || [])) {{
    const bytes = Uint8Array.from(atob(a.data_b64), c => c.charCodeAt(0));
    storeImageFrame({{ id: a.id, codec: a.codec, bytes }});
}}"""
