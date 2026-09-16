# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the scene-graph node classes (`_nodes.py`) and Scene integration."""

import math

import numpy as np
import pytest

from pytanga.geometry.entities import Direction, Line, Point
from pytanga.geometry.operators import Motor, Rotor, Translator
from pytanga.viz._nodes import Transform, VizGroup, VizOverlayObject, VizSceneObject
from pytanga.viz._styles import PointStyle
from pytanga.viz._transforms import operator_to_matrix
from pytanga.viz.scene import Scene


# ── Transform ───────────────────────────────────────────────


class TestTransform:
    def test_defaults(self):  # noqa: ANN201
        t = Transform()
        assert t.position == (0.0, 0.0, 0.0)
        assert t.rotation == (0.0, 0.0, 0.0)
        assert t.scale == (1.0, 1.0, 1.0)

    def test_matrix_identity(self):  # noqa: ANN201
        t = Transform()
        assert np.allclose(t.matrix(), np.eye(4))

    def test_matrix_translation(self):  # noqa: ANN201
        t = Transform(position=(1.0, 2.0, 3.0))
        m = t.matrix()
        assert np.allclose(m[:3, 3], [1.0, 2.0, 3.0])

    def test_scale_by_uniform(self):  # noqa: ANN201
        t = Transform()
        t.scale_by(2.0)
        assert t.scale == (2.0, 2.0, 2.0)

    def test_scale_by_component(self):  # noqa: ANN201
        t = Transform()
        t.scale_by(2.0, 3.0, 4.0)
        assert t.scale == (2.0, 3.0, 4.0)

    def test_translate(self):  # noqa: ANN201
        t = Transform()
        t.translate(1.0, 2.0, 3.0)
        assert t.position == (1.0, 2.0, 3.0)

    def test_translate_vector(self):  # noqa: ANN201
        t = Transform()
        t.translate((1.0, 2.0, 3.0))
        assert t.position == (1.0, 2.0, 3.0)

    def test_rotate_z(self):  # noqa: ANN201
        t = Transform()
        t.rotate((0.0, 0.0, 1.0), math.pi / 2)
        m = t.matrix()
        v = np.array([1.0, 0.0, 0.0, 1.0])
        assert np.allclose(m @ v, [0.0, 1.0, 0.0, 1.0], atol=1e-12)

    def test_from_matrix_roundtrip(self):  # noqa: ANN201
        t = Transform(position=(1.0, 2.0, 3.0), scale=(2.0, 1.0, 1.0))
        m = t.matrix()
        t2 = Transform().from_matrix(m)
        assert np.allclose(t2.matrix(), m, atol=1e-10)

    def test_set(self):  # noqa: ANN201
        t = Transform()
        t.set(position=(1.0, 0.0, 0.0), scale=(2.0, 2.0, 2.0))
        assert t.position == (1.0, 0.0, 0.0)
        assert t.scale == (2.0, 2.0, 2.0)

    def test_from_operator(self):  # noqa: ANN201
        from pytanga.viz import Transform as PublicTransform

        ops = [
            Translator(vector=Direction(1, 2, 3)),
            Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)),
            Motor(
                rotor=Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)),
                translator=Translator(vector=Direction(1, 0, 0)),
            ),
        ]
        for op in ops:
            t = Transform.from_operator(op)
            assert np.allclose(t.matrix(), operator_to_matrix(op), atol=1e-12)

        # `Transform` is importable from the public `pytanga.viz` namespace.
        assert PublicTransform is Transform


# ── Auto-generated ids ──────────────────────────────────────


class TestAutoId:
    def test_viz_group_default_id(self):  # noqa: ANN201
        g = VizGroup()
        assert g.id
        assert g.kind == "VizGroup"

    def test_viz_scene_object_default_id(self):  # noqa: ANN201
        n = VizSceneObject(None, Point(0, 0, 0), kind="Point")
        assert n.id

    def test_distinct_default_ids(self):  # noqa: ANN201
        assert VizGroup().id != VizGroup().id

    def test_explicit_id_preserved(self):  # noqa: ANN201
        assert VizGroup("my-id").id == "my-id"
        assert VizSceneObject("node-id", Point(0, 0, 0), kind="Point").id == "node-id"


