# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the VizObjectRef convenience wrapper."""

import math

import numpy as np
import pytest

from pytanga.geometry.entities import Direction, Point
from pytanga.geometry.operators import Dilator, Motor, Rotor, Translator
from pytanga.viz._label import Label
from pytanga.viz._object_ref import VizObjectRef
from pytanga.viz._styles import PointStyle
from pytanga.viz.visualizer import Visualizer


def _point_ref(handle, point=(0, 0, 0), **kwargs):
    eid = handle.add(Point(*point), **kwargs)
    return VizObjectRef(handle, handle.scene.get_node(eid))


class TestEntityAndStyle:
    def test_entity_get_set(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h, (1, 2, 3))
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.entity = Point(4, 5, 6)
        assert node.dirty_for("content")
        assert node.entity == Point(4, 5, 6)
        assert ref.entity == Point(4, 5, 6)

    def test_style_merge(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.style = PointStyle(size=0.2)
        assert node.dirty_for("style")
        assert node.style["size"] == 0.2

    def test_color_opacity(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.color = "#00ff00"
        assert node.dirty_for("style")
        assert node.style["color"] == "#00ff00"
        node.consume_dirty()
        ref.opacity = 0.5
        assert node.dirty_for("style")
        assert node.style["opacity"] == 0.5
        assert ref.color == "#00ff00"
        assert ref.opacity == 0.5

    def test_texture_label(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.texture_label = {"text": "hi"}
        assert node.dirty_for("style")
        assert node.style["texture_label"] == {"text": "hi"}


class TestTransforms:
    def test_translate_marks_transform(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.translate(1, 2, 3)
        assert node.dirty_for("transform")
        assert not node.dirty_for("style")
        assert node.transform.position == (1.0, 2.0, 3.0)

    def test_rotate_scale_set_transform(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.rotate(math.pi / 2, (0, 0, 1))
        ref.scale_by(2.0)
        ref.set_transform(position=(1.0, 2.0, 3.0))
        assert node.transform.position == (1.0, 2.0, 3.0)
        assert node.dirty_for("transform")

    def test_set_transform_accepts_rotor(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.set_transform(rotation=Rotor(math.pi / 2, Direction(0, 0, 1)))
        assert node.transform.rotation == pytest.approx((0.0, 0.0, math.pi / 2), abs=1e-9)
        assert node.dirty_for("transform")

    def test_set_transform_scale_is_triple(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.set_transform(scale=(2.0, 3.0, 4.0))
        assert node.transform.scale == (2.0, 3.0, 4.0)


    def test_transform_operator(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.apply_transform(Translator(vector=Direction(1.0, 2.0, 3.0)))
        assert node.dirty_for("transform")
        assert node.transform.position == (1.0, 2.0, 3.0)

        node.consume_dirty()
        ref.apply_transform(Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)))
        assert node.dirty_for("transform")

        ref.apply_transform(Motor(
            rotor=Rotor(angle=0.5, axis=Direction(0, 0, 1)),
            translator=Translator(vector=Direction(1.0, 0.0, 0.0)),
        ))
        ref.apply_transform(Dilator(factor=2.0))
        assert node.dirty_for("transform")

    def test_set_transform_accepts_operator(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.set_transform(Translator(vector=Direction(1.0, 2.0, 3.0)))
        assert node.dirty_for("transform")
        assert node.transform.position == (1.0, 2.0, 3.0)

    def test_set_transform_accepts_transform(self):
        from pytanga.viz import Transform

        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.set_transform(Transform(position=(4.0, 5.0, 6.0)))
        assert node.dirty_for("transform")
        assert node.transform.position == (4.0, 5.0, 6.0)

    def test_apply_transform_accepts_transform(self):
        from pytanga.viz import Transform

        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.apply_transform(Transform(position=(1.0, 0.0, 0.0)))
        assert node.dirty_for("transform")
        assert node.transform.position == (1.0, 0.0, 0.0)

    def test_set_and_apply_transform_accept_mv(self):
        from pytanga.basis import BasisN3
        from pytanga.geometry import Geometry

        geo = Geometry(BasisN3())
        mv = geo.create(Translator(vector=Direction(1.0, 2.0, 3.0)))

        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        node = h.scene.get_node(ref.id)
        node.consume_dirty()
        ref.set_transform(mv)
        assert node.dirty_for("transform")
        assert node.transform.position == (1.0, 2.0, 3.0)

        node.consume_dirty()
        ref.apply_transform(geo.create(Translator(vector=Direction(1.0, 0.0, 0.0))))
        assert node.dirty_for("transform")
        assert node.transform.position == (2.0, 2.0, 3.0)

    def test_world_matrix(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        g = h.scene.add_group("g")
        gref = VizObjectRef(h, g)
        gref.translate(1.0, 0.0, 0.0)
        child = gref.new(Point(0, 0, 0))
        child.translate(0.0, 2.0, 0.0)
        m = child.world_matrix
        assert np.allclose(m[:3, 3], [1.0, 2.0, 0.0])


class TestOverlay:
    def test_overlay_ref_has_no_transform(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        lid = h.add(Label(text="X", position=(0, 0, 0)))
        ref = VizObjectRef(h, h.scene.get_node(lid))
        assert ref.layer == "overlay"
        assert ref.text == "X"
        with pytest.raises(TypeError):
            ref.translate(1, 0, 0)
        with pytest.raises(TypeError):
            ref.world_matrix

    def test_labels_access(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        eid = h.add(Point(0, 0, 0), label="L")
        ref = VizObjectRef(h, h.scene.get_node(eid))
        assert len(ref.label_ids) == 1
        assert len(ref.labels) == 1
        assert ref.labels[0].text == "L"

    def test_update_label(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        eid = h.add(Point(0, 0, 0), label="L")
        label_id = h.scene.get_label_ids(eid)[0]
        lref = VizObjectRef(h, h.scene.get_node(label_id))
        lref.update_label(text="New")
        assert lref.text == "New"

    def test_update_label_on_entity_ref(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = h.new(Point(1, 2, 3), label="P")
        ref.update_label(text="moved")
        assert ref.labels[0].text == "moved"


class TestGroup:
    def test_group_add_new(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        g = h.scene.add_group("grp")
        gref = VizObjectRef(h, g)
        child = gref.new(Point(1, 2, 3))
        assert isinstance(child, VizObjectRef)
        assert child.parent is not None
        assert child.parent.id == g.id

    def test_group_non_group_guards(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("t")
        ref = _point_ref(h)
        with pytest.raises(TypeError):
            ref.new(Point(1, 2, 3))
        with pytest.raises(TypeError):
            ref.add_group("x")

