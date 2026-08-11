# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Texture label style for the Tanga 3D viewer.

A :class:`TextureLabelStyle` defines a label (plain text, KaTeX formula,
or mixed text with embedded ``$...$`` / ``$$...$$`` math) that is rendered
onto a canvas and applied as a :class:`THREE.CanvasTexture` on entity surfaces
(spheres, planes).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TextureLabelStyle:
    """Visual style for texture labels on entity surfaces.

    Rendered via ``createTextureLabel()`` on the JS frontend using a
    **Canvas → CanvasTexture** pipeline.  Supports three content modes:

    * **Math mode** (``math_mode=True``): the entire ``text`` is treated
      as a KaTeX formula and rendered via ``katex.renderToString()``.
    * **Mixed mode** (``math_mode=False``, text contains ``$...$`` or
      ``$$...$$``): plain text segments are drawn with ``ctx.fillText()``,
      formula segments are rendered with KaTeX and composited.
    * **Plain text mode** (``math_mode=False``, no ``$`` delimiters):
      rendered as-is with ``ctx.fillText()``.

    When ``text`` is ``None``, no texture is produced — the entity renders
    with its plain material color.

    Attributes:
        text: Label content.  Can be a plain string, a KaTeX formula
            (``math_mode=True``), or mixed text with embedded ``$...$``
            (inline) and ``$$...$$`` (display) delimiters.
        math_mode: When ``True``, the entire ``text`` is treated as a
            single KaTeX formula.  When ``False``, ``$`` delimiters are
            auto-detected for embedded math.
        repeat_u: Texture repeat count along the U axis (longitude on
            spheres, X on planes).  ``None`` uses the canvas default.
        repeat_v: Texture repeat count along the V axis (latitude on
            spheres, Y on planes).
        offset_u: UV offset along U.  Shifts the label horizontally.
        offset_v: UV offset along V.  For spheres, set to ``0.25`` to
            center the label at the equator (V=0.5).  For planes,
            ``0.0`` centers on the quad.
        align: Plane-only layout mode.  ``"stretch"`` fills the quad
            (default), ``"fit"`` preserves aspect ratio, ``"repeat"``
            tiles with ``repeat_u``/``repeat_v``.  Ignored for spheres.
        background: Canvas background CSS color.  ``None`` or
            ``"transparent"`` produces a transparent background (entity
            material color shows through).  Default ``"#ffffff"``.
        resolution: Canvas width in pixels.  Height is ``resolution // 2``
            (2:1 aspect ratio matches standard UV mapping).  Higher
            values produce sharper labels but use more GPU memory.
        color: Text/formula CSS color.  Passed to KaTeX ``\\color{}``
            or used as ``ctx.fillStyle``.
        font_size: Font size in CSS pixels for plain text rendering.
            Ignored when ``math_mode=True`` (KaTeX controls its own
            sizing via its CSS).
        scale: Overall size of the texture content.
            1.0 = native size, 2.0 = twice as large, 0.5 = half size.
            ``None`` defaults to 1.0.
        aspect: Height‑to‑width ratio of the texture bounding box.
            1.0 = square, 2.0 = twice as tall, 0.5 = half as tall.
            Sphere per‑kind default is 0.5 to counteract UV stretching.
    """

    text: str | None = None
    math_mode: bool | None = False
    repeat_u: float | None = None
    repeat_v: float | None = None
    offset_u: float | None = None
    offset_v: float | None = None
    align: str | None = None
    background: str | None = "#ffffff"
    resolution: int | None = 512
    color: str | None = "#000000"
    font_size: int | None = 48
    scale: float | None = None
    aspect: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize non-``None`` fields to a JSON-ready dict.

        The ``style_type`` discriminator is ``"TextureLabelStyle"``.
        Fields with value ``None`` are omitted so the frontend falls
        back to its own defaults.
        """
        result: dict[str, Any] = {"style_type": "TextureLabelStyle"}
        if self.text is not None:
            result["text"] = self.text
        if self.math_mode is not None:
            result["math_mode"] = self.math_mode
        if self.repeat_u is not None:
            result["repeat_u"] = self.repeat_u
        if self.repeat_v is not None:
            result["repeat_v"] = self.repeat_v
        if self.offset_u is not None:
            result["offset_u"] = self.offset_u
        if self.offset_v is not None:
            result["offset_v"] = self.offset_v
        if self.align is not None:
            result["align"] = self.align
        if self.background is not None:
            result["background"] = self.background
        if self.resolution is not None:
            result["resolution"] = self.resolution
        if self.color is not None:
            result["color"] = self.color
        if self.font_size is not None:
            result["font_size"] = self.font_size
        if self.scale is not None:
            result["scale"] = self.scale
        if self.aspect is not None:
            result["aspect"] = self.aspect
        return result
