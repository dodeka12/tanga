# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Validate the bundled T-LESS calibration data for the pinhole example."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DATA_DIR = _REPO_ROOT / "py" / "examples" / "viz" / "camera" / "data" / "tless"


def _load() -> dict:
    return json.loads((_DATA_DIR / "calibration.json").read_text(encoding="utf-8"))


def _is_rotation(m: np.ndarray) -> bool:
    """True when *m* is a 3×3 proper rotation (orthonormal, det ≈ +1)."""
    return bool(np.allclose(m @ m.T, np.eye(3), atol=1e-6)) and bool(
        np.isclose(np.linalg.det(m), 1.0, atol=1e-6)
    )


def test_calibration_json_shape():  # noqa: ANN201
    d = _load()
    k = np.asarray(d["K"], dtype=float)
    assert k.shape == (3, 3)
    fx, fy = k[0, 0], k[1, 1]
    assert fx > 0 and fy > 0
    assert np.isclose(fx, fy, rtol=0.1)  # square-ish pixels
    assert np.asarray(d["R_w2c"]).shape == (3, 3)
    assert np.asarray(d["t_w2c"]).shape == (3,)
    assert np.asarray(d["cam_R_m2c"]).shape == (3, 3)
    assert np.asarray(d["cam_t_m2c"]).shape == (3,)
    assert np.asarray(d["bbox_min"]).shape == (3,)
    assert np.asarray(d["bbox_size"]).shape == (3,)
    assert all(s > 0 for s in d["bbox_size"])


def test_rotation_matrices_orthonormal():  # noqa: ANN201
    d = _load()
    assert _is_rotation(np.asarray(d["R_w2c"], dtype=float))
    assert _is_rotation(np.asarray(d["cam_R_m2c"], dtype=float))


def test_image_matches_declared_size():  # noqa: ANN201
    d = _load()
    img_path = _DATA_DIR / d["image"]
    assert img_path.exists()
    with Image.open(img_path) as img:
        img.load()
        assert (img.width, img.height) == (d["width"], d["height"])
        assert img.mode == "RGB"


def test_gt_object_projects_into_image():  # noqa: ANN201
    """The GT bounding-box centre must project into the image (sanity check)."""
    d = _load()
    k = np.asarray(d["K"], dtype=float)
    r_w2c = np.asarray(d["R_w2c"], dtype=float)
    t_w2c = np.asarray(d["t_w2c"], dtype=float)
    r_m2c = np.asarray(d["cam_R_m2c"], dtype=float)
    t_m2c = np.asarray(d["cam_t_m2c"], dtype=float)

    # Object centre in model coords = bbox_min + bbox_size / 2; map to world,
    # then to camera (world → camera), then project through K.
    model_centre = np.asarray(d["bbox_min"]) + np.asarray(d["bbox_size"]) / 2.0
    r_m2w = r_w2c.T @ r_m2c
    t_m2w = r_w2c.T @ (t_m2c - t_w2c)
    cam = r_w2c @ (r_m2w @ model_centre + t_m2w) + t_w2c
    uv = k @ cam
    u, v = uv[0] / uv[2], uv[1] / uv[2]
    assert 0.0 <= u < d["width"]
    assert 0.0 <= v < d["height"]
