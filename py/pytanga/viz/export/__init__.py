# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Scene export submodule — self-contained HTML and glTF 2.0 binary (``.glb``).

Usage::
    from pytanga.viz.export import render_export_html, build_gltf_scene

    objects = scene.full_state()
    html = render_export_html(objects, scene_config)
    glb_bytes = build_gltf_scene(entities, config)
"""

from ._gltf import build_gltf_scene
from ._html import render_export_html, render_snapshot

__all__ = ["build_gltf_scene", "render_export_html", "render_snapshot"]
