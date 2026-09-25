# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for entity visibility (hide/show)."""

import pytest

from pytanga.geometry import Point, Sphere
from pytanga.viz._nodes import VizSceneObject
from pytanga.viz._object_ref import VizObjectRef
from pytanga.viz.visualizer import Visualizer


def _scene_with_sphere():  # noqa: ANN202
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    h = viz.scene("t")
    eid = h.add(Sphere(Point(0, 0, 0), radius=1), entity_id="sphere")
    node = h.scene.get_node(eid)
    node.consume_dirty()
    return h, node


class TestNodeVisibility:
    def test_set_visible_marks_aspect(self):  # noqa: ANN201
        node = VizSceneObject("n", Point(0, 0, 0), kind="Point")
        node.consume_dirty()
        node.set_visible(False)
        assert node.visible is False
        assert node.dirty_for("visible")

    def test_visible_patch_shape(self):  # noqa: ANN201
        node = VizSceneObject("n", Point(0, 0, 0), kind="Point")
        node.consume_dirty()
        node.set_visible(False)
        assert node.patch("visible") == {
            "id": "n",
            "aspect": "visible",
            "value": {"visible": False},
        }

    def test_apply_props_visible_not_in_style_or_props(self):  # noqa: ANN201
        node = VizSceneObject("n", Point(0, 0, 0), kind="Point")
        node.consume_dirty()
        node.apply_props({"visible": False})
        assert node.visible is False
        assert node.dirty_for("visible")
        assert not node.dirty_for("style")
        assert "visible" not in node._props
        assert "visible" not in (node.style or {})


class TestSceneVisibility:
    def test_set_visible_flush_emits_visible_patch(self):  # noqa: ANN201
        h, _ = _scene_with_sphere()
        h.scene.set_visible("sphere", False)
        patches, _ = h.scene.flush()
        visible_patches = [p for p in patches if p["aspect"] == "visible"]
        assert visible_patches == [
            {"id": "sphere", "aspect": "visible", "value": {"visible": False}}
        ]

    def test_set_visible_unknown_raises(self):  # noqa: ANN201
        h, _ = _scene_with_sphere()
        with pytest.raises(KeyError):
            h.scene.set_visible("missing", False)


class TestVisibilityApi:
    def test_handle_hide_show(self):  # noqa: ANN201
        h, node = _scene_with_sphere()
        h.hide("sphere")
        assert node.visible is False
        assert node.dirty_for("visible")
        node.consume_dirty()
        h.set_visible("sphere", True)
        assert node.visible is True

    def test_visualizer_set_visible_and_hide(self):  # noqa: ANN201
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        h.add(Sphere(Point(0, 0, 0), radius=1), entity_id="sphere")
        node = h.scene.get_node("sphere")
        node.consume_dirty()
        viz.set_visible("sphere", False, scene_name="t")
        assert node.visible is False
        node.consume_dirty()
        viz.set_visible("sphere", True, scene_name="t")
        assert node.visible is True
        viz.hide("sphere", scene_name="t")
        assert node.visible is False

    def test_object_ref_set_visible(self):  # noqa: ANN201
        h, node = _scene_with_sphere()
        ref = VizObjectRef(h, node)
        ref.set_visible(False)
        assert node.visible is False
        assert node.dirty_for("visible")
        node.consume_dirty()
        ref.set_visible(True)
        assert node.visible is True
