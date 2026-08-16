# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Entity/Operator → JSON serialization."""

import json

import pytest
from pytanga.geometry.entities import (
    Circle,
    Direction,
    HPoint,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)
from pytanga.geometry.operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    Motor,
    ReflectionLine,
    ReflectionPlane,
    ReflectionPoint,
    Rotor,
    Translator,
)
from pytanga.viz._styles import _DEFAULT_STYLE_FOR_KIND as _CANONICAL
from pytanga.viz.serializer import (
    serialize_entity,
    serialize_object_update,
    serialize_scene_update,
)

# ── Helpers ────────────────────────────────────────────────


def _serialize(ent, props=None, *, styles_map=None):
    """Serialize using the canonical defaults (fresh copy each time)."""
    from copy import copy

    sm = (
        {k: copy(v) for k, v in _CANONICAL.items()}
        if styles_map is None
        else styles_map
    )
    return serialize_entity(
        ent,
        "test_id",
        properties=props,
        styles_map=sm,
    )


# ── Entities ────────────────────────────────────────────────


class TestSerializeEntities:
    def test_point(self):
        d = _serialize(Point(1.5, 2.5, 3.5))
        assert d["id"] == "test_id"
        assert d["kind"] == "Point"
        assert d["position"] == [1.5, 2.5, 3.5]
        assert d["color"] == "#ff4444"

    def test_point_with_color_override(self):
        d = _serialize(Point(0, 0, 0), {"color": "#00ff00"})
        assert d["color"] == "#00ff00"

    def test_direction(self):
        d = _serialize(Direction(1, 0, 0))
        assert d["kind"] == "Direction"
        assert d["vector"] == [1, 0, 0]
        assert d["length"] == 2.0

    def test_homogeneous_point(self):
        hp = HPoint(point=Point(1, 2, 3), weight=2.0)
        d = _serialize(hp)
        assert d["kind"] == "HPoint"
        assert d["position"] == [1, 2, 3]
        assert d["weight"] == 2.0

    def test_point_pair(self):
        pp = PointPair(point_a=Point(0, 0, 0), point_b=Point(1, 1, 1))
        d = _serialize(pp)
        assert d["kind"] == "PointPair"
        assert d["pointA"] == [0, 0, 0]
        assert d["pointB"] == [1, 1, 1]
        assert d["lineThickness"] == 0.02
        assert d["pointSize"] == 0.06

    def test_line(self):
        l = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
        d = _serialize(l)
        assert d["kind"] == "Line"
        assert d["origin"] == [0, 0, 0]
        assert d["direction"] == [1, 0, 0]
        assert d["thickness"] == 0.03
        assert d["length"] == 20.0

    def test_plane(self):
        p = Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1))
        d = _serialize(p)
        assert d["kind"] == "Plane"
        assert d["point"] == [0, 0, 3]
        assert d["normal"] == [0, 0, 1]
        assert d["opacity"] == 0.3
        assert d["extent"] == 10.0

    def test_circle(self):
        c = Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=3.0)
        d = _serialize(c)
        assert d["kind"] == "Circle"
        assert d["center"] == [0, 0, 0]
        assert d["normal"] == [0, 0, 1]
        assert d["radius"] == 3.0
        assert d["tubeRadius"] == 0.03

    def test_circle_radius_clamped(self):
        c = Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=0.0)
        d = _serialize(c)
        assert d["radius"] == 0.001

    def test_sphere(self):
        s = Sphere(center=Point(0, 0, 0), radius=2.5)
        d = _serialize(s)
        assert d["kind"] == "Sphere"
        assert d["center"] == [0, 0, 0]
        assert d["radius"] == 2.5
        assert d["style"]["wireframe"] is True
        assert d["style"]["opacity"] == 0.4
        assert d["style"]["color"] == "#ffaa00"

    def test_sphere_radius_clamped(self):
        d = _serialize(Sphere(Point(0, 0, 0), radius=-0.5))
        assert d["radius"] == 0.001

    def test_space(self):
        d = _serialize(Space())
        assert d["kind"] == "Space"
        assert d["opacity"] == 0.1
        assert d["extent"] == 10.0
        assert d["scale"] == 1.0

    def test_all_json_serializable(self):
        entities = [
            Point(1, 2, 3),
            Direction(0, 1, 0),
            HPoint(point=Point(0, 0, 0)),
            PointPair(point_a=Point(0, 0, 0), point_b=Point(1, 0, 0)),
            Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
            Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1)),
            Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=1),
            Sphere(center=Point(0, 0, 0), radius=1),
            Space(),
        ]
        for ent in entities:
            d = _serialize(ent)
            json.dumps(d)  # should not raise


