# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Validate the multi-layer image example (`py/examples/viz/image/image_layers.py`)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

_REPO_ROOT = Path(__file__).resolve().parents[3]
_EXAMPLE_PATH = _REPO_ROOT / "py" / "examples" / "viz" / "image" / "image_layers.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("image_layers_example", _EXAMPLE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_example_module_imports() -> None:
    module = _load_module()
    assert module._IMAGE_W > 0  # noqa: SLF001
    assert module._BLEND_CODES["add"] is module.LayerBlendMode.ADD  # noqa: SLF001


def test_example_builds_layers_and_layout() -> None:
    module = _load_module()
    _viz, canvas, layout = module.build()

    assert [img.id for img in canvas.image_view.images] == ["rgb", "depth", "seg"]
    # The RGB base is visible; depth + segmentation start disabled at half opacity.
    assert canvas.image_view.uniforms["u_layer0_enabled"] == 1
    assert canvas.image_view.uniforms["u_layer1_enabled"] == 0
    assert canvas.image_view.uniforms["u_layer2_enabled"] == 0
    assert canvas.image_view.uniforms["u_layer2_opacity"] == 0.5
    assert layout is not None
