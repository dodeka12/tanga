# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Scene export submodule — self-contained HTML and glTF 2.0 binary (``.glb``).

Usage::
    from pytanga.viz.export import render_export_html, build_gltf_scene

    html = render_export_html(entities, labels, scene_config)
    glb_bytes = build_gltf_scene(entities, config, labels=labels)
"""

from ._gltf import build_gltf_scene
from ._html import render_export_html

__all__ = ["build_gltf_scene", "render_export_html"]
