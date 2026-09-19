# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Node-executed tests for the pure ``camera-fit.js`` ortho-frustum math.

``camera-fit.js`` has no ``three``/DOM dependency, so Node can import it as an
ES module and exercise ``orthoFrustum`` directly.  These tests pin the four
``stretch`` modes (``fit`` / ``fill`` / ``fill_x`` / ``fill_y``).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]

_NODE_PROGRAM = r"""
import { orthoFrustum } from './py/pytanga/viz/templates/camera-fit.js';
const cases = [
    // Wide rectangle (x is the limiting axis): 10x4 in a 1000x700 viewport.
    [0, 10, 0, 4, 'fit',    0, 1000, 700],
    [0, 10, 0, 4, 'fill',   0, 1000, 700],
    [0, 10, 0, 4, 'fill_x', 0, 1000, 700],
    [0, 10, 0, 4, 'fill_y', 0, 1000, 700],
    // Tall rectangle (y is the limiting axis): 4x10 in a 700x1000 viewport.
    [0, 4, 0, 10, 'fit',    0, 700, 1000],
    [0, 4, 0, 10, 'fill',   0, 700, 1000],
    [0, 4, 0, 10, 'fill_x', 0, 700, 1000],
    [0, 4, 0, 10, 'fill_y', 0, 700, 1000],
];
console.log(JSON.stringify(cases.map(c => orthoFrustum(...c))));
"""


def _run_node() -> list[dict]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not available")
    proc = subprocess.run(
        [node, "--input-type=module", "-e", _NODE_PROGRAM],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_ortho_frustum_stretch_modes() -> None:
    results = _run_node()
    fit_w, fill_w, fillx_w, filly_w, fit_t, fill_t, fillx_t, filly_t = results

    # Wide rectangle: x fills, y is letterboxed/derived.
    assert fit_w == {"left": -5.0, "right": 5.0, "top": 3.5, "bottom": -3.5}
    assert fill_w == {"left": -5.0, "right": 5.0, "top": 2.0, "bottom": -2.0}
    # x is the limiting axis here, so fill_x coincides with fit.
    assert fillx_w == fit_w
    # fill_y forces y to fill the content height; x keeps aspect (20/7 ≈ 2.857).
    assert filly_w["top"] == pytest.approx(2.0)
    assert filly_w["bottom"] == pytest.approx(-2.0)
    assert filly_w["left"] == pytest.approx(-20 / 7)
    assert filly_w["right"] == pytest.approx(20 / 7)

    # Tall rectangle: y fills, x is letterboxed/derived.
    assert fit_t == {"left": -3.5, "right": 3.5, "top": 5.0, "bottom": -5.0}
    assert fill_t == {"left": -2.0, "right": 2.0, "top": 5.0, "bottom": -5.0}
    # fill_x forces x to fill the content width; y keeps aspect (40/7 ≈ 5.714).
    assert fillx_t["left"] == pytest.approx(-2.0)
    assert fillx_t["right"] == pytest.approx(2.0)
    assert fillx_t["top"] == pytest.approx(20 / 7)
    assert fillx_t["bottom"] == pytest.approx(-20 / 7)
    # y is the limiting axis here, so fill_y coincides with fit.
    assert filly_t == fit_t


def test_ortho_frustum_unknown_mode_falls_back_to_fit() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not available")
    program = (
        "import { orthoFrustum } from './py/pytanga/viz/templates/camera-fit.js';\n"
        "console.log(JSON.stringify(orthoFrustum(0, 10, 0, 4, 'bogus', 0, 1000, 700)));"
    )
    proc = subprocess.run(
        [node, "--input-type=module", "-e", program],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result == {"left": -5.0, "right": 5.0, "top": 3.5, "bottom": -3.5}


def test_clamp_ortho_view() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not available")
    program = r"""
    import { clampOrthoView } from './py/pytanga/viz/templates/camera-fit.js';
    const camera = {
        position: { x: 100, y: -50 },
        zoom: 0.25,
        userData: { _view2d: {
            xmin: -5, xmax: 5, ymin: -2, ymax: 2,
            pan_xmin: -8, pan_xmax: 8, pan_ymin: -4, pan_ymax: 4,
            min_zoom: 1, max_zoom: 10,
        } },
        updateProjectionMatrix() { this._updated = true; },
    };
    const controls = { target: { x: 100, y: -50 } };
    clampOrthoView(camera, controls);
    console.log(JSON.stringify({ camera, controls }));
    """
    proc = subprocess.run(
        [node, "--input-type=module", "-e", program],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    # Position clamped to pan bounds; zoom clamped to [min, max]; controls synced.
    assert out["camera"]["position"] == {"x": 8, "y": -4}
    assert out["camera"]["zoom"] == 1
    assert out["camera"]["_updated"] is True
    assert out["controls"]["target"] == {"x": 8, "y": -4}


def test_clamp_ortho_view_defaults_pan_to_data_bounds() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not available")
    program = r"""
    import { clampOrthoView } from './py/pytanga/viz/templates/camera-fit.js';
    const camera = {
        position: { x: 99, y: 0 },
        zoom: 5,
        userData: { _view2d: { xmin: -5, xmax: 5, ymin: -2, ymax: 2 } },
        updateProjectionMatrix() {},
    };
    clampOrthoView(camera, null);
    console.log(JSON.stringify(camera));
    """
    proc = subprocess.run(
        [node, "--input-type=module", "-e", program],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    # Pan defaults to data bounds; zoom defaults to min 1 (max Infinity).
    assert out["position"]["x"] == 5
    assert out["zoom"] == 5


def test_clamp_ortho_view_derives_min_zoom_for_overflow() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not available")
    program = r"""
    import { clampOrthoView } from './py/pytanga/viz/templates/camera-fit.js';
    const results = [];
    const run = (camera) => { clampOrthoView(camera, null); return camera.zoom; };

    // fill_x-style: x fills, y overflows (spanY/extY < 1) → min zoom < 1.
    const overflow = {
        position: { x: 0, y: 0 }, zoom: 0.5,
        left: -6, right: 6, top: 6, bottom: -6,
        userData: { _view2d: { xmin: -5, xmax: 5, ymin: -25, ymax: 25 } },
        updateProjectionMatrix() {},
    };
    // spanX = 12, extX = 10 → 1.2; spanY = 12, extY = 50 → 0.24 → min 0.24.
    results.push(run(overflow));  // 0.5 is within [0.24, Inf] → unchanged
    overflow.zoom = 0.1;
    results.push(run(overflow));  // 0.1 < 0.24 → clamped up to 0.24

    // fit/fill-style: data contained (spans >= extents) → min zoom capped at 1.
    const contained = {
        position: { x: 0, y: 0 }, zoom: 0.5,
        left: -10, right: 10, top: 10, bottom: -10,
        userData: { _view2d: { xmin: -5, xmax: 5, ymin: -2, ymax: 2 } },
        updateProjectionMatrix() {},
    };
    results.push(run(contained));  // 0.5 < 1 → clamped up to 1

    console.log(JSON.stringify(results));
    """
    proc = subprocess.run(
        [node, "--input-type=module", "-e", program],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out[0] == pytest.approx(0.5)
    assert out[1] == pytest.approx(0.24)
    assert out[2] == pytest.approx(1.0)
