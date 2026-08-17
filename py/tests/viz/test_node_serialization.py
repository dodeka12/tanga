# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for scene-graph node serialization and aspect-scoped patches."""

import json

from pytanga.geometry.entities import (
    Circle,
    Direction,
    HPoint,
    ImagCircle,
    ImagPointPair,
    ImagSphere,
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
from pytanga.viz._nodes import VizGroup, VizOverlayObject, VizSceneObject
from pytanga.viz._point_path import PointPath
from pytanga.viz._scene_objects import Axes2D, Axes3D, Axis, Grid
from pytanga.viz.scene import Scene
from pytanga.viz.serializer import serialize_entity


class TestNodeSerialization:
    def test_point_serialize(self):
        s = Scene()
        eid = s.add(Point(1.5, 2.5, 3.5))
        d = s.get_node(eid).serialize()
        assert d["id"] == eid
        assert d["layer"] == "scene"
        assert d["kind"] == "Point"
        assert d["parent_id"] is None
        assert d["transform"] == {
            "position": [0.0, 0.0, 0.0],
            "rotation": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
        }
        assert d["visible"] is True
        assert d["position"] == [1.5, 2.5, 3.5]
        assert d["style"]["style_type"] == "PointStyle"

    def test_line_from_points_keeps_segment_length(self):
        # Regression: the node's canonical style default (LineStyle.length=20.0)
        # must not clobber the explicit segment length from Line.from_points.
        s = Scene()
        eid = s.add(Line.from_points(Point(0, 0, 0), Point(2, 0, 0)))
        d = s.get_node(eid).serialize()
        # `length` is a content field carrying the explicit segment length.
        assert d["length"] == 2.0
        # The style `length` stays the default (used only for infinite lines).
        assert d["style"]["length"] == 20.0
        assert d["thickness"] == 1.0
        assert d["style"]["thickness"] == 1.0

    def test_infinite_line_resolves_default_length(self):
        s = Scene()
        eid = s.add(Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)))
        d = s.get_node(eid).serialize()
        # The backend resolves the effective length (default 20.0) so the
        # frontend always receives a valid value.
        assert d["length"] == 20.0
        assert d["style"]["length"] == 20.0

    def test_cylinder_line_style(self):
        from pytanga.viz import CylinderLineStyle

        s = Scene()
        eid = s.add(
            Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
            style=CylinderLineStyle(thickness=0.05),
        )
        d = s.get_node(eid).serialize()
        assert d["style"]["style_type"] == "CylinderLineStyle"
        assert d["style"]["thickness"] == 0.05

    def test_representative_kinds_serialize(self):
        path = PointPath()
        path.add((1, 2, 0), color="#ff0000")
        path.add((3, 1, 0))

        cases = [
            (Point(1, 2, 3), "Point"),
            (Direction(1, 0, 0), "Direction"),
            (HPoint(point=Point(1, 2, 3), weight=2.0), "HPoint"),
            (PointPair(point_a=Point(0, 0, 0), point_b=Point(1, 1, 1)), "PointPair"),
            (Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)), "Line"),
            (Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), "Plane"),
            (Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=3.0), "Circle"),
            (Sphere(center=Point(0, 0, 0), radius=1.0), "Sphere"),
            (Space(), "Space"),
            (path, "PointPath"),
            (Grid(range_u=(-5.0, 5.0), range_v=(-3.0, 3.0)), "Grid"),
            (Axis((0, 0, 0), (3, 0, 0), major_interval=1.0, label="X"), "Axis"),
            (Axes2D(range_u=(0, 2), range_v=(0, 2), labels=("X", "Y")), "Axes2D"),
            (Axes3D(range_u=(0, 2), range_v=(0, 2), range_w=(0, 2), labels=("X", "Y", "Z")), "Axes3D"),
            (ReflectionPlane(Direction(0, 0, 1)), "ReflectionPlane"),
            (ReflectionLine(Direction(0, 0, 1)), "ReflectionLine"),
            (ReflectionPoint(Point(0, 0, 0)), "ReflectionPoint"),
            (Inversion(center=Point(1, 2, 3)), "Inversion"),
            (Rotor(angle=0.5, axis=Direction(0, 0, 1)), "Rotor"),
            (Translator(vector=Direction(2, 0, 0)), "Translator"),
            (Dilator(factor=2.0), "Dilator"),
            (
                Motor(
                    rotor=Rotor(angle=0.5, axis=Direction(0, 0, 1)),
                    translator=Translator(vector=Direction(2, 0, 0)),
                ),
                "Motor",
            ),
            (
                GeneralRotor(angle=0.5, axis=Direction(0, 1, 0), origin=Point(1, 0, 0)),
                "GeneralRotor",
            ),
        ]
        for ent, kind in cases:
            s = Scene()
            eid = s.add(ent)
            d = s.get_node(eid).serialize()
            assert d["kind"] == kind
            assert d["layer"] == "scene"
            assert "parent_id" in d
            assert "transform" in d
            json.dumps(d)  # must not raise

    def test_resolved_style_present(self):
        s = Scene()
        eid = s.add(Point(0, 0, 0), color="#00ff00")
        d = s.get_node(eid).serialize()
        assert d["style"]["color"] == "#00ff00"
        assert d["color"] == "#00ff00"

    def test_imaginary_variants(self):
        s = Scene()
        s.add(ImagPointPair(point_a=Point(0, 0, 0), point_b=Point(1, 0, 0)))
        s.add(ImagCircle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2.0))
        s.add(ImagSphere(center=Point(0, 0, 0), radius=2.0))
        state = s.full_state()
        assert {d["kind"] for d in state} == {"PointPair", "Circle", "Sphere"}
        assert all(d["isImaginary"] is True for d in state)

    def test_aspect_full_patch(self):
        node = VizSceneObject("a", Point(0, 0, 0), {"color": "#ff0000"}, kind="Point")
        node.consume_dirty()
        node.set_entity(Point(1, 2, 3))
        patch = node.patch("full")
        assert patch["id"] == "a"
        assert patch["aspect"] == "full"
        assert patch["value"]["position"] == [1, 2, 3]
        assert patch["value"]["kind"] == "Point"

    def test_aspect_content_patch(self):
        node = VizSceneObject("a", Point(0, 0, 0), {"color": "#ff0000"}, kind="Point")
        node.consume_dirty()
        node.set_entity(Point(1, 2, 3))
        patch = node.patch("content")
        assert patch["id"] == "a"
        assert patch["aspect"] == "content"
        assert patch["value"]["kind"] == "Point"
        assert patch["value"]["position"] == [1, 2, 3]
        assert "parent_id" not in patch["value"]
        assert "transform" not in patch["value"]
        assert "visible" not in patch["value"]
        assert "layer" not in patch["value"]
        assert "id" not in patch["value"]

    def test_aspect_style_patch(self):
        node = VizSceneObject("a", Point(0, 0, 0), {"color": "#ff0000"}, kind="Point")
        node.consume_dirty()
        node.set_color("#00ff00")
        patch = node.patch("style")
        assert patch["aspect"] == "style"
        assert patch["value"] == {"style": {"color": "#00ff00"}}

    def test_aspect_transform_patch(self):
        node = VizSceneObject("a", Point(0, 0, 0), None, kind="Point")
        node.consume_dirty()
        node.translate(1.0, 2.0, 3.0)
        patch = node.patch("transform")
        assert patch["aspect"] == "transform"
        assert patch["value"] == {
            "position": [1.0, 2.0, 3.0],
            "rotation": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
        }

    def test_overlay_label_patch(self):
        node = VizOverlayObject("l", position=(1, 2, 3), attach_to="p", payload="X")
        node.consume_dirty()
        node.set_payload("Y")
        patch = node.patch("full")
        assert patch["value"]["position"] == [1, 2, 3]
        assert patch["value"]["attach_to"] == "p"
        assert patch["value"]["text"] == "Y"
        assert "transform" not in patch["value"]

    def test_full_state_equiv(self):
        s = Scene()
        eid = s.add(Point(1.5, 2.5, 3.5))
        full = s.full_state()[0]
        prior = serialize_entity(Point(1.5, 2.5, 3.5), eid, styles_map=s.default_styles)
        for key, value in prior.items():
            assert full[key] == value
        assert full["parent_id"] is None
        assert "transform" in full
        assert full["visible"] is True

    def test_removed_tracking(self):
        s = Scene()
        eid = s.add(Point(0, 0, 0))
        patches, removed = s.flush()
        assert len(patches) == 1
        assert removed == []

        s.update(eid, color="#ff0000")
        patches, removed = s.flush()
        assert patches[0]["aspect"] == "style"
        assert removed == []

        s.remove(eid)
        patches, removed = s.flush()
        assert removed == [eid]
        assert eid not in s._nodes

    def test_group_serialize_shape(self):
        g = VizGroup("g")
        d = g.serialize()
        assert d["kind"] == "VizGroup"
        assert d["layer"] == "scene"
        assert d["parent_id"] is None
        assert d["transform"]["position"] == [0.0, 0.0, 0.0]
        assert "style" not in d
