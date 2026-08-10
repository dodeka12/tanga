# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""HTML export logic for Tanga 3D viewer.

Generates a self-contained HTML file by reading the live renderer JS
modules at export time, stripping their ``import`` lines, and concatenating
them.  This eliminates the maintenance burden of a manually-copied bootstrap
script — any changes to the live renderers are automatically picked up.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pytanga.viz.export._bootstrap import (
    generate_bootstrap_js,
    js_annotation_panel,
    js_autofit_camera,
    js_entity_creation,
    js_imports,
    js_label_creation_static,
    js_render_loop,
    js_resize_handler,
    js_scene_setup,
    js_title_overlay,
)
from pytanga.viz.export._bootstrap._html import (
    _CDN_CHECK_SCRIPT,
    _LOADING_OVERLAY_HTML,
)

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def render_export_html(
    entities: list[dict[str, Any]],
    labels: list[dict[str, Any]] | None,
    scene_config: dict[str, Any],
) -> str:
    """Render a self-contained HTML file from entity data and scene config."""
    scene_json = json.dumps({"entities": entities, "labels": labels or []}, indent=0)
    config_json = json.dumps(scene_config, indent=0)

    html = (_TEMPLATES_DIR / "export_viewer.html").read_text(encoding="utf-8")
    bootstrap = generate_bootstrap_js(_build_static_fullpage_adapter(scene_config))

    return (
        html.replace("__CDN_CHECK_SCRIPT__", _CDN_CHECK_SCRIPT)
        .replace("__LOADING_OVERLAY__", _LOADING_OVERLAY_HTML)
        .replace("__SCENE_DATA_JSON__", scene_json)
        .replace("__SCENE_CONFIG_JSON__", config_json)
        .replace("__BOOTSTRAP_JS__", bootstrap)
    )


# ── Bootstrap adapter (composed from shared JS generators) ──


