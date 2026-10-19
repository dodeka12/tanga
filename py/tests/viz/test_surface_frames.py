# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for surface-texture frame delivery and the ``surface=`` add API."""

from __future__ import annotations

import numpy as np

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ImageData,
    SurfaceMaterial,
    SurfaceShader,
    SurfaceTexture,
    surface_material,
)
from pytanga.viz.scene import Scene


def _frame_codec(frame: bytes) -> int:
    """Read the codec byte from a v2 image frame (magic 4 + version/type/id_len)."""
    return frame[7]


def _rgb_uint8() -> np.ndarray:
    return np.arange(2 * 2 * 3, dtype=np.uint8).reshape(2, 2, 3)


def test_uint8_surface_texture_uses_jpeg_codec() -> None:
    scene = Scene()
    texture = SurfaceTexture(image=ImageData("t0", data=_rgb_uint8()))
    scene.add_viz(Sphere(Point(0.0, 0.0, 0.0), 1.0), surface=texture)

    frames = scene.surface_texture_frames()
    assert len(frames) == 1
    assert frames[0][0] == "t0"
    assert _frame_codec(frames[0][1]) == 1  # JPEG


def test_float32_surface_texture_uses_zlib_codec() -> None:
    scene = Scene()
    data = np.zeros((2, 2, 3), dtype=np.float32)
    scene.add_viz(
        Sphere(Point(0.0, 0.0, 0.0), 1.0),
        surface=SurfaceTexture(image=ImageData("t1", data=data)),
    )

    frames = scene.surface_texture_frames()
    assert len(frames) == 1
    assert _frame_codec(frames[0][1]) == 2  # ZLIB


def test_add_viz_registers_and_serializes_surface() -> None:
    scene = Scene()
    texture = SurfaceTexture(image=ImageData("t0", data=_rgb_uint8()))
    eid = scene.add_viz(Sphere(Point(0.0, 0.0, 0.0), 1.0), surface=texture)

    dirty, _ = scene.flush()
    value = next(p["value"] for p in dirty if p["id"] == eid)
    assert value["style"]["surface"]["textures"][0]["id"] == "t0"


def test_two_textures_register_two_frames() -> None:
    scene = Scene()
    material = surface_material(
        [
            SurfaceTexture(image=ImageData("a", data=_rgb_uint8())),
            SurfaceTexture(image=ImageData("b", data=_rgb_uint8())),
        ]
    )
    scene.add_viz(Sphere(Point(0.0, 0.0, 0.0), 1.0), surface=material)

    frames = scene.surface_texture_frames()
    assert [frame_id for frame_id, _ in frames] == ["a", "b"]


def test_remove_drops_surface_texture_registry() -> None:
    scene = Scene()
    texture = SurfaceTexture(image=ImageData("t0", data=_rgb_uint8()))
    eid = scene.add_viz(Sphere(Point(0.0, 0.0, 0.0), 1.0), surface=texture)
    scene.remove(eid)

    assert scene.surface_texture_frames() == []


def test_set_surface_uniform_mutates_node_style() -> None:
    scene = Scene()
    material = SurfaceMaterial(
        shader=SurfaceShader(
            "twirl",
            "vec3 surfaceColor(vec3 b, vec3 n, vec3 p){ return b; }",
            uniforms={"u_twirl": 2.0},
        ),
        textures=[SurfaceTexture(image=ImageData("t0", data=_rgb_uint8()), uniform="uTexture")],
    )
    eid = scene.add_viz(Sphere(Point(0.0, 0.0, 0.0), 1.0), surface=material)

    scene.set_surface_uniform(eid, "u_twirl", 6.0)

    node = scene._nodes[eid]
    assert node.style["surface"]["shader"]["uniforms"]["u_twirl"] == 6.0


def test_set_surface_uniform_flushes_as_surface_uniforms_patch() -> None:
    scene = Scene()
    material = SurfaceMaterial(
        shader=SurfaceShader(
            "twirl",
            "vec3 surfaceColor(vec3 b, vec3 n, vec3 p){ return b; }",
            uniforms={"u_twirl": 2.0},
        ),
        textures=[SurfaceTexture(image=ImageData("t0", data=_rgb_uint8()), uniform="uTexture")],
    )
    eid = scene.add_viz(Sphere(Point(0.0, 0.0, 0.0), 1.0), surface=material)
    scene.flush()  # consume the initial "full" patch

    # Queuing does not emit anything yet; multiple changes batch into one patch.
    scene.set_surface_uniform(eid, "u_twirl", 6.0)
    scene.set_surface_uniform(eid, "u_tint", [0.5, 0.5, 0.5])

    dirty, _ = scene.flush()
    patches = [p for p in dirty if p["id"] == eid and p["aspect"] == "surface_uniforms"]
    assert len(patches) == 1
    assert patches[0]["value"]["uniforms"] == {
        "u_twirl": 6.0,
        "u_tint": [0.5, 0.5, 0.5],
    }