# ── Operators ───────────────────────────────────────────────


class TestSerializeOperators:
    def test_reflection_plane(self):
        r = ReflectionPlane(Direction(0, 0, 1))
        d = _serialize(r)
        assert d["kind"] == "ReflectionPlane"
        assert d["normal"] == [0, 0, 1]
        assert d["color"] == "#88ccff"
        assert d["opacity"] == 0.35
        assert d["extent"] == 5.0

    def test_reflection_line(self):
        r = ReflectionLine(Direction(0, 0, 1))
        d = _serialize(r)
        assert d["kind"] == "ReflectionLine"
        assert d["direction"] == [0, 0, 1]
        assert d["color"] == "#aaccff"

    def test_reflection_origin(self):
        r = ReflectionPoint(Point(0, 0, 0))
        d = _serialize(r)
        assert d["origin"] == [0, 0, 0]
        assert d["color"] == "#ffffff"

    def test_inversion(self):
        i = Inversion(center=Point(1, 2, 3))
        d = _serialize(i)
        assert d["kind"] == "Inversion"
        assert d["center"] == [1, 2, 3]
        assert d["radius"] == 1.0
        assert d["color"] == "#cc88ff"

    def test_rotor(self):
        r = Rotor(angle=1.5708, axis=Direction(0, 0, 1))
        d = _serialize(r)
        assert d["kind"] == "Rotor"
        assert d["angle"] == 1.5708
        assert d["axis"] == [0, 0, 1]
        assert d["color"] == "#ff8844"
        assert d["discRadius"] == 1.5

    def test_translator(self):
        t = Translator(vector=Direction(2, 0, 0))
        d = _serialize(t)
        assert d["kind"] == "Translator"
        assert d["vector"] == [2, 0, 0]
        assert d["color"] == "#44aaff"
        assert d["length"] == 3.0

    def test_dilator(self):
        d_obj = Dilator(factor=2.0)
        d = _serialize(d_obj)
        assert d["kind"] == "Dilator"
        assert d["factor"] == 2.0
        assert d["color"] == "#ffcc44"
        assert d["ringCount"] == 4
        assert d["maxRadius"] == 3.0

    def test_motor(self):
        m = Motor(
            rotor=Rotor(angle=0.5, axis=Direction(0, 0, 1)),
            translator=Translator(vector=Direction(2, 0, 0)),
        )
        d = _serialize(m)
        assert d["kind"] == "Motor"
        assert d["rotor"]["angle"] == 0.5
        assert d["rotor"]["axis"] == [0, 0, 1]
        assert d["translator"]["vector"] == [2, 0, 0]

    def test_general_rotor(self):
        gr = GeneralRotor(
            angle=0.5,
            axis=Direction(0, 1, 0),
            origin=Point(1, 0, 0),
        )
        d = _serialize(gr)
        assert d["kind"] == "GeneralRotor"
        assert d["angle"] == 0.5
        assert d["axis"] == [0, 1, 0]
        assert d["origin"] == [1, 0, 0]
        assert d["color"] == "#ff9966"

    def test_dilator_with_offset_origin(self):
        gd = Dilator(factor=2.0, origin=Point(1, 2, 3))
        d = _serialize(gd)
        assert d["kind"] == "Dilator"
        assert d["factor"] == 2.0
        assert d["origin"] == [1.0, 2.0, 3.0]

    def test_dilator_at_origin(self):
        gd = Dilator(factor=3.0)
        d = _serialize(gd)
        assert d["kind"] == "Dilator"
        assert d["factor"] == 3.0
        assert d["origin"] == [0.0, 0.0, 0.0]

    def test_all_operators_json_serializable(self):
        ops = [
            ReflectionPlane(Direction(1, 0, 0)),
            ReflectionLine(Direction(1, 0, 0)),
            ReflectionPoint(Point(0, 0, 0)),
            Inversion(center=Point(0, 0, 0)),
            Rotor(angle=0.5, axis=Direction(0, 0, 1)),
            Translator(vector=Direction(1, 0, 0)),
            Dilator(factor=2.0),
            Dilator(factor=1.5, origin=Point(1, 0, 0)),
            Motor(
                rotor=Rotor(angle=0.5, axis=Direction(0, 0, 1)),
                translator=Translator(vector=Direction(1, 0, 0)),
            ),
            GeneralRotor(
                angle=0.5,
                axis=Direction(0, 0, 1),
                origin=Point(0, 0, 0),
            ),
        ]
        for op in ops:
            d = _serialize(op)
            json.dumps(d)