# ── VizSceneObject aspects ──────────────────────────────────


class TestSceneObjectAspects:
    def test_set_entity_marks_content(self):  # noqa: ANN201
        node = VizSceneObject("a", Point(0, 0, 0), kind="Point")
        node.consume_dirty()
        node.set_entity(Point(1, 2, 3))
        assert node.dirty_for("content")
        assert not node.dirty_for("style")
        assert not node.dirty_for("transform")
        assert not node.dirty_for("full")

    def test_set_entity_marks_full_on_kind_change(self):  # noqa: ANN201
        node = VizSceneObject("a", Point(0, 0, 0), kind="Point")
        node.consume_dirty()
        node.set_entity(Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)))
        assert node.dirty_for("full")
        assert not node.dirty_for("content")

    def test_set_style_marks_style(self):  # noqa: ANN201
        node = VizSceneObject("a", Point(0, 0, 0), {"color": "#ff0000"}, kind="Point")
        node.consume_dirty()
        node.set_style(PointStyle(color="#00ff00"))
        assert node.dirty_for("style")
        assert not node.dirty_for("full")

    def test_set_transform_marks_transform(self):  # noqa: ANN201
        node = VizSceneObject("a", Point(0, 0, 0), None, kind="Point")
        node.consume_dirty()
        node.translate(1.0, 0.0, 0.0)
        assert node.dirty_for("transform")
        assert not node.dirty_for("style")
        assert not node.dirty_for("full")


# ── Parenting ───────────────────────────────────────────────


class TestSceneObjectParenting:
    def test_add_child(self):  # noqa: ANN201
        parent = VizGroup("g")
        child = VizSceneObject("c", Point(0, 0, 0), None, kind="Point")
        parent.add_child(child)
        assert child.parent is parent
        assert child in parent.children

    def test_reparent(self):  # noqa: ANN201
        p1 = VizGroup("g1")
        p2 = VizGroup("g2")
        child = VizSceneObject("c", Point(0, 0, 0), None, kind="Point")
        p1.add_child(child)
        p2.add_child(child)
        assert child.parent is p2
        assert child not in p1.children

    def test_world_matrix(self):  # noqa: ANN201
        parent = VizGroup("g")
        parent.translate(1.0, 0.0, 0.0)
        child = VizSceneObject("c", Point(0, 0, 0), None, kind="Point")
        parent.add_child(child)
        child.translate(0.0, 2.0, 0.0)
        m = child.world_matrix()
        assert np.allclose(m[:3, 3], [1.0, 2.0, 0.0])


# ── Overlay ─────────────────────────────────────────────────


class TestOverlayObject:
    def test_overlay_has_no_transform(self):  # noqa: ANN201
        node = VizOverlayObject("l", position=(1.0, 2.0, 3.0), attach_to="p")
        assert node.layer == "overlay"
        assert node.position == (1.0, 2.0, 3.0)
        assert node.attach_to == "p"
        assert not hasattr(node, "transform")

    def test_overlay_setters(self):  # noqa: ANN201
        node = VizOverlayObject("l", payload="hi")
        node.consume_dirty()
        node.set_payload("bye")
        assert node.dirty_for("full")
        node.consume_dirty()
        node.set_position((0.0, 0.0, 0.0))
        assert node.dirty_for("full")


# ── Group ───────────────────────────────────────────────────


class TestGroup:
    def test_group_kind_no_entity(self):  # noqa: ANN201
        g = VizGroup("g")
        assert g.kind == "VizGroup"
        assert g.entity is None
        assert g.style is None
        s = g.serialize()
        assert s["kind"] == "VizGroup"


# ── Scene integration ───────────────────────────────────────


