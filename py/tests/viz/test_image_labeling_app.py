# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the image-labeling example's vertex tagging and segment colors."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from pytanga.viz import Visualizer

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_example() -> Any:
    import importlib.util

    path = _REPO_ROOT / "py" / "examples" / "apps" / "image_labeling_app.py"
    spec = importlib.util.spec_from_file_location("image_labeling_app", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_labeler(module: Any) -> Any:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    return module.ImageLabeler(viz)


def test_polygon_from_entity_defaults_to_tag_one() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    path = module.PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    path.add((1.0, 1.0, 0.0))
    path.add((0.0, 0.0, 0.0))
    act = labeler._act_from_entity(path)  # noqa: SLF001
    labeler.add_shape(act)
    assert act.vertex_tags == ["1", "1", "1"]


def test_tagging_checkbox_toggles_all_polygons() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    path = module.PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    path.add((1.0, 1.0, 0.0))
    path.add((0.0, 0.0, 0.0))
    act = labeler._act_from_entity(path)  # noqa: SLF001
    labeler.add_shape(act)
    assert act.tagging is False
    asyncio.run(labeler._on_tagging_change(True, None))  # noqa: SLF001
    assert labeler.tagging is True
    assert act.tagging is True


def test_tag_edit_updates_selected_vertex() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    path = module.PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    path.add((1.0, 1.0, 0.0))
    path.add((0.0, 0.0, 0.0))
    act = labeler._act_from_entity(path)  # noqa: SLF001
    labeler.add_shape(act)
    labeler._select(act)  # noqa: SLF001
    act.set_selected_vertex(0)
    asyncio.run(labeler._on_tag_edit("2", None))  # noqa: SLF001
    assert act.vertex_tags[0] == "2"


def test_segment_color_update_and_clear() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    path = module.PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    path.add((1.0, 1.0, 0.0))
    path.add((0.0, 0.0, 0.0))
    act = labeler._act_from_entity(path)  # noqa: SLF001
    labeler.add_shape(act)
    labeler._select(act)  # noqa: SLF001
    act.set_selected_vertex(0)
    asyncio.run(labeler._on_segment_color("#ff00ff", None))  # noqa: SLF001
    assert act.segment_colors[0] == "#ff00ff"
    asyncio.run(labeler._on_clear_segment(None, None))  # noqa: SLF001
    assert act.segment_colors[0] is None


def test_selection_resyncs_tag_panel() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    path = module.PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    path.add((1.0, 1.0, 0.0))
    path.add((0.0, 0.0, 0.0))
    act = labeler._act_from_entity(path)  # noqa: SLF001
    labeler.add_shape(act)
    labeler._select(act)  # noqa: SLF001
    act.set_selected_vertex(1)
    act.set_vertex_tag(1, "2")
    labeler._sync_tag_panel()  # noqa: SLF001
    assert labeler._tag_edit.value == "2"  # noqa: SLF001


def test_to_document_and_load_round_trip() -> None:
    module = _load_example()
    labeler = _make_labeler(module)
    path = module.PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    path.add((1.0, 1.0, 0.0))
    path.add((0.0, 0.0, 0.0))
    act = labeler._act_from_entity(path)  # noqa: SLF001
    labeler.add_shape(act, vertex_tags=["1", "2", "1"], segment_colors=[None, "#ff00ff", None])
    doc = labeler.to_document()
    assert doc.shapes[0].vertex_tags == ["1", "2", "1"]
    assert doc.shapes[0].segment_colors == [None, "#ff00ff", None]

    labeler2 = _make_labeler(module)
    labeler2.load_document(doc)
    assert labeler2.shapes[0].act.vertex_tags == ["1", "2", "1"]
    assert labeler2.shapes[0].act.segment_colors == [None, "#ff00ff", None]
