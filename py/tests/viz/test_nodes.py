# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the scene-graph node classes (`_nodes.py`) and Scene integration."""

import math

import numpy as np

from pytanga.geometry.entities import Direction, Line, Point
from pytanga.viz._nodes import Transform, VizGroup, VizOverlayObject, VizSceneObject
from pytanga.viz._styles import PointStyle
from pytanga.viz.scene import Scene


# ── Transform ───────────────────────────────────────────────


class TestTransform:
    def test_defaults(self):
        t = Transform()
        assert t.position == (0.0, 0.0, 0.0)
        assert t.rotation == (0.0, 0.0, 0.0)
        assert t.scale == (1.0, 1.0, 1.0)

    def test_matrix_identity(self):
        t = Transform()
        assert np.allclose(t.matrix(), np.eye(4))

    def test_matrix_translation(self):
        t = Transform(position=(1.0, 2.0, 3.0))
        m = t.matrix()
        assert np.allclose(m[:3, 3], [1.0, 2.0, 3.0])

    def test_scale_by_uniform(self):
        t = Transform()
        t.scale_by(2.0)
        assert t.scale == (2.0, 2.0, 2.0)

    def test_scale_by_component(self):
        t = Transform()
        t.scale_by(2.0, 3.0, 4.0)
        assert t.scale == (2.0, 3.0, 4.0)

    def test_translate(self):
        t = Transform()
        t.translate(1.0, 2.0, 3.0)
        assert t.position == (1.0, 2.0, 3.0)

    def test_translate_vector(self):
        t = Transform()
        t.translate((1.0, 2.0, 3.0))
        assert t.position == (1.0, 2.0, 3.0)

    def test_rotate_z(self):
        t = Transform()
        t.rotate((0.0, 0.0, 1.0), math.pi / 2)
        m = t.matrix()
        v = np.array([1.0, 0.0, 0.0, 1.0])
        assert np.allclose(m @ v, [0.0, 1.0, 0.0, 1.0], atol=1e-12)

    def test_from_matrix_roundtrip(self):
        t = Transform(position=(1.0, 2.0, 3.0), scale=(2.0, 1.0, 1.0))
        m = t.matrix()
        t2 = Transform().from_matrix(m)
        assert np.allclose(t2.matrix(), m, atol=1e-10)

    def test_set(self):
        t = Transform()
        t.set(position=(1.0, 0.0, 0.0), scale=(2.0, 2.0, 2.0))
        assert t.position == (1.0, 0.0, 0.0)
        assert t.scale == (2.0, 2.0, 2.0)


# ── VizSceneObject aspects ──────────────────────────────────


class TestSceneObjectAspects:
    def test_set_entity_marks_content(self):
        node = VizSceneObject("a", Point(0, 0, 0), kind="Point")
        node.consume_dirty()
        node.set_entity(Point(1, 2, 3))
        assert node.dirty_for("content")
        assert not node.dirty_for("style")
        assert not node.dirty_for("transform")
        assert not node.dirty_for("full")

    def test_set_entity_marks_full_on_kind_change(self):
        node = VizSceneObject("a", Point(0, 0, 0), kind="Point")
        node.consume_dirty()
        node.set_entity(Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)))
        assert node.dirty_for("full")
        assert not node.dirty_for("content")

    def test_set_style_marks_style(self):
        node = VizSceneObject("a", Point(0, 0, 0), {"color": "#ff0000"}, kind="Point")
        node.consume_dirty()
        node.set_style(PointStyle(color="#00ff00"))
        assert node.dirty_for("style")
        assert not node.dirty_for("full")

    def test_set_transform_marks_transform(self):
        node = VizSceneObject("a", Point(0, 0, 0), None, kind="Point")
        node.consume_dirty()
        node.translate(1.0, 0.0, 0.0)
        assert node.dirty_for("transform")
        assert not node.dirty_for("style")
        assert not node.dirty_for("full")


# ── Parenting ───────────────────────────────────────────────


class TestSceneObjectParenting:
    def test_add_child(self):
        parent = VizGroup("g")
        child = VizSceneObject("c", Point(0, 0, 0), None, kind="Point")
        parent.add_child(child)
        assert child.parent is parent
        assert child in parent.children

    def test_reparent(self):
        p1 = VizGroup("g1")
        p2 = VizGroup("g2")
        child = VizSceneObject("c", Point(0, 0, 0), None, kind="Point")
        p1.add_child(child)
        p2.add_child(child)
        assert child.parent is p2
        assert child not in p1.children

    def test_world_matrix(self):
        parent = VizGroup("g")
        parent.translate(1.0, 0.0, 0.0)
        child = VizSceneObject("c", Point(0, 0, 0), None, kind="Point")
        parent.add_child(child)
        child.translate(0.0, 2.0, 0.0)
        m = child.world_matrix()
        assert np.allclose(m[:3, 3], [1.0, 2.0, 0.0])


# ── Overlay ─────────────────────────────────────────────────


class TestOverlayObject:
    def test_overlay_has_no_transform(self):
        node = VizOverlayObject("l", position=(1.0, 2.0, 3.0), attach_to="p")
        assert node.layer == "overlay"
        assert node.position == (1.0, 2.0, 3.0)
        assert node.attach_to == "p"
        assert not hasattr(node, "transform")

    def test_overlay_setters(self):
        node = VizOverlayObject("l", payload="hi")
        node.consume_dirty()
        node.set_payload("bye")
        assert node.dirty_for("full")
        node.consume_dirty()
        node.set_position((0.0, 0.0, 0.0))
        assert node.dirty_for("full")


# ── Group ───────────────────────────────────────────────────


class TestGroup:
    def test_group_kind_no_entity(self):
        g = VizGroup("g")
        assert g.kind == "VizGroup"
        assert g.entity is None
        assert g.style is None
        s = g.serialize()
        assert s["kind"] == "VizGroup"


# ── Scene integration ───────────────────────────────────────


class TestSceneIntegration:
    def test_scene_add_populates_nodes(self):
        s = Scene()
        eid = s.add(Point(1, 2, 3))
        node = s.get_node(eid)
        assert isinstance(node, VizSceneObject)
        assert node.style is not None
        assert node.style["style_type"] == "PointStyle"

    def test_scene_add_resolves_color_override(self):
        s = Scene()
        eid = s.add(Point(0, 0, 0), color="#00ff00")
        assert s.get_node(eid).style["color"] == "#00ff00"

    def test_scene_add_label_populates_nodes(self):
        from pytanga.viz._label import Label

        s = Scene()
        lid = s.add_label(Label(text="X", position=(0, 0, 0), parent_id="p"))
        node = s.get_node(lid)
        assert isinstance(node, VizOverlayObject)
        assert node.attach_to == "p"
        assert node.payload == "X"

    def test_get_node_and_add_group(self):
        s = Scene()
        g = s.add_group("grp")
        assert isinstance(g, VizGroup)
        assert s.get_node(g.id) is g
        assert g.id in s.group_ids

    def test_remove_group_node(self):
        s = Scene()
        g = s.add_group("grp")
        s.remove(g.id)
        _, removed = s.flush()
        assert g.id in removed
        assert g.id not in s._nodes