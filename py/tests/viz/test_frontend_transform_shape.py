# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the Python-authorized frontend object_update message shapes."""

from pytanga.geometry.entities import Point
from pytanga.viz._label import Label
from pytanga.viz.scene import Scene
from pytanga.viz.serializer import serialize_object_update


class TestFrontendTransformShape:
    def test_object_update_message_shape(self):
        msg = serialize_object_update(
            [{"id": "a", "aspect": "full", "value": {"id": "a", "kind": "Point"}}],
            ["b"],
        )
        assert msg["type"] == "object_update"
        assert "patches" in msg
        assert msg["removed"] == ["b"]

    def test_full_patch_includes_parent_and_transform(self):
        s = Scene()
        g = s.add_group("g")
        eid = s.add(Point(1, 2, 3))
        node = s.get_node(eid)
        g.add_child(node)
        patch = node.patch("full")
        assert patch["value"]["parent_id"] == g.id
        assert "transform" in patch["value"]
        assert patch["value"]["transform"]["position"] == [0.0, 0.0, 0.0]

    def test_style_patch_shape(self):
        s = Scene()
        eid = s.add(Point(0, 0, 0))
        node = s.get_node(eid)
        node.set_color("#ff0000")
        patch = node.patch("style")
        assert patch["aspect"] == "style"
        assert set(patch["value"].keys()) == {"style"}

    def test_transform_patch_shape(self):
        s = Scene()
        eid = s.add(Point(0, 0, 0))
        node = s.get_node(eid)
        node.translate(1, 2, 3)
        patch = node.patch("transform")
        assert patch["aspect"] == "transform"
        assert set(patch["value"].keys()) == {"position", "rotation", "scale"}

    def test_content_patch_shape(self):
        s = Scene()
        eid = s.add(Point(0, 0, 0))
        node = s.get_node(eid)
        node.consume_dirty()
        node.set_entity(Point(1, 2, 3))
        patch = node.patch("content")
        assert patch["aspect"] == "content"
        assert patch["value"]["kind"] == "Point"
        assert "position" in patch["value"]
        assert "transform" not in patch["value"]
        assert "parent_id" not in patch["value"]

    def test_overlay_patch_has_attach_to(self):
        s = Scene()
        s.add(Point(0, 0, 0))
        lid = s.add_label(Label(text="X", position=(0, 0, 0), parent_id="p"))
        patch = s.get_node(lid).patch("full")
        assert patch["value"]["attach_to"] == "p"
        assert "transform" not in patch["value"]

    def test_group_kind_in_state(self):
        s = Scene()
        g = s.add_group("g")
        state = s.full_state()
        kinds = {d["kind"] for d in state}
        assert "VizGroup" in kinds
        assert g.id in {d["id"] for d in state}

    def test_dfs_preorder(self):
        s = Scene()
        parent = s.add_group("parent")
        child_group = s.add_group("child_group")
        parent.add_child(child_group)
        point = s.get_node(s.add(Point(0, 0, 0)))
        child_group.add_child(point)

        order = [n.id for n in s._dfs_preorder()]
        assert order.index(parent.id) < order.index(child_group.id)
        assert order.index(child_group.id) < order.index(point.id)
