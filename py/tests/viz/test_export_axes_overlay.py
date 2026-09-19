# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Export regression tests for the overlay coordinate system.

Ensures a `CoordinateSystem(display_mode="overlay")` scene serializes its
`axes_overlay` + `grid_underlay` objects and that the exported HTML (inline
delivery) wires the frame/grid renderers + per-frame update.
"""

from __future__ import annotations

from pytanga.viz import CoordinateSystem, Visualizer
from pytanga.viz.export._figure_html import render_figure
from pytanga.viz.export._html import render_snapshot


def _overlay_scene():  # noqa: ANN202
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    CoordinateSystem(viz, display_mode="overlay", xlim=(0, 10), ylim=(0, 4))
    return viz._scenes[""]


def test_snapshot_contains_overlay_specs_and_wiring():  # noqa: ANN201
    s = _overlay_scene()
    html = render_snapshot(s.full_state(), s.config.to_dict(), delivery="inline")
    assert "axes_overlay" in html
    assert "grid_underlay" in html
    assert "updateCoordinateOverlays" in html
    assert "class AxesOverlay" in html
    assert "class GridUnderlay" in html


def test_figure_contains_overlay_wiring():  # noqa: ANN201
    s = _overlay_scene()
    html = render_figure(
        s.full_state(),
        s.config.to_dict(),
        {"width": 400, "height": 300, "responsive": True},
        {"title": "T"},
        delivery="inline",
    )
    assert "axes_overlay" in html
    assert "grid_underlay" in html
    assert "updateCoordinateOverlays" in html
