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
