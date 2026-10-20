# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Surface material data model for texture mapping and custom shaders.

A :class:`SurfaceMaterial` describes how a solid surface entity (plane, sphere,
ellipsoid, disk, box, cylinder, cone) is shaded: either a standard texture map
from an image, a custom GLSL program, or both (the program then binds the
supplied textures as samplers).  Pixels travel as binary image frames through
the existing :mod:`pytanga.viz._image_wire` codec; only the metadata is
serialized here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..image import ImageData

_WRAP_MODES = ("repeat", "clamp", "mirror")


@dataclass(frozen=True)
class SurfaceShader:
    """A custom GLSL fragment program that replaces the standard surface shader.

    ``fragment`` is a GLSL body that must **not** contain ``main()`` or a
    ``#version``/``precision`` directive — the host assembles the full shader
    and supplies those.  The host provides the varyings ``vUv``, ``vNormal``,
    ``vWorldPosition`` and ``vLocalPos``, the lighting uniforms
    (``uLightCount``/``uLightDir[]``/``uLightColor[]``/``uAmbientColor``) plus a
    ``tangaLight(albedo, n, p)`` helper, and the uniforms ``u_color`` /
    ``u_opacity`` (the entity's resolved opacity, which the shader may use as it
    likes).  The fragment must define
    ``vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p)``.

    ``uniforms`` holds the runtime values for any extra ``uniform`` declarations
    in ``fragment``; each key must be declared in the fragment.  Array values of
    length 2/3/4 are uploaded as ``vec2``/``vec3``/``vec4``.  Texture samplers
    are declared by the host from each ``SurfaceTexture.uniform`` name — the
    fragment samples them but must not redeclare them.
    """

    name: str
    fragment: str
    vertex: str | None = None
    uniforms: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "fragment": self.fragment,
        }
        if self.vertex is not None:
            result["vertex"] = self.vertex
        result["uniforms"] = dict(self.uniforms)
        return result


@dataclass
class SurfaceTexture:
    """An image used to texture a surface.

    ``image`` is a non-tiled :class:`~pytanga.viz.ImageData` whose pixels travel
    as a binary frame (default codec: JPEG for ``uint8`` 1/3-channel images).
    ``uniform`` is the sampler name a custom shader declares for this texture;
    the standard texture map always uses ``uTexture0``.
    """

    image: ImageData
    uniform: str = "uTexture0"
    repeat_u: float = 1.0
    repeat_v: float = 1.0
    offset_u: float = 0.0
    offset_v: float = 0.0
    wrap_s: str = "repeat"
    wrap_t: str = "repeat"

    def __post_init__(self) -> None:
        for name in ("wrap_s", "wrap_t"):
            value = getattr(self, name)
            if value not in _WRAP_MODES:
                raise ValueError(f"{name} must be one of {_WRAP_MODES}, got {value!r}")

    def to_dict(self) -> dict[str, Any]:
        meta = self.image.layer_meta()
        return {
            "id": meta["id"],
            "uniform": self.uniform,
            "width": meta["width"],
            "height": meta["height"],
            "channels": meta["channels"],
            "dtype": meta["dtype"],
            "source": meta["source"],
            "repeat_u": self.repeat_u,
            "repeat_v": self.repeat_v,
            "offset_u": self.offset_u,
            "offset_v": self.offset_v,
            "wrap_s": self.wrap_s,
            "wrap_t": self.wrap_t,
        }


@dataclass
class SurfaceMaterial:
    """A surface's material: an optional shader plus zero or more textures.

    See the module docstring for the resolution semantics: no shader and one or
    more textures uses only the first texture with the standard texture map; a
    shader replaces the standard shader and binds every texture to its declared
    ``uniform`` sampler.
    """

    shader: SurfaceShader | None = None
    textures: list[SurfaceTexture] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shader": self.shader.to_dict() if self.shader is not None else None,
            "textures": [texture.to_dict() for texture in self.textures],
        }


def surface_material(
    obj: SurfaceMaterial
    | SurfaceShader
    | SurfaceTexture
    | list[SurfaceTexture]
    | tuple[SurfaceTexture, ...]
    | None = None,
) -> SurfaceMaterial:
    """Normalize a convenience input into a :class:`SurfaceMaterial`.

    ``None`` → an empty material (the standard renderer).  A bare
    :class:`SurfaceShader` / :class:`SurfaceTexture` / sequence of textures is
    wrapped accordingly.
    """
    if obj is None:
        return SurfaceMaterial()
    if isinstance(obj, SurfaceMaterial):
        return obj
    if isinstance(obj, SurfaceShader):
        return SurfaceMaterial(shader=obj)
    if isinstance(obj, SurfaceTexture):
        return SurfaceMaterial(textures=[obj])
    if isinstance(obj, (list, tuple)):
        textures = list(obj)
        if not all(isinstance(texture, SurfaceTexture) for texture in textures):
            raise TypeError("a texture sequence must contain only SurfaceTexture values")
        return SurfaceMaterial(textures=textures)
    raise TypeError(
        "surface must be a SurfaceMaterial, SurfaceShader, SurfaceTexture, "
        f"or a sequence of SurfaceTexture values, got {type(obj).__name__}"
    )
