# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""End-to-end scene-graph checks: recording, GLTF, and subtree removal."""

from pytanga.geometry.entities import Point
from pytanga.viz.export._animation_recording import AnimationRecording
from pytanga.viz.export._gltf import _GltfBuilder
from pytanga.viz.scene import Scene


def _group_scene() -> Scene:
    s = Scene()
    group = s.add_group("grp")
    child_id = s.add(Point(1, 2, 3))
    group.add_child(s.get_node(child_id))
    return s


class TestSceneGraphE2E:
    def test_recording_captures_hierarchy(self):
        s = _group_scene()
        rec = AnimationRecording(s)
        rec.capture_frame()
        frame = rec.frames[0]
        group = next(d for d in frame if d["kind"] == "VizGroup")
        child = next(d for d in frame if d["kind"] == "Point")
        assert child["parent_id"] == group["id"]
        assert "transform" in child

    def test_remove_group_removes_subtree(self):
        s = _group_scene()
        nodes = s._dfs_preorder()
        group = next(n for n in nodes if n.kind == "VizGroup")
        child = next(n for n in nodes if n.kind == "Point")
        s.remove(group.id)
        _, removed = s.flush()
        assert group.id in removed
        assert child.id in removed
        assert child.id not in s._nodes

    def test_transform_patch_does_not_resend_children(self):
        s = _group_scene()
        s.flush()  # consume initial dirty
        nodes = s._dfs_preorder()
        group = next(n for n in nodes if n.kind == "VizGroup")
        child = next(n for n in nodes if n.kind == "Point")
        group.translate(1.0, 0.0, 0.0)
        patches, _ = s.flush()
        ids = [p["id"] for p in patches]
        assert group.id in ids
        assert child.id not in ids
        assert all(p["aspect"] == "transform" for p in patches)

    def test_gltf_group_hierarchy(self):
        s = _group_scene()
        builder = _GltfBuilder()
        builder.add_entities(s.full_state())
        nodes = s._dfs_preorder()
        group = next(n for n in nodes if n.kind == "VizGroup")
        child = next(n for n in nodes if n.kind == "Point")
        group_idx = builder._node_by_id[group.id]
        child_idx = builder._node_by_id[child.id]
        assert "mesh" not in builder._nodes[group_idx]  # group is an empty node
        assert child_idx in builder._nodes[group_idx].get("children", [])
        assert builder._nodes[child_idx].get("mesh") is not None
