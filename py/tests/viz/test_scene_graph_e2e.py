# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""End-to-end scene-graph checks: recording, GLTF, and subtree removal."""

from pytanga.geometry.entities import Point, Sphere
from pytanga.viz._nodes import VizGroup, VizSceneObject
from pytanga.viz._styles import SphereStyle, TextureLabelStyle
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
    def test_recording_captures_hierarchy(self):  # noqa: ANN201
        s = _group_scene()
        rec = AnimationRecording(s)
        rec.capture_frame()
        frame = rec.frames[0]
        group = next(d for d in frame if d["kind"] == "VizGroup")
        child = next(d for d in frame if d["kind"] == "Point")
        assert child["parent_id"] == group["id"]
        assert "transform" in child

    def test_remove_group_removes_subtree(self):  # noqa: ANN201
        s = _group_scene()
        nodes = s._dfs_preorder()
        group = next(n for n in nodes if n.kind == "VizGroup")
        child = next(n for n in nodes if n.kind == "Point")
        s.remove(group.id)
        _, removed = s.flush()
        assert group.id in removed
        assert child.id in removed
        assert child.id not in s._nodes

    def test_transform_patch_does_not_resend_children(self):  # noqa: ANN201
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

    def test_gltf_group_hierarchy(self):  # noqa: ANN201
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


class TestDetachedSubtreeE2E:
    def test_detached_tree_roundtrip_and_backfill(self):  # noqa: ANN201
        s = Scene()
        g = VizGroup("g")
        partial = VizSceneObject(
            "partial",
            Sphere(center=Point(0, 0, 0), radius=1.0),
            SphereStyle(color="#ffaa00"),
            kind="Sphere",
        )
        tex = VizSceneObject(
            "tex",
            Sphere(center=Point(1, 0, 0), radius=1.0),
            SphereStyle(texture_label=TextureLabelStyle(text="S₁")),
            kind="Sphere",
        )
        g.add_child(partial)
        g.add_child(tex)

        s.add_viz(g)
        state = s.full_state()
        kinds = [d["kind"] for d in state]
        assert kinds.index("VizGroup") < kinds.index("Sphere")

        partial_dict = next(d for d in state if d["id"] == "partial")
        assert partial_dict["parent_id"] == "g"
        assert partial_dict["style"]["color"] == "#ffaa00"
        assert partial_dict["style"]["style_type"] == "SphereStyle"
        assert "opacity" in partial_dict["style"]  # canonical default backfilled

        tex_dict = next(d for d in state if d["id"] == "tex")
        assert tex_dict["parent_id"] == "g"
        assert tex_dict["style"]["texture_label"]["text"] == "S₁"

    def test_detached_tree_addressability(self):  # noqa: ANN201
        from pytanga.viz._interaction import InteractionConfig

        s = Scene()
        g = VizGroup("g")
        c1 = VizSceneObject("c1", Point(0, 0, 0), kind="Point")
        c2 = VizSceneObject("c2", Point(1, 0, 0), kind="Point")
        g.add_child(c1)
        g.add_child(c2)
        s.add_viz(g)

        assert s.get_node("c1") is c1
        s.update("c1", opacity=0.5)
        assert s.get_node("c1").style["opacity"] == 0.5
        s.update_entity("c1", Point(9, 9, 9))
        node = s.get_node("c1")
        assert (node.entity.x, node.entity.y, node.entity.z) == (9, 9, 9)
        s.set_interaction("c1", InteractionConfig(enabled=True))
        assert s.get_interaction("c1") is not None
        s.remove("c1")
        _, removed = s.flush()
        assert "c1" in removed
        assert "c2" not in removed

    def test_add_group_reparent_flow_unchanged(self):  # noqa: ANN201
        # The pre-existing "add_group + add + re-parent" flow must still work.
        s = Scene()
        group = s.add_group("grp")
        child_id = s.add(Point(1, 2, 3))
        group.add_child(s.get_node(child_id))
        state = s.full_state()
        child = next(d for d in state if d["kind"] == "Point")
        assert child["parent_id"] == group.id