def _build_static_fullpage_adapter(scene_config: dict[str, Any]) -> str:
    """Generate the JS bootstrap adapter for static full-page HTML exports."""
    bg_color = scene_config.get("background_color", "#1a1a2e")
    space_extent = scene_config.get("space_extent", 10)
    space_dim = scene_config.get("space_dim", 3)
    title_raw = scene_config.get("title", "")
    annotation_raw = scene_config.get("annotation", "")

    cam_cfg = scene_config.get("camera") or {}
    cam_pos = cam_cfg.get("position", [8, 6, 10])
    cam_target = cam_cfg.get("target", [0, 0, 0])
    cam_fov = cam_cfg.get("fov", 50)
    cam_near = cam_cfg.get("near", 0.1)
    cam_far = cam_cfg.get("far", 1000)

    parts = [
        "window.__tanga_ready = true;",
        "// ── Bootstrap adapter for Tanga self-contained HTML exports ──",
        "",
        js_imports(),
        "",
        "const sceneData = JSON.parse(document.getElementById('tanga-scene-data').textContent);",
        "const sceneConfig = JSON.parse(document.getElementById('tanga-scene-config').textContent);",
        "const entities = sceneData.entities || [];",
        "const labels = sceneData.labels || [];",
        "",
        js_scene_setup(
            bg_color=bg_color,
            container_expr="document.body",
            append_to="document.body",
            renderer_var="adapterRenderer",
            label_renderer_var="adapterLabelRenderer",
            camera_var="adapterCamera",
            controls_var="adapterControls",
            scene_var="adapterScene",
            width_expr="window.innerWidth",
            height_expr="window.innerHeight",
            cam_fov=cam_fov,
            cam_pos=(cam_pos[0], cam_pos[1], cam_pos[2]),
            cam_target=(cam_target[0], cam_target[1], cam_target[2]),
            cam_near=cam_near,
            cam_far=cam_far,
            auto_rotate=False,
            show_grid=False,
            show_axes=False,
            space_dim=space_dim,
        ),
    ]

    parts.append(
        f"const adapterExtent = sceneConfig.space_extent || {space_extent};\n"
        "if (sceneConfig.show_grid !== false) {\n"
        "    const gs = adapterExtent * 2;\n"
        "    adapterScene.add(new THREE.GridHelper(gs, Math.max(gs, 20), 0x444466, 0x222244));\n"
        "}\n"
        "if (sceneConfig.show_axes !== false) {\n"
        "    adapterScene.add(new THREE.AxesHelper(adapterExtent));\n"
        "}"
    )

    parts.append("")
    parts.append(
        js_title_overlay(
            title=title_raw,
            container_expr="document.body",
            positioning="fixed",
            show_title=bool(title_raw),
        )
    )

    parts.append(
        js_annotation_panel(
            annotation_md=annotation_raw,
            container_expr="document.body",
            positioning="fixed",
            show_annotation=bool(annotation_raw),
        )
    )

    parts.append("")
    parts.append(
        js_entity_creation(
            entities_expr="entities",
            mesh_map_var="meshMap",
            scene_var="adapterScene",
            layer_dispatch=False,
        )
    )

    parts.append("")
    parts.append(
        js_label_creation_static(
            labels_expr="labels",
            mesh_map_var="meshMap",
            scene_var="adapterScene",
        )
    )

    parts.append("")
    parts.append(
        "const adapterCamConfig = sceneConfig.camera;\n"
        "if (adapterCamConfig) {\n"
        "    if (adapterCamConfig.position) adapterCamera.position.set(...adapterCamConfig.position);\n"
        "    if (adapterCamConfig.target) adapterControls.target.set(...adapterCamConfig.target);\n"
        "    if (adapterCamConfig.fov) { adapterCamera.fov = adapterCamConfig.fov; adapterCamera.updateProjectionMatrix(); }\n"
        "    if (adapterCamConfig.near) { adapterCamera.near = adapterCamConfig.near; adapterCamera.updateProjectionMatrix(); }\n"
        "    if (adapterCamConfig.far) { adapterCamera.far = adapterCamConfig.far; adapterCamera.updateProjectionMatrix(); }\n"
        "    adapterControls.update();\n"
        "}\n"
        "if (!adapterCamConfig || (!adapterCamConfig.position && !adapterCamConfig.target)) {"
    )
    parts.append(
        js_autofit_camera(
            mesh_map_var="meshMap",
            camera_var="adapterCamera",
            controls_var="adapterControls",
            cam_explicit=False,
            space_dim=space_dim,
        )
    )
    parts.append(
        "    const _box = new THREE.Box3();\n"
        "    meshMap.forEach(m => _box.expandByObject(m));\n"
        "    if (!_box.isEmpty()) {\n"
        "        const _sz = new THREE.Vector3();\n"
        "        _box.getSize(_sz);\n"
        "        const _d = Math.max(_sz.x, _sz.y, _sz.z, 1) * 1.5 + 2;\n"
        "        if (!adapterCamConfig || !adapterCamConfig.near) adapterCamera.near = Math.max(0.01, _d * 0.001);\n"
        "        if (!adapterCamConfig || !adapterCamConfig.far) adapterCamera.far = _d * 10;\n"
        "        adapterCamera.updateProjectionMatrix();\n"
        "        adapterControls.update();\n"
        "    }\n"
        "}"
    )

    parts.append("")
    parts.append(
        js_render_loop(
            renderer_var="adapterRenderer",
            label_renderer_var="adapterLabelRenderer",
            scene_var="adapterScene",
            camera_var="adapterCamera",
            controls_var="adapterControls",
        )
    )

    parts.append("")
    parts.append(
        js_resize_handler(
            renderer_var="adapterRenderer",
            label_renderer_var="adapterLabelRenderer",
            camera_var="adapterCamera",
            width_expr="window.innerWidth",
            height_expr="window.innerHeight",
        )
    )

    return "\n\n".join(parts)
