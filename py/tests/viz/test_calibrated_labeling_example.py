# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Validate the bundled calibration + labelme data for the calibrated labeling app."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from pytanga.geometry import Matrix, OpenCVFrame
from pytanga.viz import CalibratedPlaneMapper, CameraCalibration, LabelMeStore

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DATA_DIR = _REPO_ROOT / "py" / "examples" / "viz" / "camera" / "data" / "tless"


def _calibration() -> CameraCalibration:
    data = json.loads((_DATA_DIR / "calibration.json").read_text(encoding="utf-8"))
    return CameraCalibration(
        K=Matrix(data["K"]),
        R=Matrix(data["R_w2c"]),
        t=data["t_w2c"],
        image_size=(int(data["width"]), int(data["height"])),
        frame=OpenCVFrame(),
        units=0.001,
    )


def test_mapper_round_trips_principal_point() -> None:
    mapper = CalibratedPlaneMapper(_calibration(), depth=0.6)
    k = _calibration().K.data
    cx, cy = k[0, 2], k[1, 2]
    u, v = mapper.to_pixel(mapper.to_world(cx, cy))
    assert u == pytest.approx(cx, abs=1e-6)
    assert v == pytest.approx(cy, abs=1e-6)


def test_labels_load_and_map_without_errors() -> None:
    store = LabelMeStore(mapper=CalibratedPlaneMapper(_calibration(), depth=0.6))
    result = store.load(_DATA_DIR / "labels.json")
    assert result.errors == []
    assert len(result.document.shapes) >= 1
    pairs, errors = store.iter_objects(result.document, active=True)
    assert errors == []
    assert len(pairs) == len(result.document.shapes)


def test_calibration_is_valid() -> None:
    calib = _calibration()
    k = calib.K.data
    assert k.shape == (3, 3)
    assert k[0, 0] > 0 and k[1, 1] > 0
    assert np.isclose(k[0, 0], k[1, 1], rtol=0.1)
    assert np.allclose(calib.R.data @ calib.R.data.T, np.eye(3), atol=1e-6)


def test_example_module_imports() -> None:
    import importlib.util

    path = _REPO_ROOT / "py" / "examples" / "apps" / "calibrated_labeling_app.py"
    spec = importlib.util.spec_from_file_location("calibrated_labeling_app", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._DEPTH > 0.0  # noqa: SLF001
