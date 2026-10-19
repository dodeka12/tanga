# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Non-interactive smoke test for the depth surface example."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

from pytanga.viz import DepthImage, DepthImageData
from pytanga.viz._styles import _style_to_output

_REPO_ROOT = Path(__file__).resolve().parents[3]
_EXAMPLE_PATH = _REPO_ROOT / "py" / "examples" / "viz" / "image" / "depth_surface.py"


def _load_example():  # noqa: ANN202
    spec = importlib.util.spec_from_file_location("tanga_depth_surface", _EXAMPLE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_surface_shape_and_range() -> None:
    module = _load_example()
    z = module._surface(64, 48)
    assert z.shape == (48, 64)
    assert z.dtype == np.float32
    assert float(z.min()) >= 0.0
    assert float(z.max()) <= 1.0


def test_color_image_shape() -> None:
    module = _load_example()
    img = module._color_image(64, 48)
    assert img.shape == (48, 64, 3)
    assert img.dtype == np.uint8


def test_positive_negative_segmentations() -> None:
    module = _load_example()
    pos = module._positive_segmentation(64, 48)
    neg = module._negative_segmentation(64, 48)
    assert pos.shape == (48, 64)
    assert neg.shape == (48, 64)
    assert set(np.unique(pos).tolist()) <= {0, 1}
    assert set(np.unique(neg).tolist()) <= {0, 1}
    # Both regions occur, and they never overlap (positive vs. negative sign).
    assert int(pos.sum()) > 0
    assert int(neg.sum()) > 0
    assert not bool((pos & neg).any())


def test_build_depth_image_entity() -> None:
    module = _load_example()
    data = DepthImageData(
        image=module._color_image(64, 48),
        depth=module._surface(32, 24),
        segmentation=module._positive_segmentation(32, 24),
    )
    content, frames = DepthImage(data)._build(
        _style_to_output(None, "DepthImage"), "d0"
    )
    # depth is transmitted at its own resolution (one sample per mesh vertex).
    assert content["depth"]["width"] == 32
    assert content["segmentation"] is not None
    assert len(frames) == 3
