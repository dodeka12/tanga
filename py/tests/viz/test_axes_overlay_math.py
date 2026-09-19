# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Node-executed tests for the pure ``axes-overlay-math.js`` module.

Verifies the ortho world-rect extraction, the world↔data scale mapping, and the
screen-space tick/px layout used by the axes overlay and grid underlay.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]

_NODE_PROGRAM = r"""
import { visibleWorldRect, worldToData, ticksAndGrid } from './py/pytanga/viz/templates/axes-overlay-math.js';
const rect = visibleWorldRect({ left: -5, right: 5, top: 5, bottom: -5, zoom: 1, x: 0, y: 0 });
const rectZoom = visibleWorldRect({ left: -5, right: 5, top: 5, bottom: -5, zoom: 2, x: 3, y: -1 });
const linear = worldToData({ xmin: 0, xmax: 10, ymin: 0, ymax: 4 }, { xscale: 'linear', yscale: 'linear', base: 10 });
const log = worldToData({ xmin: -1, xmax: 2, ymin: 0, ymax: 2 }, { xscale: 'log', yscale: 'log', base: 10 });
const grid = ticksAndGrid(
    { xmin: 0, xmax: 10, ymin: 0, ymax: 4 },
    { xscale: 'linear', yscale: 'linear', base: 10, value_format: '.4g' },
    { width: 100, height: 40 }
);
console.log(JSON.stringify({ rect, rectZoom, linear, log, grid }));
"""


def _run_node() -> dict:
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


def test_visible_world_rect():  # noqa: ANN201
    out = _run_node()
    assert out["rect"] == {"xmin": -5, "xmax": 5, "ymin": -5, "ymax": 5}
    assert out["rectZoom"]["xmin"] == pytest.approx(0.5)
    assert out["rectZoom"]["xmax"] == pytest.approx(5.5)
    assert out["rectZoom"]["ymin"] == pytest.approx(-3.5)
    assert out["rectZoom"]["ymax"] == pytest.approx(1.5)


def test_world_to_data_linear():  # noqa: ANN201
    out = _run_node()
    assert out["linear"] == {"xlo": 0, "xhi": 10, "ylo": 0, "yhi": 4}


def test_world_to_data_log():  # noqa: ANN201
    out = _run_node()
    assert out["log"]["xlo"] == pytest.approx(0.1)
    assert out["log"]["xhi"] == pytest.approx(100)
    assert out["log"]["ylo"] == pytest.approx(1)
    assert out["log"]["yhi"] == pytest.approx(100)


def test_ticks_and_grid_px():  # noqa: ANN201
    out = _run_node()
    x_ticks = out["grid"]["xTicks"]
    y_ticks = out["grid"]["yTicks"]
    # Tick density is now derived from the viewport (min 60px spacing), so the
    # exact tick count varies; the endpoints always map to the viewport edges.
    # x spans 0..10 across width 100: 0 → 0 px, 10 → 100 px.
    assert x_ticks[0][2] == pytest.approx(0)
    assert x_ticks[-1][2] == pytest.approx(100)
    # y is top-down: world ymin (0) → height (40) px, world ymax (4) → 0 px.
    assert y_ticks[0][2] == pytest.approx(40)
    assert y_ticks[-1][2] == pytest.approx(0)


def test_world_to_screen_center():  # noqa: ANN201
    # A symmetric ortho world rect maps its centre to the viewport centre —
    # this is the full-viewport mapping the overlay grid/ticks rely on, since
    # overlay mode uses `stretch="fill"` (no letterbox).
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not available")
    program = (
        "import { worldToScreen } from "
        "'./py/pytanga/viz/templates/axes-overlay-math.js';\n"
        "console.log(JSON.stringify(worldToScreen("
        "{ xmin: -3.395, xmax: 3.395, ymin: -1.73, ymax: 1.73 }, 0, 0, 1600, 900)));\n"
    )
    proc = subprocess.run(
        [node, "--input-type=module", "-e", program],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    p = json.loads(proc.stdout)
    assert p["x"] == pytest.approx(800)
    assert p["y"] == pytest.approx(450)
