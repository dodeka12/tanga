# Phase 1 — `TextureLabelStyle` Dataclass

**Prerequisites:** None (new file, no dependencies on other phases)

**Goal:** Create the `TextureLabelStyle` dataclass with all texture label properties
and JSON serialization. Export from the styles package and the public `viz` API.

---

## 1. Motivation

The existing `ObjVizProps` and per-entity style classes (Phase 4c) control color,
opacity, size, wireframe, etc. — but have no mechanism for applying a
**texture label** (plain text, KaTeX formula, or mixed text+formula) to an
entity's surface. `TextureLabelStyle` fills this gap as an optional field on
entity styles.

It is a standalone dataclass, **not** a subclass of `VizStyle`. It is used as a
**field value** inside entity style dataclasses (e.g., `SphereStyle.texture_label`).

---

## 2. Dataclass Definition

### 2.1 New File: `py/pytanga/viz/_styles/_tex_label_style.py`

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Texture label style for the Tanga 3D viewer.

A :class:`TextureLabelStyle` defines a label (plain text, KaTeX formula,
or mixed text with embedded ``$...$`` / ``$$...$$`` math) that is rendered
onto a canvas and applied as a :class:`THREE.CanvasTexture` on entity surfaces
(spheres, planes).
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
        color: Text/formula CSS color.  Passed to KaTeX ``\color{}``
            or used as ``ctx.fillStyle``.
        font_size: Font size in CSS pixels for plain text rendering.
            Ignored when ``math_mode=True`` (KaTeX controls its own
            sizing via its CSS).
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
        return result
```

### 2.2 Export from `py/pytanga/viz/_styles/__init__.py`

```python
from ._tex_label_style import TextureLabelStyle
```

Add `TextureLabelStyle` to the module-level `__all__` if one exists,
or simply ensure it's importable.

### 2.3 Export from `py/pytanga/viz/__init__.py`

```python
from ._styles import TextureLabelStyle
```

---

## 3. Design Decisions

### 3.1 Not a `VizStyle` Subclass

`TextureLabelStyle` is **not** a `VizStyle` because it is never dispatched on
as a top-level style. It is always a **field** inside another style dataclass
(e.g., `SphereStyle.texture_label`). The `style_type` discriminator is still
included for clarity in the JSON wire format, but the frontend does not dispatch
on it — it reads `ent.style.texture_label` directly.

### 3.2 All Fields Default to `None`

Follows the same pattern as all other style classes in the codebase.
`_style_for_kind()` / `_style_to_output()` merge `None` values with
canonical defaults. The canonical default for `texture_label` is `None`
(no texture), so entities render without a texture label by default.

### 3.3 `text` Field Naming

The field is called `text` (not `formula`) because it can hold plain text,
a KaTeX formula, or mixed content. The `math_mode` flag controls how the
frontend interprets it.

---

## 4. Serialization Example

```python
>>> from pytanga.viz._styles._tex_label_style import TextureLabelStyle
>>> tls = TextureLabelStyle(
...     text=r"\mathcal{S}_1",
...     math_mode=True,
...     repeat_u=4,
...     repeat_v=1,
...     offset_v=0.25,
...     background=None,
...     resolution=1024,
... )
>>> tls.to_dict()
{
    "style_type": "TextureLabelStyle",
    "text": "\\mathcal{S}_1",
    "math_mode": True,
    "repeat_u": 4,
    "repeat_v": 1,
    "offset_v": 0.25,
    "background": None,
    "resolution": 1024,
}
```

```python
>>> tls2 = TextureLabelStyle(text="Hello World", font_size=36, color="#333333")
>>> tls2.to_dict()
{
    "style_type": "TextureLabelStyle",
    "text": "Hello World",
    "math_mode": False,
    "font_size": 36,
    "color": "#333333",
    "background": "#ffffff",
    "resolution": 512,
}
```

---

## 5. Implementation Checklist

- [ ] Create `py/pytanga/viz/_styles/_tex_label_style.py`
- [ ] Define `TextureLabelStyle` dataclass with all 11 fields
- [ ] Implement `to_dict()` — emit `"style_type": "TextureLabelStyle"`, omit `None` values
- [ ] Import and re-export from `py/pytanga/viz/_styles/__init__.py`
- [ ] Import and re-export from `py/pytanga/viz/__init__.py`

---

## 6. Verification

- [ ] `TextureLabelStyle().to_dict()` → `{"style_type": "TextureLabelStyle", "math_mode": False, "background": "#ffffff", "resolution": 512, "color": "#000000", "font_size": 48}`
- [ ] `TextureLabelStyle(text=None).to_dict()` → same as above (no `"text"` key)
- [ ] `TextureLabelStyle(text="abc", math_mode=True, background=None).to_dict()` → includes `text`, `math_mode`, `background` (null)
- [ ] `from pytanga.viz import TextureLabelStyle` works
- [ ] `from pytanga.viz._styles import TextureLabelStyle` works