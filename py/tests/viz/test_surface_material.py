# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Unit tests for the surface material model and its style serialization."""

from __future__ import annotations

import numpy as np

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ImageData,
    SphereStyle,
    SurfaceMaterial,
    SurfaceShader,
    SurfaceTexture,
    checkerboard,
    gradient,
    grid,
    sphere_coloring,
    surface_material,
)
from pytanga.viz.serializer import serialize_entity


def _texture() -> SurfaceTexture:
    data = np.zeros((4, 6, 3), dtype=np.uint8)
    return SurfaceTexture(image=ImageData("tex0", data=data))


def test_surface_shader_to_dict_omits_vertex_when_none() -> None:
    shader = SurfaceShader("s", "vec3 surfaceColor(vec3 b, vec3 n, vec3 p){ return b; }")
    payload = shader.to_dict()
    assert payload["name"] == "s"
    assert "vertex" not in payload
    assert payload["uniforms"] == {}


def test_surface_material_to_dict_defaults() -> None:
    assert SurfaceMaterial().to_dict() == {"shader": None, "textures": []}


def test_surface_material_normalization() -> None:
    assert surface_material() == SurfaceMaterial()

    shader = checkerboard()
    material = surface_material(shader)
    assert material.shader is shader
    assert material.textures == []

    tex = _texture()
    textures = surface_material(tex).textures
    assert len(textures) == 1 and textures[0] is tex

    textures = surface_material([tex, tex]).textures
    assert len(textures) == 2 and textures[0] is tex and textures[1] is tex


def test_surface_texture_wire_meta() -> None:
    payload = _texture().to_dict()
    assert payload["id"] == "tex0"
    assert payload["width"] == 6
    assert payload["height"] == 4
    assert payload["channels"] == 3
    assert payload["dtype"] == 0
    assert payload["source"] == "data"
    assert payload["uniform"] == "uTexture0"
    assert payload["wrap_s"] == "repeat"
    assert payload["wrap_t"] == "repeat"


def test_sphere_style_serializes_surface() -> None:
    style = SphereStyle(surface=surface_material(checkerboard()))
    payload = style.to_dict()
    assert payload["surface"]["shader"]["name"] == "checkerboard"
    assert payload["surface"]["textures"] == []


def test_serialize_entity_emits_surface() -> None:
    style = SphereStyle(surface=surface_material(checkerboard()))
    entity = serialize_entity(Sphere(Point(0.0, 0.0, 0.0), 1.0), "e0", {"style": style})
    assert entity["style"]["surface"]["shader"]["name"] == "checkerboard"


def test_standard_shaders_are_host_fragments() -> None:
    for shader in (checkerboard(), sphere_coloring(), grid(), gradient()):
        assert shader.fragment.strip()
        assert "main(" not in shader.fragment
        assert "#version" not in shader.fragment
