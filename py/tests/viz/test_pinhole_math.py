# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Node-executed tests for the pure ``pinhole-framing.js`` math.

``pinhole-framing.js`` has no ``three``/DOM dependency, so Node can import it as
an ES module and exercise ``pinholeFraming`` directly.  These tests pin the
off-center frustum bounds (``fit="fill"``) and the letterbox behaviour
(``fit="fit"``) by projecting known camera-space points and checking the
recovered pixel/NDC coordinates.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_node_program(program: str) -> dict:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not available")
    proc = subprocess.run(
        [node, "--input-type=module", "-e", program],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_pinhole_framing_fill_pixel_mapping() -> None:
    program = r"""
    import { pinholeFraming } from './py/pytanga/viz/templates/pinhole-framing.js';

    function project(f, X, Y, Z, W, H) {
        const l = f.left, r = f.right, t = f.top, b = f.bottom, n = f.near;
        const clipX = (2 * n / (r - l)) * X + ((r + l) / (r - l)) * Z;
        const clipY = (2 * n / (t - b)) * Y + ((t + b) / (t - b)) * Z;
        const w = -Z;
        return { u: (clipX / w + 1) / 2 * W, v: (1 - clipY / w) / 2 * H };
    }

    const f = pinholeFraming(500, 500, 320, 240, 640, 480, 1, 100, 640/480, 'fill');
    // OpenCV camera point (Xc, Yc, Zc) -> Three.js camera (Xc, -Yc, -Zc).
    console.log(JSON.stringify([
        project(f, 100, -50, -200, 640, 480),  // (100, 50, 200) -> (570, 365)
        project(f, 0, 0, -200, 640, 480),      // principal ray   -> (320, 240)
    ]));
    """
    results = _run_node_program(program)
    assert results[0]["u"] == pytest.approx(570.0)
    assert results[0]["v"] == pytest.approx(365.0)
    assert results[1]["u"] == pytest.approx(320.0)
    assert results[1]["v"] == pytest.approx(240.0)


def test_pinhole_framing_fill_bounds() -> None:
    program = (
        "import { pinholeFraming } from './py/pytanga/viz/templates/pinhole-framing.js';\n"
        "console.log(JSON.stringify(pinholeFraming(500, 500, 320, 240, 640, 480, 1, 100, 2.0, 'fill')));"
    )
    f = _run_node_program(program)
    assert f["left"] == pytest.approx(-320 / 500)
    assert f["right"] == pytest.approx((640 - 320) / 500)
    assert f["top"] == pytest.approx(240 / 500)
    assert f["bottom"] == pytest.approx(-(480 - 240) / 500)
    assert f["hx"] == 1
    assert f["hy"] == 1


def test_pinhole_framing_fit_wide_pane() -> None:
    # image 640x480 (A=1.333) in a 2.0-aspect pane: expand horizontal by 1.5.
    program = (
        "import { pinholeFraming } from './py/pytanga/viz/templates/pinhole-framing.js';\n"
        "console.log(JSON.stringify(pinholeFraming(500, 500, 320, 240, 640, 480, 1, 100, 2.0, 'fit')));"
    )
    f = _run_node_program(program)
    assert f["left"] == pytest.approx(-0.96)
    assert f["right"] == pytest.approx(0.96)
    assert f["top"] == pytest.approx(0.48)
    assert f["bottom"] == pytest.approx(-0.48)
    assert f["hx"] == pytest.approx(640 / 480 / 2.0)
    assert f["hy"] == 1


def test_pinhole_framing_fit_tall_pane() -> None:
    # image 640x480 (A=1.333) in a 0.5-aspect pane: expand vertical by 2.667.
    program = (
        "import { pinholeFraming } from './py/pytanga/viz/templates/pinhole-framing.js';\n"
        "console.log(JSON.stringify(pinholeFraming(500, 500, 320, 240, 640, 480, 1, 100, 0.5, 'fit')));"
    )
    f = _run_node_program(program)
    assert f["left"] == pytest.approx(-0.64)
    assert f["right"] == pytest.approx(0.64)
    assert f["top"] == pytest.approx(1.28)
    assert f["bottom"] == pytest.approx(-1.28)
    assert f["hx"] == 1
    assert f["hy"] == pytest.approx(0.5 / (640 / 480))

def test_pinhole_framing_crop_window() -> None:
    program = r"""
    import { pinholeFraming } from './py/pytanga/viz/templates/pinhole-framing.js';
    const base = [500, 500, 320, 240, 640, 480, 1, 100, 640/480, 'fill'];
    const full = pinholeFraming(...base, null);
    const zoom2 = pinholeFraming(...base, { zoom: 2, pan: [0, 0] });
    const pan = pinholeFraming(...base, { zoom: 2, pan: [0.5, 0] });
    const overpan = pinholeFraming(...base, { zoom: 2, pan: [1.0, 0] });
    console.log(JSON.stringify({ full, zoom2, pan, overpan }));
    """
    r = _run_node_program(program)
    full, zoom2, pan, overpan = r["full"], r["zoom2"], r["pan"], r["overpan"]

    # No crop: full image, frustum unchanged, full-image crop rect.
    assert full["crop"] == {"u0": 0, "v0": 0, "u1": 1, "v1": 1}
    assert full["left"] == pytest.approx(-0.64)
    assert full["right"] == pytest.approx(0.64)
    assert full["top"] == pytest.approx(0.48)
    assert full["bottom"] == pytest.approx(-0.48)

    # zoom=2 centred: frustum span halves, crop is the central quarter.
    assert zoom2["crop"] == {"u0": 0.25, "v0": 0.25, "u1": 0.75, "v1": 0.75}
    assert zoom2["left"] == pytest.approx(-0.32)
    assert zoom2["right"] == pytest.approx(0.32)
    assert zoom2["top"] == pytest.approx(0.24)
    assert zoom2["bottom"] == pytest.approx(-0.24)

    # pan right (pan=[0.5, 0]) at zoom=2: crop shifts toward the right edge.
    assert pan["crop"] == {"u0": 0.5, "v0": 0.25, "u1": 1.0, "v1": 0.75}
    assert pan["left"] == pytest.approx(0.0)
    assert pan["right"] == pytest.approx(0.64)
    assert pan["top"] == pytest.approx(0.24)
    assert pan["bottom"] == pytest.approx(-0.24)

    # Over-pan clamps to the image edge *without* shrinking the crop window.
    assert overpan["crop"] == {"u0": 0.5, "v0": 0.25, "u1": 1.0, "v1": 0.75}
    assert overpan["left"] == pytest.approx(0.0)
    assert overpan["right"] == pytest.approx(0.64)


def test_pinhole_framing_fit_crop_window_grows() -> None:
    # image 640x480 (A=1.333) in a square (1.0) pane: zooming must grow the
    # image to fill the pane (hx/hy → 1) instead of pinning the fit region.
    program = r"""
    import { pinholeFraming } from './py/pytanga/viz/templates/pinhole-framing.js';
    const base = [500, 500, 320, 240, 640, 480, 1, 100, 1.0, 'fit'];
    const z1 = pinholeFraming(...base, { zoom: 1, pan: [0, 0] });
    const z2 = pinholeFraming(...base, { zoom: 2, pan: [0, 0] });
    const z4 = pinholeFraming(...base, { zoom: 4, pan: [0, 0] });
    console.log(JSON.stringify({ z1, z2, z4 }));
    """
    r = _run_node_program(program)
    z1, z2, z4 = r["z1"], r["z2"], r["z4"]

    # zoom=1: full image, fit letterbox (image taller than the square pane).
    assert z1["crop"] == {"u0": 0, "v0": 0, "u1": 1, "v1": 1}
    assert z1["hx"] == 1
    assert z1["hy"] == pytest.approx(0.75)
    assert z1["fitHx"] == 1
    assert z1["fitHy"] == pytest.approx(0.75)

    # zoom=2: the image fills the pane (no letterbox).
    assert z2["crop"]["u0"] == pytest.approx(0.25)
    assert z2["crop"]["u1"] == pytest.approx(0.75)
    assert z2["crop"]["v0"] == pytest.approx(1 / 6)
    assert z2["crop"]["v1"] == pytest.approx(5 / 6)
    assert z2["hx"] == pytest.approx(1)
    assert z2["hy"] == pytest.approx(1)
    assert z2["left"] == pytest.approx(-0.32)
    assert z2["right"] == pytest.approx(0.32)
    assert z2["top"] == pytest.approx(0.32)
    assert z2["bottom"] == pytest.approx(-0.32)

    # zoom=4: pane-shaped crop window, still filling the pane.
    assert z4["crop"]["u0"] == pytest.approx(0.375)
    assert z4["crop"]["u1"] == pytest.approx(0.625)
    assert z4["crop"]["v0"] == pytest.approx(1 / 3)
    assert z4["crop"]["v1"] == pytest.approx(2 / 3)
    assert z4["hx"] == pytest.approx(1)
    assert z4["hy"] == pytest.approx(1)
    assert z4["left"] == pytest.approx(-0.16)
    assert z4["right"] == pytest.approx(0.16)
    assert z4["top"] == pytest.approx(0.16)
    assert z4["bottom"] == pytest.approx(-0.16)
