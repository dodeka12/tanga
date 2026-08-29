# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Quadric3D ray rendering (serializer + style default + GLSL)."""

from pathlib import Path

from pytanga.geometry import Quadric3D
from pytanga.viz import RayQuadricStyle, RayStyle
from pytanga.viz._styles import _DEFAULT_STYLE_FOR_KIND
from pytanga.viz.serializer import serialize_entity

_RENDERS_DIR = Path(__file__).parents[2] / "pytanga" / "viz" / "templates" / "renderers"


class TestSerializeQuadric:
    def test_emits_ray_kind_with_coeffs(self):
        q = Quadric3D(tuple(float(i) for i in range(1, 11)))
        d = serialize_entity(q, "q1", kind="Quadric3D")
        assert d["kind"] == "ray"
        assert d["rayKind"] == "Quadric3D"
        assert d["coeffs"] == [float(i) for i in range(1, 11)]
        assert len(d["matrix"]) == 16

    def test_emits_bound(self):
        q = Quadric3D(tuple(float(i) for i in range(1, 11)))
        d = serialize_entity(q, "q1", kind="Quadric3D")
        assert d["bound"]["min"] == [-10.05, -10.05, -10.05]
        assert d["bound"]["max"] == [10.05, 10.05, 10.05]

    def test_resolves_default_color_opacity(self):
        q = Quadric3D(tuple(float(i) for i in range(1, 11)))
        d = serialize_entity(q, "q1", kind="Quadric3D")
        assert d["color"] == "#ffaa00"
        assert d["opacity"] == 0.7


class TestRayQuadricStyle:
    def test_is_default_for_quadric3d(self):
        assert isinstance(_DEFAULT_STYLE_FOR_KIND["Quadric3D"], RayQuadricStyle)
        assert isinstance(_DEFAULT_STYLE_FOR_KIND["Quadric3D"], RayStyle)

    def test_to_dict(self):
        d = RayQuadricStyle().to_dict()
        assert d["style_type"] == "RayQuadricStyle"


class TestQuadricGlsl:
    def test_no_main(self):
        code = (_RENDERS_DIR / "ray" / "quadric.glsl").read_text(encoding="utf-8")
        assert "void main" not in code

    def test_has_intersection_functions(self):
        code = (_RENDERS_DIR / "ray" / "quadric.glsl").read_text(encoding="utf-8")
        assert "float intersectRay" in code
        assert "vec3 normalAt" in code
        assert "uniform mat4 uQuadric" in code

    def test_intersection_is_range_clipped(self):
        code = (_RENDERS_DIR / "ray" / "quadric.glsl").read_text(encoding="utf-8")
        assert "float intersectRay(vec3 ro, vec3 rd, float tMin, float tMax)" in code
        assert "t1 >= tMin && t1 <= tMax" in code
        assert "t2 >= tMin && t2 <= tMax" in code
