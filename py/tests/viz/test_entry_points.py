# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the Phase 6 entry points (new / add_group / parent_id / attach_to)."""

from pytanga.geometry.entities import Point
from pytanga.viz import Visualizer, VizObjectRef


class TestEntryPoints:
    def test_add_returns_str(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        eid = viz.add(Point(1, 2, 3))
        assert isinstance(eid, str)

    def test_new_returns_ref(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        ref = viz.new(Point(1, 2, 3))
        assert isinstance(ref, VizObjectRef)
        assert ref.id in viz._scenes[""]._nodes

    def test_add_group_returns_ref(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        ref = viz.add_group("g")
        assert isinstance(ref, VizObjectRef)
        assert ref.id in viz._scenes[""]._nodes
        assert viz._scenes[""].get_node(ref.id).kind == "VizGroup"

    def test_group_new_attaches_child(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        grp = viz.add_group("g")
        child = grp.new(Point(1, 2, 3))
        assert child.parent is not None
        assert child.parent.id == grp.id

    def test_parent_id_add(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        grp = viz.add_group("g")
        eid = viz.add(Point(1, 2, 3), parent_id=grp.id)
        node = viz._scenes[""].get_node(eid)
        assert node.parent is not None
        assert node.parent.id == grp.id

    def test_attach_to_label(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        other = viz.add(Point(1, 1, 1))
        viz.add(Point(0, 0, 0), label="L", attach_to=other)
        label_ids = viz._scenes[""].get_label_ids(other)
        assert len(label_ids) == 1

    def test_update_control(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add_slider("s", min=0.0, max=1.0)
        viz.update_control("s", max=10.0)
        assert viz._scenes[""]._controls["s"].max == 10.0

    def test_scene_handle_new(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("s")
        ref = h.new(Point(1, 2, 3))
        assert isinstance(ref, VizObjectRef)
        assert ref.scene_name == "s"
        assert ref.id in viz._scenes["s"]._nodes

    def test_scene_handle_add_group(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        h = viz.scene("s")
        ref = h.add_group("g")
        assert isinstance(ref, VizObjectRef)
        assert ref.scene_name == "s"
        assert ref.id in viz._scenes["s"]._nodes

    def test_add_backward_compat(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        eid = viz.add(Point(1, 2, 3), color="#ff4444")
        assert isinstance(eid, str)
        assert viz._scenes[""].entity_count == 1
