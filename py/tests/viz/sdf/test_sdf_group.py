# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the SDF group serializer (standard viewer)."""

from __future__ import annotations

import math

import pytest
from pytanga.geometry import Direction, GeneralRotor, Point, Rotor
from pytanga.viz import SdfStyle, Visualizer
from pytanga.viz.sdf import Composed, SdfGroup, capped_cylinder, sphere
from pytanga.viz.sdf.serializer import serialize_entity_local


def test_sdf_group_serializes_kind_sdf() -> None:
    group = SdfGroup(sphere(1.0), (capped_cylinder(0.6, 0.4), "subtract"))
    result = serialize_entity_local(group, "g", {"style": SdfStyle(color="#44ff44")})
    assert result["kind"] == "sdf"
    assert result["sdfKind"] == "SdfGroup"
    assert result["tree"]["kind"] == "group"
    assert len(result["tree"]["children"]) == 2
    assert len(result["members"]) == 2
    assert result["color"] == "#44ff44"


def test_sdf_group_members_have_transform_and_bound() -> None:
    group = SdfGroup(sphere(1.0), (capped_cylinder(0.6, 0.4), "intersection"))
    result = serialize_entity_local(group, "g", {"style": SdfStyle()})
    for member in result["members"]:
        assert set(member) == {"transform", "bound"}
        assert "position" in member["transform"]
        assert "rotation" in member["transform"]
        assert "scale" in member["transform"]
        for v in member["bound"]["min"] + member["bound"]["max"]:
            assert math.isfinite(v)


def test_sdf_group_union_bound_is_finite_and_centered() -> None:
    group = SdfGroup(sphere(1.0), sphere(0.5, position=(1.5, 0, 0)))
    result = serialize_entity_local(group, "g", {"style": SdfStyle()})
    b = result["bound"]
    for v in b["min"] + b["max"]:
        assert math.isfinite(v)
    # Centered bound: min == -max in every axis.
    for i in range(3):
        assert b["min"][i] == pytest.approx(-b["max"][i])


def test_sdf_group_combine_modes_preserved() -> None:
    group = SdfGroup(sphere(1.0), (capped_cylinder(0.6, 0.4), "subtract"))
    result = serialize_entity_local(group, "g", {"style": SdfStyle()})
    combines = [c["combine"] for c in result["tree"]["children"]]
    assert combines == ["union", "subtract"]


def test_sdf_group_invalid_combine_mode() -> None:
    with pytest.raises(ValueError):
        SdfGroup((sphere(1.0), "bogus"))


def test_visualizer_add_sdf_group() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    oid = viz.add(
        SdfGroup(sphere(1.0), (capped_cylinder(0.6, 0.4), "subtract")),
        style=SdfStyle(color="#44ff44"),
    )
    objs = viz._scene.full_state(styles_map=viz.styles.kind)
    sdf = [o for o in objs if o["id"] == oid]
    assert len(sdf) == 1
    obj = sdf[0]
    assert obj["kind"] == "sdf"
    assert obj["sdfKind"] == "SdfGroup"
    assert len(obj["members"]) == 2


def test_sdf_group_member_composed() -> None:
    # A Composed member (nested CSG) is allowed inside a group.
    bead = Composed(sphere(0.7), (capped_cylinder(1.0, 0.45), "subtract"))
    group = SdfGroup(bead, sphere(0.5, position=(1.5, 0, 0)))
    result = serialize_entity_local(group, "g", {"style": SdfStyle()})
    assert result["sdfKind"] == "SdfGroup"
    assert len(result["members"]) == 2
    # The Composed member serializes to its own group tree.
    assert result["tree"]["children"][0]["kind"] == "group"


def test_sdf_group_member_transform_override() -> None:
    group = SdfGroup(sphere(1.0), (capped_cylinder(0.6, 0.4), "subtract"))
    group.set_member_transform(0, position=(2.0, 0, 0))
    result = serialize_entity_local(group, "g", {"style": SdfStyle()})
    assert result["members"][0]["transform"]["position"] == pytest.approx([2.0, 0.0, 0.0])
    # Member 1 keeps its intrinsic placement (relative to the group origin).
    assert result["members"][1]["transform"]["position"] == pytest.approx([0.0, 0.0, 0.0])


def test_update_sdf_group_member_flushes_content() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    gid = viz.add(
        SdfGroup(sphere(1.0), (capped_cylinder(0.6, 0.4), "subtract")),
        style=SdfStyle(),
    )
    viz._scene.flush(styles_map=viz.styles.kind)  # clear the initial "full" mark

    viz.update_sdf_group_member(gid, 0, position=(3.0, 0, 0))
    patches, _ = viz._scene.flush(styles_map=viz.styles.kind)
    content = [p for p in patches if p["aspect"] == "content"]
    assert len(content) == 1
    value = content[0]["value"]
    assert value["members"][0]["transform"]["position"] == pytest.approx([3.0, 0.0, 0.0])
    # The proxy box resizes (symmetrically) to cover the moved member.
    assert value["bound"]["max"][0] == pytest.approx(3.0 + 1.05)


def test_sdf_group_member_index_error() -> None:
    group = SdfGroup(sphere(1.0))
    with pytest.raises(IndexError):
        group.set_member_transform(5, position=(0, 0, 0))


