# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the animated-export frame pump (serialized frame application).

The render loop shape is a Python-emitted JS string, so these tests guard the
emitted contract; the pump itself is unit-tested by
``js/dev/tests/frame-pump.test.mjs`` and the behaviour is covered by
``js/dev/tests/anim-export-smoke.mjs``.
"""

from __future__ import annotations

import re

from pytanga.viz.export._bootstrap._animation import (
    js_animated_render_loop,
    js_frame_pump,
)
from pytanga.viz.export._bootstrap._html import (
    _TEMPLATES_DIR,
    generate_library_js,
)
from pytanga.viz.export._bootstrap._scene import (
    js_tanga_bridge,
    js_tanga_destructure,
)


def test_render_loop_is_non_async_and_requests_frames():  # noqa: ANN201
    """``_figAnimate`` requests frames and never awaits ``_playFrame``."""
    js = js_animated_render_loop(fps=30, scene_var="figScene")
    assert "async function _figAnimate" not in js
    assert "await _playFrame(" not in js
    assert "requestAnimationFrame(_figAnimate)" in js
    assert "_requestFrame(" in js


def test_frame_pump_declarations():  # noqa: ANN201
    js = js_frame_pump()
    assert "createFramePump(_playFrame)" in js
    assert "function _requestFrame(" in js


def test_frame_pump_is_a_bridge_symbol_and_bundled():  # noqa: ANN201
    assert "createFramePump" in js_tanga_bridge()
    assert "createFramePump" in js_tanga_destructure()
    lib = generate_library_js()
    # `export` is stripped from shared modules in the inline bundle.
    assert "function createFramePump(" in lib


def test_frame_pump_module_is_pure():  # noqa: ANN201
    """The module must have no imports and only its one `export` keyword."""
    source = (_TEMPLATES_DIR / "frame-pump.js").read_text(encoding="utf-8")
    assert re.search(r"^\s*import\b", source, re.MULTILINE) is None
    exports = re.findall(r"^export\s+", source, re.MULTILINE)
    assert exports == ["export "]