class TestSceneIntegration:
    def test_scene_add_populates_nodes(self):  # noqa: ANN201
        s = Scene()
        eid = s.add(Point(1, 2, 3))
        node = s.get_node(eid)
        assert isinstance(node, VizSceneObject)
        assert node.style is not None
        assert node.style["style_type"] == "PointStyle"

    def test_scene_add_resolves_color_override(self):  # noqa: ANN201
        s = Scene()
        eid = s.add(Point(0, 0, 0), color="#00ff00")
        assert s.get_node(eid).style["color"] == "#00ff00"

    def test_scene_add_label_populates_nodes(self):  # noqa: ANN201
        from pytanga.viz._label import Label

        s = Scene()
        lid = s.add_label(Label(text="X", position=(0, 0, 0), parent_id="p"))
        node = s.get_node(lid)
        assert isinstance(node, VizOverlayObject)
        assert node.attach_to == "p"
        assert node.payload == "X"

    def test_get_node_and_add_group(self):  # noqa: ANN201
        s = Scene()
        g = s.add_group("grp")
        assert isinstance(g, VizGroup)
        assert s.get_node(g.id) is g
        assert g.id in s.group_ids

    def test_remove_group_node(self):  # noqa: ANN201
        s = Scene()
        g = s.add_group("grp")
        s.remove(g.id)
        _, removed = s.flush()
        assert g.id in removed
        assert g.id not in s._nodes

    def test_add_viz_entity_and_label(self):  # noqa: ANN201
        s = Scene()
        eid = s.add_viz(
            Line(Point(0, 0, 0), Direction(1, 0, 0)), color="#ff0000", label="axis"
        )
        node = s.get_node(eid)
        assert isinstance(node, VizSceneObject)
        assert node.style["color"] == "#ff0000"
        label_ids = s.get_label_ids(eid)
        assert len(label_ids) == 1
        assert s.get_node(label_ids[0]).payload == "axis"


# ── Detached subtree insertion ──────────────────────────────


class TestSubtreeInsertion:
    def _make_subtree(self) -> tuple:
        s = Scene()
        g = VizGroup("g")
        c1 = VizSceneObject("c1", Point(0, 0, 0), kind="Point")
        c2 = VizSceneObject("c2", Point(1, 0, 0), kind="Point")
        g.add_child(c1)
        g.add_child(c2)
        s.add_subtree(g)
        return s, g, c1, c2

    def test_remove_node_only_child(self):  # noqa: ANN201
        s, _, c1, c2 = self._make_subtree()
        s.remove("c1")
        _, removed = s.flush()
        assert "c1" in removed
        assert "c2" not in removed
        assert "c1" not in s._nodes

    def test_set_interaction_node_only_child(self):  # noqa: ANN201
        from pytanga.viz._interaction import InteractionConfig

        s, _, c1, _ = self._make_subtree()
        c1.consume_dirty()
        s.set_interaction("c1", InteractionConfig(enabled=True))
        assert c1.dirty_for("interaction")
        assert s.get_interaction("c1") is not None

    def test_add_subtree_registers_descendants(self):  # noqa: ANN201
        s, g, c1, c2 = self._make_subtree()
        assert s.get_node("g") is g
        assert s.get_node("c1") is c1
        assert s.get_node("c2") is c2
        assert s._order == ["g"]

    def test_add_subtree_backfills_partial_style(self):  # noqa: ANN201
        s = Scene()
        g = VizGroup("g")
        c = VizSceneObject("c", Point(0, 0, 0), PointStyle(color="#ff0000"), kind="Point")
        g.add_child(c)
        s.add_subtree(g)
        style = s.get_node("c").style
        assert style["color"] == "#ff0000"
        assert style["style_type"] == "PointStyle"
        assert "size" in style  # canonical default backfilled

    def test_update_node_only_child(self):  # noqa: ANN201
        s, _, c1, _ = self._make_subtree()
        s.update("c1", opacity=0.5)
        assert s.get_node("c1").style["opacity"] == 0.5

    def test_update_entity_node_only_child(self):  # noqa: ANN201
        s, _, c1, _ = self._make_subtree()
        s.update_entity("c1", Point(9, 9, 9))
        node = s.get_node("c1")
        assert (node.entity.x, node.entity.y, node.entity.z) == (9, 9, 9)

    def test_add_subtree_id_collision_raises(self):  # noqa: ANN201
        s = Scene()
        s.add_node(VizGroup("dup"))
        g = VizGroup("g")
        c = VizSceneObject("dup", Point(1, 0, 0), kind="Point")
        g.add_child(c)
        with pytest.raises(ValueError):
            s.add_subtree(g)
