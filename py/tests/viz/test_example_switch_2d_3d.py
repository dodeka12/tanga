# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Non-interactive smoke test for the 2D/3D switch example."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_EXAMPLE_PATH = _REPO_ROOT / "py" / "examples" / "viz" / "camera" / "switch_2d_3d.py"


def _load_example():
    spec = importlib.util.spec_from_file_location(
        "tanga_example_switch_2d_3d", _EXAMPLE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_switch_2d_3d_example_constructs_and_switches():
    module = _load_example()
    viz = module.viz

    # The plot scene starts in 2D with the CoordinateSystem's fitted 2D camera.
    assert viz._scenes["plot"].config.space_dim == 2
    assert viz._scenes["plot"].config.camera is not None
    assert viz._scenes["plot"].config.camera.type == "2d"

    # The checkbox handler's 3D camera is a View3dConfig (tilted perspective).
    assert module.cam_3d.normal == (0.3, 0.4, 1.0)

    # Switching flips the scene dimension and swaps in the matching camera.
    viz.set_space_dim(3, scene_name="plot", camera=module.cam_3d)
    assert viz._scenes["plot"].config.space_dim == 3
    assert viz._scenes["plot"].config.camera.type == "3d"

    viz.set_space_dim(2, scene_name="plot", camera=module.cam_2d)
    assert viz._scenes["plot"].config.space_dim == 2
    assert viz._scenes["plot"].config.camera.type == "2d"