def test_sdf_group_member_ids() -> None:
    group = SdfGroup(
        sphere(1.0, id="outer"),
        (capped_cylinder(0.6, 0.4, id="drill"), "subtract"),
        sphere(0.5),  # unnamed
    )
    assert group.member_ids == ["outer", "drill", None]


def test_sdf_group_member_ids_serialized_in_tree() -> None:
    group = SdfGroup(
        sphere(1.0, id="outer"),
        (capped_cylinder(0.6, 0.4, id="drill"), "subtract"),
    )
    result = serialize_entity_local(group, "g", {"style": SdfStyle()})
    ids = [c.get("id") for c in result["tree"]["children"]]
    assert ids == ["outer", "drill"]


def test_sdf_group_reference_member_by_id() -> None:
    group = SdfGroup(
        sphere(1.0, id="outer"),
        (capped_cylinder(0.6, 0.4, id="drill"), "subtract"),
    )
    group.set_member_transform("drill", position=(2.0, 0, 0))
    result = serialize_entity_local(group, "g", {"style": SdfStyle()})
    assert result["members"][1]["transform"]["position"] == pytest.approx([2.0, 0.0, 0.0])
    # The untargeted member keeps its intrinsic placement.
    assert result["members"][0]["transform"]["position"] == pytest.approx([0.0, 0.0, 0.0])


def test_sdf_group_unknown_member_id_raises() -> None:
    group = SdfGroup(sphere(1.0, id="outer"))
    with pytest.raises(KeyError):
        group.set_member_transform("nope", position=(0, 0, 0))


def test_viz_new_sdf_group_ref_set_member_transform() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    ref = viz.new(
        SdfGroup(
            sphere(1.0, id="outer"),
            (capped_cylinder(0.6, 0.4, id="drill"), "subtract"),
        ),
        style=SdfStyle(),
    )
    assert isinstance(ref.entity, SdfGroup)
    assert ref.entity.member_ids == ["outer", "drill"]
    viz._scene.flush(styles_map=viz.styles.kind)  # clear the initial "full" mark

    ref.set_member_transform("drill", position=(2.0, 0.0, 0.0))
    patches, _ = viz._scene.flush(styles_map=viz.styles.kind)
    content = [p for p in patches if p["aspect"] == "content"]
    assert len(content) == 1
    assert content[0]["value"]["members"][1]["transform"]["position"] == pytest.approx(
        [2.0, 0.0, 0.0]
    )


def test_sdf_group_entity_change_hook_marks_content() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    ref = viz.new(
        SdfGroup(sphere(1.0, id="outer"), (capped_cylinder(0.6, 0.4, id="drill"), "subtract")),
        style=SdfStyle(),
    )
    viz._scene.flush(styles_map=viz.styles.kind)

    # Mutating directly through `ref.entity` must mark the node's content dirty.
    ref.entity.set_member_transform("outer", position=(0.0, 1.0, 0.0))
    patches, _ = viz._scene.flush(styles_map=viz.styles.kind)
    content = [p for p in patches if p["aspect"] == "content"]
    assert len(content) == 1
    assert content[0]["value"]["members"][0]["transform"]["position"] == pytest.approx(
        [0.0, 1.0, 0.0]
    )


def test_sdf_group_member_rotation_accepts_rotor() -> None:
    group = SdfGroup(
        sphere(1.0, id="outer"),
        (capped_cylinder(0.6, 0.4, id="drill"), "subtract"),
    )
    group.set_member_transform("drill", rotation=Rotor(math.pi / 2.0, Direction(0.0, 0.0, 1.0)))
    result = serialize_entity_local(group, "g", {"style": SdfStyle()})
    # Axis-angle (0,0,1, π/2) → Euler XYZ ≈ (0, 0, π/2).
    assert result["members"][1]["transform"]["rotation"] == pytest.approx(
        [0.0, 0.0, math.pi / 2.0], abs=1e-9
    )


def test_sdf_group_member_position_accepts_point() -> None:
    group = SdfGroup(sphere(1.0, id="outer"), (capped_cylinder(0.6, 0.4, id="drill"), "subtract"))
    group.set_member_transform("drill", position=Point(2.0, 1.0, 0.0))
    result = serialize_entity_local(group, "g", {"style": SdfStyle()})
    assert result["members"][1]["transform"]["position"] == pytest.approx([2.0, 1.0, 0.0])


def test_sdf_group_member_euler_rotation_still_works() -> None:
    group = SdfGroup(sphere(1.0, id="outer"), (capped_cylinder(0.6, 0.4, id="drill"), "subtract"))
    group.set_member_transform("drill", rotation=(0.1, 0.2, 0.3))
    result = serialize_entity_local(group, "g", {"style": SdfStyle()})
    assert result["members"][1]["transform"]["rotation"] == pytest.approx([0.1, 0.2, 0.3])


def test_sdf_group_member_displaced_general_rotor_raises() -> None:
    group = SdfGroup(sphere(1.0, id="outer"))
    displaced = GeneralRotor(0.5, Direction(0.0, 0.0, 1.0), Point(1.0, 0.0, 0.0))
    try:
        group.set_member_transform("outer", rotation=displaced)
    except TypeError as exc:
        assert "displaced origin" in str(exc)
    else:
        raise AssertionError("expected TypeError for a displaced GeneralRotor")



