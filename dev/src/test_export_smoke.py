#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Smoke test for Phase 11 scene export (HTML + glTF).

Verifies that both export formats produce valid output for all entity
and operator types, including labels and camera configuration.
"""

from __future__ import annotations

import json
import struct

import pytest
from pytanga.geometry import (
    Circle,
    Dilator,
    Direction,
    GeneralDilator,
    GeneralRotor,
    HPoint,
    Inversion,
    Line,
    Motor,
    Plane,
    Point,
    PointPair,
    ReflectionLine,
    ReflectionOrigin,
    ReflectionPlane,
    Rotor,
    Space,
    Sphere,
    Translator,
)
from pytanga.viz import CameraConfig, Visualizer

_GLTF_MAGIC = 0x46546C67


def _make_full_scene() -> Visualizer:
    """Create a Visualizer with one of each entity/operator type."""
    viz = Visualizer(
        camera=CameraConfig(position=(10, 6, 12), target=(0, 0, 0), fov=45),
        space_extent=15,
    )

    # Entities
    viz.add(Point(2, 0, 0), label="Pt")
    viz.add(Direction(1, 1, 0))
    viz.add(HPoint(point=Point(1, 0, 0)))
    viz.add(PointPair(point_a=Point(-1, 0, 0), point_b=Point(1, 0, 0)))
    viz.add(Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)))
    viz.add(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)))
    viz.add(Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2))
    viz.add(Sphere(Point(0, 0, 0), 2.5))
    viz.add(Space())

    # Operators
    viz.add(ReflectionLine(Direction(0, 0, 1)))
    viz.add(ReflectionPlane(Direction(0, 0, 1)))
    viz.add(ReflectionOrigin())
    viz.add(Inversion(center=Point(0, 0, 0)))
    viz.add(Rotor(angle=1.2, axis=Direction(0, 0, 1)))
    viz.add(Translator(vector=Direction(2, 0, 0)))
    viz.add(Dilator(factor=2))
    viz.add(
        Motor(
            rotor=Rotor(angle=1.5, axis=Direction(0, 0, 1)),
            translator=Translator(vector=Direction(1, 0, 0)),
        )
    )
    viz.add(
        GeneralRotor(
            rotor=Rotor(angle=1.5, axis=Direction(0, 0, 1)),
            translator=Translator(vector=Direction(1, 0, 0)),
        )
    )
    viz.add(GeneralDilator(factor=2, translator=Translator(vector=Direction(1, 0, 0))))

    return viz


class TestHtmlExport:
    """Tests for self-contained HTML export."""

    def test_produces_valid_html(self, tmp_path):
        """export_html() produces a file starting with <!DOCTYPE html>."""
        viz = _make_full_scene()
        path = tmp_path / "scene.html"
        viz.export_snapshot(str(path))
        content = path.read_text()
        assert content.startswith("<!DOCTYPE html>")

    def test_contains_scene_data(self, tmp_path):
        """Exported HTML embeds scene data as JSON."""
        viz = _make_full_scene()
        path = tmp_path / "scene.html"
        viz.export_snapshot(str(path))
        content = path.read_text()
        assert "tanga-scene-data" in content
        assert "tanga-scene-config" in content

    def test_contains_threejs_bootstrap(self, tmp_path):
        """Exported HTML contains THREE.js rendering code."""
        viz = _make_full_scene()
        path = tmp_path / "scene.html"
        viz.export_snapshot(str(path))
        content = path.read_text()
        assert "THREE" in content
        assert "OrbitControls" in content

    def test_scene_data_is_valid_json(self, tmp_path):
        """Embedded scene data parses as valid JSON."""
        viz = _make_full_scene()
        path = tmp_path / "scene.html"
        viz.export_snapshot(str(path))
        content = path.read_text()

        # Extract the JSON from the script tag
        import re

        match = re.search(
            r'<script type="application/json" id="tanga-scene-data">(.+?)</script>',
            content,
            re.DOTALL,
        )
        assert match is not None, "Could not find tanga-scene-data script tag"
        data = json.loads(match.group(1))
        assert isinstance(data, dict)
        assert "entities" in data
        assert "labels" in data

    def test_empty_scene(self, tmp_path):
        """Export of an empty scene produces valid HTML."""
        viz = Visualizer()
        path = tmp_path / "empty.html"
        viz.export_snapshot(str(path))
        content = path.read_text()
        assert content.startswith("<!DOCTYPE html>")

    def test_label_included(self, tmp_path):
        """Entities with labels include label data in the export."""
        viz = Visualizer()
        viz.add(Point(1, 2, 3), label="MyLabel")
        path = tmp_path / "labeled.html"
        viz.export_snapshot(str(path))
        content = path.read_text()
        assert "MyLabel" in content


class TestGltfExport:
    """Tests for glTF 2.0 binary export."""

    def test_produces_valid_glb_header(self, tmp_path):
        """export_glb() produces a file with correct glTF magic and version."""
        viz = _make_full_scene()
        path = tmp_path / "scene.glb"
        viz.export_glb(str(path))
        data = path.read_bytes()
        assert len(data) >= 20
        magic = struct.unpack("<I", data[0:4])[0]
        version = struct.unpack("<I", data[4:8])[0]
        assert magic == _GLTF_MAGIC
        assert version == 2

    def test_glb_contains_valid_json_chunk(self, tmp_path):
        """The JSON chunk in the .glb file must be valid JSON."""
        viz = _make_full_scene()
        path = tmp_path / "scene.glb"
        viz.export_glb(str(path))
        data = path.read_bytes()
        # Skip 12-byte header
        json_len = struct.unpack("<I", data[12:16])[0]
        json_type = struct.unpack("<I", data[16:20])[0]
        assert json_type == 0x4E4F534A  # "JSON"
        json_bytes = data[20 : 20 + json_len]
        gltf = json.loads(json_bytes)
        assert gltf["asset"]["version"] == "2.0"
        assert "scenes" in gltf or "meshes" in gltf

    def test_glb_has_meshes(self, tmp_path):
        """A scene with entities produces glTF meshes."""
        viz = _make_full_scene()
        path = tmp_path / "scene.glb"
        viz.export_glb(str(path))
        data = path.read_bytes()
        json_len = struct.unpack("<I", data[12:16])[0]
        json_bytes = data[20 : 20 + json_len]
        gltf = json.loads(json_bytes)
        assert "meshes" in gltf
        assert len(gltf["meshes"]) > 0

    def test_glb_with_camera(self, tmp_path):
        """Camera config produces a glTF camera node."""
        viz = Visualizer(camera=CameraConfig(position=(10, 6, 12), fov=45))
        viz.add(Point(0, 0, 0))
        path = tmp_path / "camera.glb"
        viz.export_glb(str(path))
        data = path.read_bytes()
        json_len = struct.unpack("<I", data[12:16])[0]
        json_bytes = data[20 : 20 + json_len]
        gltf = json.loads(json_bytes)
        assert "cameras" in gltf

    def test_empty_scene_glb(self, tmp_path):
        """Export of an empty scene produces a valid glTF file with no meshes."""
        viz = Visualizer()
        path = tmp_path / "empty.glb"
        viz.export_glb(str(path))
        data = path.read_bytes()
        magic = struct.unpack("<I", data[0:4])[0]
        assert magic == _GLTF_MAGIC

    def test_all_entity_types_export(self, tmp_path):
        """Each entity kind can be exported to glTF without error."""
        viz = Visualizer()
        entities = [
            Point(1, 2, 3),
            Direction(1, 0, 0),
            HPoint(point=Point(1, 0, 0)),
            PointPair(point_a=Point(-1, 0, 0), point_b=Point(1, 0, 0)),
            Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
            Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
            Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2),
            Sphere(Point(0, 0, 0), 2.5),
            Space(),
        ]
        for ent in entities:
            viz.add(ent)
        path = tmp_path / "entities.glb"
        viz.export_glb(str(path))
        data = path.read_bytes()
        assert struct.unpack("<I", data[0:4])[0] == _GLTF_MAGIC

    def test_all_operator_types_export(self, tmp_path):
        """Each operator kind can be exported to glTF without error."""
        viz = Visualizer()
        operators = [
            ReflectionLine(Direction(0, 0, 1)),
            ReflectionPlane(Direction(0, 0, 1)),
            ReflectionOrigin(),
            Inversion(center=Point(0, 0, 0)),
            Rotor(angle=1.2, axis=Direction(0, 0, 1)),
            Translator(vector=Direction(2, 0, 0)),
            Dilator(factor=2),
            Motor(
                rotor=Rotor(angle=1.5, axis=Direction(0, 0, 1)),
                translator=Translator(vector=Direction(1, 0, 0)),
            ),
            GeneralRotor(
                rotor=Rotor(angle=1.5, axis=Direction(0, 0, 1)),
                translator=Translator(vector=Direction(1, 0, 0)),
            ),
            GeneralDilator(factor=2, translator=Translator(vector=Direction(1, 0, 0))),
        ]
        for op in operators:
            viz.add(op)
        path = tmp_path / "operators.glb"
        viz.export_glb(str(path))
        data = path.read_bytes()
        assert struct.unpack("<I", data[0:4])[0] == _GLTF_MAGIC


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
