# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Validate the bundled calibration + labelme data for the calibrated labeling app."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from pytanga.geometry import Matrix, OpenCVFrame
from pytanga.viz import (
    CalibratedPlaneMapper,
    CameraCalibration,
    DragEvent,
    LabelMeStore,
    LabelShape,
    ModifierKey,
    PlanarMapper,
    Visualizer,
)

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


def test_mapper_world_units_per_pixel() -> None:
    assert PlanarMapper().world_units_per_pixel() == 1.0
    calib = _calibration()
    mapper = CalibratedPlaneMapper(calib, depth=0.6)
    assert mapper.world_units_per_pixel() == pytest.approx(0.6 / calib.K.data[0, 0])


def test_labels_load_and_map_without_errors() -> None:
    store = LabelMeStore(mapper=CalibratedPlaneMapper(_calibration(), depth=0.6))
    result = store.load(_DATA_DIR / "labels.json")
    assert result.errors == []
    assert len(result.document.shapes) >= 1
    pairs, errors = store.iter_objects(result.document)
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
    """The example module imports (surface-backed labeler wiring)."""
    import importlib.util

    path = _REPO_ROOT / "py" / "examples" / "apps" / "calibrated_labeling_app.py"
    spec = importlib.util.spec_from_file_location("calibrated_labeling_app", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._DEPTH > 0  # noqa: SLF001
    assert module._CalibratedLabeler is not None  # noqa: SLF001


def test_labeler_pixel_scale_from_mapper() -> None:
    """The calibrated labeler derives `pixel_scale` from the mapper (depth/fx)."""
    import importlib.util

    path = _REPO_ROOT / "py" / "examples" / "apps" / "calibrated_labeling_app.py"
    spec = importlib.util.spec_from_file_location("calibrated_labeling_app", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    calib = _calibration()
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=3)
    world = viz.scene("world")
    labeler = module._CalibratedLabeler(world, calib, 0.6)  # noqa: SLF001
    assert labeler._pixel_scale == pytest.approx(0.6 / calib.K.data[0, 0])  # noqa: SLF001


def _load_example() -> Any:
    import importlib.util

    path = _REPO_ROOT / "py" / "examples" / "apps" / "calibrated_labeling_app.py"
    spec = importlib.util.spec_from_file_location("calibrated_labeling_app", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_labeler(module: Any) -> Any:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=3)
    world = viz.scene("world")
    return module._CalibratedLabeler(world, _calibration(), 0.6)  # noqa: SLF001


def _make_labeler_with_viz(module: Any) -> tuple[Any, Any]:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=3)
    world = viz.scene("world")
    labeler = module._CalibratedLabeler(world, _calibration(), 0.6)  # noqa: SLF001
    return viz, labeler


def test_selection_is_exclusive() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    rect = module.ActRectangle2D(center=module.Point(1.0, 1.0, 0.0), size=(1.0, 1.0))
    circle = module.ActCircle(center=module.Point(2.0, 2.0, 0.0), radius=0.5)
    labeler._add_shape(rect, module._style_for("rect", "#ff4444"))  # noqa: SLF001
    labeler._add_shape(circle, module._style_for("circle", "#ff4444"))  # noqa: SLF001

    labeler._select(rect)  # noqa: SLF001
    assert labeler.selected is rect
    labeler._select(circle)  # noqa: SLF001
    assert labeler.selected is circle
    labeler._deselect()  # noqa: SLF001
    assert labeler.selected is None


def test_handles_follow_active_type() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    rect = module.ActRectangle2D(center=module.Point(1.0, 1.0, 0.0), size=(1.0, 1.0))
    circle = module.ActCircle(center=module.Point(2.0, 2.0, 0.0), radius=0.5)
    labeler._add_shape(rect, module._style_for("rect", "#ff4444"))  # noqa: SLF001
    labeler._add_shape(circle, module._style_for("circle", "#ff4444"))  # noqa: SLF001

    # No mode → every composite handle is disabled.
    assert all(h._enabled is False for h in rect._all_handles())  # noqa: SLF001
    assert all(h._enabled is False for h in circle._all_handles())  # noqa: SLF001

    # Rect mode → only rectangle handles are enabled.
    labeler.set_mode("rect")
    assert all(h._enabled is True for h in rect._all_handles())  # noqa: SLF001
    assert all(h._enabled is False for h in circle._all_handles())  # noqa: SLF001

    # Circle mode → only circle handles are enabled.
    labeler.set_mode("circle")
    assert all(h._enabled is False for h in rect._all_handles())  # noqa: SLF001
    assert all(h._enabled is True for h in circle._all_handles())  # noqa: SLF001


def test_point_gated_by_point_mode() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    point = module.ActPoint(module.Point(1.0, 1.0, 0.0))
    labeler._add_shape(point, module._style_for("point", "#ff4444"))  # noqa: SLF001

    # No mode → point disabled (but still visible).
    assert point._enabled is False  # noqa: SLF001

    # Point mode → point enabled.
    labeler.set_mode("point")
    assert point._enabled is True  # noqa: SLF001

    # Rect mode → point disabled again.
    labeler.set_mode("rect")
    assert point._enabled is False  # noqa: SLF001