# ── Style override tests ────────────────────────────────────


class TestStyleOverrides:
    def test_style_override_color(self):
        """Style with explicit color overrides the canonical default."""
        from pytanga.viz._styles import PointStyle

        d = _serialize(Point(0, 0, 0), {"style": PointStyle(color="#0000ff")})
        assert d["color"] == "#0000ff"

    def test_per_entity_overrides_style(self):
        """Per-entity properties take priority over style."""
        from pytanga.viz._styles import PointStyle

        d = _serialize(
            Point(0, 0, 0),
            {"color": "#ff0000", "style": PointStyle(color="#0000ff")},
        )
        assert d["color"] == "#ff0000"

    def test_style_mutates_default_line_length(self):
        """Mutating canonical style changes serialized length."""
        from copy import copy

        from pytanga.viz._styles import _DEFAULT_STYLE_FOR_KIND as _CANONICAL

        styles_map = {k: copy(v) for k, v in _CANONICAL.items()}
        styles_map["Line"].length = 50.0
        d = _serialize(
            Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
            styles_map=styles_map,
        )
        assert d["length"] == 50.0

    def test_style_plane_extent(self):
        from copy import copy

        from pytanga.viz._styles import _DEFAULT_STYLE_FOR_KIND as _CANONICAL

        styles_map = {k: copy(v) for k, v in _CANONICAL.items()}
        styles_map["Plane"].extent = 25.0
        d = _serialize(
            Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1)),
            styles_map=styles_map,
        )
        assert d["extent"] == 25.0

    def test_sphere_style_opacity(self):
        """Sphere default opacity comes from canonical style."""
        from copy import copy

        from pytanga.viz._styles import _DEFAULT_STYLE_FOR_KIND as _CANONICAL

        styles_map = {k: copy(v) for k, v in _CANONICAL.items()}
        d = _serialize(Sphere(Point(0, 0, 0), 1.0), styles_map=styles_map)
        assert d["style"]["opacity"] == 0.4

    def test_unknown_type_raises(self):
        with pytest.raises(TypeError, match="Unknown entity type"):
            _serialize("not_an_entity")


# ── Scene update wrapper ───────────────────────────────────


class TestSceneUpdate:
    def test_wrapper_format(self):
        msg = serialize_scene_update(
            [{"id": "a", "kind": "Point"}],
            ["b"],
        )
        assert msg["type"] == "scene_update"
        assert msg["objects"] == [{"id": "a", "kind": "Point"}]
        assert msg["removed"] == ["b"]

    def test_empty(self):
        msg = serialize_scene_update([], [])
        assert msg["type"] == "scene_update"
        assert msg["objects"] == []
        assert msg["removed"] == []

    def test_with_labels(self):
        msg = serialize_scene_update(
            [{"id": "a", "kind": "Point"}],
            [],
            labels=[{"id": "l1", "kind": "label", "text": "X"}],
        )
        assert len(msg["objects"]) == 2
        assert msg["objects"][1]["text"] == "X"


# ── Object update wrapper ───────────────────────────────────


class TestObjectUpdate:
    def test_wrapper_format(self):
        msg = serialize_object_update(
            [{"id": "a", "aspect": "full", "value": {"kind": "Point"}}],
            ["b"],
        )
        assert msg["type"] == "object_update"
        assert msg["scene"] == ""
        assert msg["patches"] == [{"id": "a", "aspect": "full", "value": {"kind": "Point"}}]
        assert msg["removed"] == ["b"]

    def test_empty(self):
        msg = serialize_object_update([], [])
        assert msg["type"] == "object_update"
        assert msg["patches"] == []
        assert msg["removed"] == []
