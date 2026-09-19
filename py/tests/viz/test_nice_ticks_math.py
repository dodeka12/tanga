# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Node-executed tests for the pure ``nice-ticks.js`` module.

``nice-ticks.js`` is a port of ``py/pytanga/viz/_scale.py`` with no
``three``/DOM dependency, so Node can import it as an ES module.  These tests
pin parity with the Python ``nice_linear_ticks`` / ``log_ticks`` / ``format``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from pytanga.viz._scale import log_ticks, nice_linear_ticks

_REPO_ROOT = Path(__file__).resolve().parents[3]

_NODE_PROGRAM = r"""
import { niceLinearTicks, logTicks, formatValue } from './py/pytanga/viz/templates/nice-ticks.js';
const out = {
    linear: niceLinearTicks(0, 10, 8, '.4g'),
    linearNeg: niceLinearTicks(-5, 5, 8, '.4g'),
    linearZoom: niceLinearTicks(0, 3, 8, '.4g'),
    linearIntervals: niceLinearTicks(0, 1000, 8, '.4g', [50, 200, 500]),
    linearZeroCross: niceLinearTicks(-0.05, 0.05, 11, '.4g', [0.01, 0.02, 0.05]),
    log: logTicks(1, 100, 10, '.4g'),
    logSub: logTicks(0.1, 1000, 10, '.4g'),
    fmtF: formatValue('.2f', 1.5),
    fmtGInt: formatValue('.4g', 100),
    fmtGDec: formatValue('.4g', 0.12345),
    fmtGSci: formatValue('.4g', 10000),
    fmtGTiny: formatValue('.4g', 0.0001),
};
console.log(JSON.stringify(out));
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


def _assert_ticks(got: list, expected: list) -> None:
    assert len(got) == len(expected)
    for (gv, gl), (ev, el) in zip(got, expected, strict=True):
        assert gv == pytest.approx(ev)
        assert gl == el


def test_nice_linear_ticks_parity():  # noqa: ANN201
    out = _run_node()
    _assert_ticks(out["linear"], nice_linear_ticks(0, 10, max_ticks=8, fmt=".4g"))
    _assert_ticks(out["linearNeg"], nice_linear_ticks(-5, 5, max_ticks=8, fmt=".4g"))
    _assert_ticks(out["linearZoom"], nice_linear_ticks(0, 3, max_ticks=8, fmt=".4g"))
    _assert_ticks(
        out["linearIntervals"],
        nice_linear_ticks(0, 1000, max_ticks=8, fmt=".4g", intervals=[50, 200, 500]),
    )
    _assert_ticks(
        out["linearZeroCross"],
        nice_linear_ticks(-0.05, 0.05, max_ticks=11, fmt=".4g", intervals=[0.01, 0.02, 0.05]),
    )


def test_log_ticks_parity():  # noqa: ANN201
    out = _run_node()
    _assert_ticks(out["log"], log_ticks(1, 100, base=10, fmt=".4g"))
    _assert_ticks(out["logSub"], log_ticks(0.1, 1000, base=10, fmt=".4g"))


def test_format_value_parity():  # noqa: ANN201
    out = _run_node()
    assert out["fmtF"] == format(1.5, ".2f")
    assert out["fmtGInt"] == format(100, ".4g")
    assert out["fmtGDec"] == format(0.12345, ".4g")
    assert out["fmtGSci"] == format(10000, ".4g")
    assert out["fmtGTiny"] == format(0.0001, ".4g")


def test_zoom_in_shrinks_step():  # noqa: ANN201
    wide = [v for v, _ in nice_linear_ticks(0, 10, max_ticks=8)]
    narrow = [v for v, _ in nice_linear_ticks(0, 1, max_ticks=8)]
    wide_step = wide[1] - wide[0]
    narrow_step = narrow[1] - narrow[0]
    assert narrow_step < wide_step