def test_add_shape_applies_pixel_scale_before_spawning_handles() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    ellipse = module.ActEllipse(
        center=module.Point(0.0, 0.0, 0.0), radius_u=1.0, radius_v=0.5
    )
    labeler._add_shape(ellipse, module._style_for("ellipse", "#ff4444"))  # noqa: SLF001

    # The rotate handle's offset uses the labeler's pixel scale, which must be
    # applied *before* the handles are spawned — otherwise the icon is placed
    # with the default 1.0 scale and only corrected after a later refresh.
    assert ellipse._pixel_scale == labeler._pixel_scale  # noqa: SLF001
    handle_pos = ellipse._rotate_handle.point  # noqa: SLF001
    expected_pos = ellipse._rotate_handle_position()  # noqa: SLF001
    assert (handle_pos.x, handle_pos.y, handle_pos.z) == (
        expected_pos.x,
        expected_pos.y,
        expected_pos.z,
    )


def test_ctrl_drag_does_not_create_shape() -> None:
    """Ctrl+drag adjusts brightness/contrast; it must not create a shape."""
    module = _load_example()
    labeler = _make_labeler(module)
    labeler.set_mode("polygon")

    ctrl = frozenset({ModifierKey.CTRL})
    start = DragEvent(modifiers=ctrl, world_position=module.Point(0.0, 0.0, 0.0))
    end = DragEvent(
        modifiers=ctrl,
        delta_pixels=(50.0, 0.0),
        world_position=module.Point(1.0, 0.0, 0.0),
    )

    asyncio.run(labeler._on_drag_start(start, None))  # noqa: SLF001
    asyncio.run(labeler._on_drag_end(end, None))  # noqa: SLF001

    assert labeler.shapes == []


def _polygon_points(module: Any) -> list[Any]:
    return [module.Point(0.0, 0.0, 0.0), module.Point(1.0, 0.0, 0.0), module.Point(1.0, 1.0, 0.0)]


def test_tag_two_segment_colors_table() -> None:
    module = _load_example()
    fn = module._tag_two_segment_colors  # noqa: SLF001
    assert fn(["1", "1", "1", "1"], closed=True) == [None, None, None, None]
    # Each vertex labels its outgoing segment.
    assert fn(["1", "2", "1", "1"], closed=True) == [None, "#ff00ff", None, None]
    assert fn(["1", "2", "1", "2"], closed=True) == [None, "#ff00ff", None, "#ff00ff"]
    assert fn(["1", "2", "2", "1"], closed=True) == [None, "#ff00ff", "#ff00ff", None]
    assert fn(["2", "1", "2", "1"], closed=True) == ["#ff00ff", None, "#ff00ff", None]
    # The last vertex labels the closing segment back to the first.
    assert fn(["1", "1", "1", "2"], closed=True) == [None, None, None, "#ff00ff"]
    assert fn(["2", "2", "2", "2"], closed=True) == ["#ff00ff", "#ff00ff", "#ff00ff", "#ff00ff"]
    assert fn(["1", "2", "1"], closed=False) == [None, "#ff00ff"]


def test_tag_keys_registered() -> None:
    module = _load_example()
    viz, _ = _make_labeler_with_viz(module)
    keyboard = viz._layout.scene("world").config.keyboard  # noqa: SLF001
    keys = [entry["key"] for entry in keyboard]
    assert "1" in keys
    assert "2" in keys


def test_tag_two_handler_updates_tag_and_segment_colors() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    act = module.ActPolygon(_polygon_points(module), default_vertex_tag="1")
    labeler._add_shape(act, module._style_for("polygon", "#ff4444"))  # noqa: SLF001
    labeler._select(act)  # noqa: SLF001

    # Tagging vertex 1 colors its outgoing segment (1 → 2) and keeps it selected.
    act.set_selected_vertex(1)
    asyncio.run(labeler._on_tag_two(None))  # noqa: SLF001
    assert act.vertex_tags == ["1", "2", "1"]
    assert act.segment_colors == [None, "#ff00ff", None]
    assert act.tag_colors["2"] == "#ff00ff"
    assert act.selected_vertex == 1

    # Tagging vertex 2 colors its outgoing segment too (2 → 0); still selected.
    act.set_selected_vertex(2)
    asyncio.run(labeler._on_tag_two(None))  # noqa: SLF001
    assert act.vertex_tags == ["1", "2", "2"]
    assert act.segment_colors == [None, "#ff00ff", "#ff00ff"]
    assert act.selected_vertex == 2

    # Reverting vertex 2 clears only its outgoing segment; still selected.
    asyncio.run(labeler._on_tag_one(None))  # noqa: SLF001
    assert act.vertex_tags == ["1", "2", "1"]
    assert act.segment_colors == [None, "#ff00ff", None]
    assert act.selected_vertex == 2


def test_polygon_defaults_to_tag_one_and_tag_colors() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    act = module.ActPolygon(_polygon_points(module), default_vertex_tag="1")
    labeler._add_shape(act, module._style_for("polygon", "#ff4444"))  # noqa: SLF001
    assert act.vertex_tags == ["1", "1", "1"]
    assert act.tagging is True
    assert act.tag_colors["1"] == "#ff4444"
    assert act.tag_colors["2"] == "#ff00ff"
    assert act.segment_colors == [None, None, None]


def test_load_applies_tags_and_segment_colors() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    path = module.PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    path.add((1.0, 1.0, 0.0))
    path.add((0.0, 0.0, 0.0))
    shape = LabelShape(
        label="p",
        points=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)],
        shape_type="polygon",
        vertex_tags=["1", "2", "1"],
        segment_colors=[None, "#ff00ff", None],
    )
    labeler.add_loaded_shape(path, shape)
    act = labeler.shapes[-1][0]
    assert act.vertex_tags == ["1", "2", "1"]
    assert act.segment_colors == [None, "#ff00ff", None]
