# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Non-interactive smoke test for the ``py/examples/viz/app`` split-view example."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_EXAMPLE_PATH = _REPO_ROOT / "py" / "examples" / "viz" / "app" / "split_view_app.py"


def _load_example():
    spec = importlib.util.spec_from_file_location(
        "tanga_example_split_view_app", _EXAMPLE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_split_view_app_constructs_and_initialises():
    app_module = _load_example()
    app = app_module.SplitViewApp()

    viz = app.viz
    assert viz._scenes[""].config.space_dim == 2
    assert viz._scenes["sin"].config.space_dim == 2
    assert viz._scenes["cos"].config.space_dim == 2

    # The plot scenes opt out of the default grid/axes (they draw their own).
    for name in ("sin", "cos"):
        kinds = {o.kind for o in viz._scenes[name]._objects.values()}
        assert "Grid" not in kinds
        assert "Axes2D" not in kinds
        assert "Axes3D" not in kinds

    asyncio.run(app.init())

    assert app._amp is not None
    assert len(app._points) == 4
    assert len(app._lines) == 4
    # Exactly one interactive object in the sin pane (the amplitude point) and
    # four in the main pane (the polygon corners).
    assert len(viz._scenes["sin"]._interaction_configs) == 1
    assert len(viz._scenes[""]._interaction_configs) == 4
