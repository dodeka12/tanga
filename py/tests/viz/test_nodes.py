# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the scene-graph node classes (`_nodes.py`)."""

import numpy as np
import pytest

from pytanga.geometry.entities import Point
from pytanga.viz._nodes import Transform, VizGroup, VizNode, VizObject
from pytanga.viz._styles import PointStyle

from pytanga.viz._transforms import rotation_matrix, to_trs, translation_matrix


class TestTransform:
    def test_transform_matrix(self):
        t = Transform(position=(1, 2, 3), rotation=(0, 0, 0), scale=(1, 1, 1))
        m = t.matrix()
        assert np.allclose(m, translation_matrix(1, 2, 3))

    def test_transform_from_matrix_roundtrip(self):
        r = rotation_matrix((1.0, 0.5, -0.3), 0.9)
        m = translation_matrix(0.5, -1.0, 2.0) @ r
        t = Transform()
        t.from_matrix(m)
        assert np.allclose(t.matrix(), m, atol=1e-10)

    def test_transform_apply_local(self):
        t = Transform(position=(1, 0, 0))
        t.apply_matrix(translation_matrix(0, 1, 0), space="local")
        # M_current @ M = T(1,0,0) @ T(0,1,0) = T(1,1,0)
        assert t.position == (1.0, 1.0, 0.0)

    def test_transform_apply_world(self):
        t = Transform(position=(1, 0, 0))
        t.apply_matrix(translation_matrix(0, 1, 0), space="world")
        # M @ M_current = T(0,1,0) @ T(1,0,0) = T(1,1,0)
        assert t.position == (1.0, 1.0, 0.0)

    def test_transform_apply_bad_space(self):
        t = Transform()
        with pytest.raises(ValueError, match="local"):
            t.apply_matrix(np.eye(4), space="bogus")

    def test_transform_mutators(self):
        t = Transform()
        t.translate(1, 2, 3)
        assert t.position == (1.0, 2.0, 3.0)
        t.rotate((0, 0, 1), 0.0)
        t.scale_by(2.0)
        assert t.scale == (2.0, 2.0, 2.0)
        t.scale_by(1.0, 2.0, 3.0)
        assert t.scale == (2.0, 4.0, 6.0)

    def test_transform_set(self):
        t = Transform()
        t.set(position=(1, 1, 1), rotation=(0, 0, 1), scale=(2, 2, 2))
        assert t.position == (1.0, 1.0, 1.0)
        assert t.rotation == (0.0, 0.0, 1.0)
        assert t.scale == (2.0, 2.0, 2.0)


class TestNodeParenting:
    def test_add_child_sets_parent(self):
        parent = VizNode("p")
        child = VizNode("c")
        parent.add_child(child)
        assert child.parent is parent
        assert child in parent.children

    def test_reparent_moves_child(self):
        a = VizNode("a")
        b = VizNode("b")
        child = VizNode("c", parent=a)
        b.add_child(child)
        assert child.parent is b
        assert child not in a.children
        assert child in b.children

    def test_remove_child(self):
        parent = VizNode("p")
        child = VizNode("c", parent=parent)
        parent.remove_child(child)
        assert child.parent is None
        assert child not in parent.children

    def test_world_matrix(self):
        parent = VizNode("p", transform=Transform(position=(1, 0, 0)))
        child = VizNode("c", parent=parent, transform=Transform(position=(0, 2, 0)))
        m = child.world_matrix()
        pos, _, _ = to_trs(m)
        assert np.allclose(pos, (1.0, 2.0, 0.0))


class TestVizObject:
    def _obj(self):
        return VizObject("o1", kind="Point", entity=Point(0, 0, 0))

    def test_dirty_on_set_entity(self):
        o = self._obj()
        o.dirty = False
        o.transform_dirty = False
        o.set_entity(Point(3, 4, 5))
        assert o.dirty is True
        assert o.transform_dirty is False
        assert o.kind == "Point"

    def test_dirty_on_set_style(self):
        o = self._obj()
        o.style = PointStyle(color="#ffffff", size=0.08)
        o.dirty = False
        o.set_style(PointStyle(size=0.2))
        assert o.dirty is True
        assert o.style.size == 0.2  # merged non-None
        assert o.style.color == "#ffffff"  # preserved

    def test_set_color_opacity(self):
        o = self._obj()
        o.style = PointStyle(color="#ffffff", opacity=1.0)
        o.dirty = False
        o.set_color("#ff0000")
        o.set_opacity(0.5)
        assert o.color == "#ff0000"
        assert o.opacity == 0.5
        assert o.dirty is True

    def test_update_marks_dirty(self):
        o = self._obj()
        o.style = PointStyle(size=0.08)
        o.dirty = False
        o.update(size=0.25)
        assert o.dirty is True


class TestVizGroup:
    def test_group_serialize(self):
        g = VizGroup("g1", name="grp")
        d = g.serialize()
        assert d["kind"] == "VizGroup"
        assert d["id"] == "g1"
        assert d["transform"] == {
            "position": [0.0, 0.0, 0.0],
            "rotation": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
        }
        assert "entity" not in d
        assert "style" not in d

    def test_group_children(self):
        g = VizGroup("g1")
        child = VizObject("c1", kind="Point", entity=Point(0, 0, 0), parent=g)
        assert child.parent is g
        assert child in g.children

    def test_group_node_kind(self):
        g = VizGroup("g1")
        assert g.kind == "VizGroup"
        assert isinstance(g, VizNode)


class TestResolveStyle:
    def test_resolve_style_default(self):
        from pytanga.viz._nodes import resolve_style

        s = resolve_style("Point", None, {}, None)
        assert s.color == "#ff4444"
        assert s.size == 0.08

    def test_resolve_style_user_merge(self):
        from pytanga.viz._nodes import resolve_style

        s = resolve_style("Point", PointStyle(size=0.5), {}, None)
        assert s.size == 0.5
        assert s.color == "#ff4444"  # from canonical default

    def test_resolve_style_props_override(self):
        from pytanga.viz._nodes import resolve_style

        s = resolve_style("Point", None, {"color": "#00ff00", "opacity": 0.4}, None)
        assert s.color == "#00ff00"
        assert s.opacity == 0.4