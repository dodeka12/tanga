# Phase 6 — Documentation

**Prerequisites:** Phases 1–5 complete (full texture label pipeline working)

**Goal:** Write user-facing documentation for texture labels. Create a new
`docs/py/viz/texture-labels.md` page covering `TextureLabelStyle`, the
convenience API (`tex_label`/`tex_label_style`), per-kind defaults, and
usage examples. Link from `docs/py/viz/index.md` and update the examples page.

---

## 1. `docs/py/viz/texture-labels.md` — Texture Labels Guide

```markdown
# Texture Labels

Texture labels render **text, KaTeX formulas, or mixed text+formula content**
directly onto entity surfaces using a Canvas → `THREE.CanvasTexture` pipeline.
Labels wrap around spheres (e.g. formulas tiled along the equator) and cover
planes (stretched, fitted, or tiled).

No additional browser dependencies — KaTeX is already loaded for annotation
rendering.

## Quick Start

The simplest way to add a texture label is via the ``tex_label`` convenience
parameter on ``Visualizer.add()``:

```python
from pytanga.geometry import Sphere, Point
from pytanga.viz import Visualizer

viz = Visualizer()

# Plain text label on a sphere
viz.add(Sphere(Point(0, 0, 0), 2.0), tex_label="S₁")

# KaTeX formula label — set math_mode=True
viz.add(
    Sphere(Point(3, 0, 0), 2.0),
    tex_label=r"\mathcal{S}_1",
    tex_label_style=TextureLabelStyle(math_mode=True, repeat_u=4),
)

viz.run()
```

The label appears as a texture on the sphere surface. For spheres, the label
is centered at the equator by default (UV offset ``V=0.25``). Use
``repeat_u=4`` to tile the label four times around the equator.

## `TextureLabelStyle`

All texture label rendering properties are controlled by
:class:`TextureLabelStyle`. Pass it to ``tex_label_style=`` on ``add()``, or
set it directly on a style class:

```python
from pytanga.viz import TextureLabelStyle, SphereStyle

viz.add(
    Sphere(Point(0, 0, 0), 2.0),
    style=SphereStyle(
        texture_label=TextureLabelStyle(
            text=r"\nabla^2 \phi = 0",
            math_mode=True,
            repeat_u=4,
            offset_v=0.25,
            background=None,       # transparent — sphere color shows through
            resolution=1024,
        ),
    ),
)
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | `str \| None` | `None` | Label content. Plain text, KaTeX formula, or mixed with `$...$` (inline) and `$$...$$` (display) math delimiters. |
| `math_mode` | `bool \| None` | `False` | `True` = entire `text` is a KaTeX formula. `False` = auto-detect `$` delimiters. |
| `repeat_u` | `float \| None` | `None` | Texture repeat count along U (longitude on sphere, X on plane). |
| `repeat_v` | `float \| None` | `None` | Texture repeat count along V (latitude on sphere, Y on plane). |
| `offset_u` | `float \| None` | `None` | UV offset along U. |
| `offset_v` | `float \| None` | `None` | UV offset along V. Spheres default to ``0.25`` (equator). Planes default to ``0.0``. |
| `align` | `str \| None` | `None` | Plane-only: ``"stretch"`` (fill quad), ``"fit"`` (preserve aspect ratio), ``"repeat"`` (tile). Ignored for spheres. |
| `background` | `str \| None` | `"#ffffff"` | Canvas background CSS color. ``None`` or ``"transparent"`` for no background. |
| `resolution` | `int \| None` | `512` | Canvas width in pixels (height = width / 2). Higher = sharper, more GPU memory. |
| `color` | `str \| None` | `"#000000"` | Text/formula CSS color. |
| `font_size` | `int \| None` | `48` | Font size in CSS pixels for plain text. Ignored when ``math_mode=True``. |

## Content Modes

### Math Mode (`math_mode=True`)

The entire ``text`` is treated as a KaTeX formula:

```python
TextureLabelStyle(text=r"\mathcal{S}_1", math_mode=True)
```

All KaTeX macros are supported: ``\frac``, ``\sqrt``, ``\int``, ``\sum``,
``\mathbf``, ``\mathbb``, ``\nabla``, Greek letters, etc.

### Mixed Mode (`math_mode=False` with ``$`` delimiters)

When ``text`` contains ``$...$`` (inline math) or ``$$...$$`` (display math),
KaTeX formulas are rendered alongside plain text:

```python
TextureLabelStyle(
    text="Radius $$r=2.5$$ cm",
    math_mode=False,
)
```

- ``$...$``: Inline formula — renders on the same line as surrounding text.
- ``$$...$$``: Display formula — renders centered on its own line.

### Plain Text Mode (`math_mode=False`, no ``$``)

When no math delimiters are present, the text is rendered as-is:

```python
TextureLabelStyle(text="Sphere A", font_size=64, color="#ffffff")
```

## Sphere-Specific Behavior

Spheres use ``SphereGeometry`` UV mapping:
- U=0..1 wraps around the equator (longitude)
- V=0..1 maps from south pole to north pole
- The equator is at V=0.5

Per-kind defaults for spheres: ``offset_v=0.25`` (centers a single label at
the equator), ``background=None`` (transparent), ``repeat_u=1``.

**Tiling a label around the equator:**

```python
TextureLabelStyle(
    text="Label",
    repeat_u=4,      # appears 4 times
    repeat_v=1,      # single band
    offset_v=0.25,   # equator position
)
```

## Plane-Specific Behavior

Planes use ``PlaneGeometry`` UV mapping. The ``align`` field controls layout:

| `align` | Behavior |
|---------|----------|
| ``"stretch"`` (default) | Label fills the entire quad. May stretch the aspect ratio. |
| ``"fit"`` | Label preserves its aspect ratio, centered on the quad. |
| ``"repeat"`` | Label tiles across the quad using ``repeat_u``/``repeat_v``. |

Per-kind defaults for planes: ``offset_v=0.0``.

**Tiling a label on a plane:**

```python
TextureLabelStyle(
    text="Tile",
    align="repeat",
    repeat_u=3,
    repeat_v=3,
)
```

## Per-Kind Defaults

Configure default texture label styles per entity kind via the
``default_tex_label_style`` property:

```python
from pytanga.viz import Visualizer, TextureLabelStyle

viz = Visualizer()

# All spheres get these defaults
viz.default_tex_label_style["Sphere"] = TextureLabelStyle(
    repeat_u=4,
    offset_v=0.25,
    background=None,
    resolution=1024,
)

# All planes get these defaults
viz.default_tex_label_style["Plane"] = TextureLabelStyle(
    align="fit",
    background="#ffffff",
    font_size=36,
)

# Now tex_label picks up the per-kind defaults automatically
viz.add(Sphere(Point(0, 0, 0), 2.0), tex_label=r"\mathcal{S}_1")
viz.add(Plane(...), tex_label="z=3")
```

## Supported Entities

| Entity | Supported | Notes |
|--------|-----------|-------|
| Sphere | ✅ | UV-wrapped; default at equator |
| Plane | ✅ | Quad-mapped; supports align modes |
| All others | ❌ | No texture label support (ignored) |

## Convenience API vs. Explicit Style

Two equivalent ways to set a texture label:

```python
# Convenience API (recommended for simple cases)
viz.add(Sphere(...), tex_label="S₁", tex_label_style=TextureLabelStyle(repeat_u=4))

# Explicit style (for fine-grained control)
viz.add(Sphere(...), style=SphereStyle(texture_label=TextureLabelStyle(text="S₁", repeat_u=4)))
```

When both ``tex_label`` and an explicit ``style.texture_label`` are set, the
explicit style takes precedence.

## Graceful Fallback

If KaTeX fails to load (CDN issue), the label renders as plain text. If
``text`` is ``None`` or the ``texture_label`` key is absent, the entity
renders with its plain material color — no texture is applied.
```

---

## 2. Update `docs/py/viz/index.md`

### 2.1 Add to Entity Rendering Properties Table

Locate the "Entity Rendering Properties" section and add:

```markdown
| `tex_label` | `str \| None` | `None` | Texture label text rendered onto the entity surface. Only supported for Sphere and Plane. |
| `tex_label_style` | `TextureLabelStyle \| None` | `None` | Style overrides for the texture label (math_mode, repeat, offset, etc.). Merged with per-kind defaults. |
```

### 2.2 Add Reference for `default_tex_label_style`

Locate the "Default Rendering Properties" / `Visualizer` methods section and add:

```markdown
### Texture Label Defaults

```python
# Configure per-kind texture label defaults
viz.default_tex_label_style["Sphere"] = TextureLabelStyle(
    repeat_u=4, offset_v=0.25, background=None
)
viz.default_tex_label_style["Plane"] = TextureLabelStyle(
    align="fit", background="#ffffff"
)
```

| Property | Type | Description |
|----------|------|-------------|
| `default_tex_label_style` | `_StyleDict` | Per-kind texture label style defaults, keyed by entity kind string (e.g. ``"Sphere"``, ``"Plane"``). Accepts ``TextureLabelStyle`` instances. |
```

### 2.3 Add Link to Texture Labels Guide

Add to the bottom of the API reference or in a "Further Reading" section:

```markdown
- [Texture Labels](texture-labels.md) — Text, KaTeX formulas, and mixed content on entity surfaces
```

---

## 3. Update `docs/py/viz/styles.md` (if it exists)

If `docs/py/viz/styles.md` covers the style classes, add a section for
`TextureLabelStyle`:

```markdown
### `TextureLabelStyle`

Controls texture-based labels on entity surfaces (Sphere, Plane). See
[Texture Labels](texture-labels.md) for full documentation and examples.

Fields: `text`, `math_mode`, `repeat_u`, `repeat_v`, `offset_u`, `offset_v`,
`align`, `background`, `resolution`, `color`, `font_size`.

Appears as an optional `texture_label` field on `SphereStyle` and `PlaneStyle`.
```

---

## 4. Implementation Checklist

- [ ] Create `docs/py/viz/texture-labels.md` with full content from §1
- [ ] Update `docs/py/viz/index.md`:
  - [ ] Add `tex_label`/`tex_label_style` to entity rendering properties table
  - [ ] Add `default_tex_label_style` property reference
  - [ ] Add link to `texture-labels.md`
- [ ] Update `docs/py/viz/styles.md` (if it exists) — add `TextureLabelStyle` section
- [ ] Verify all code snippets in `texture-labels.md` are syntactically correct
- [ ] Verify documentation format matches existing docs style

---

## 5. Verification

- [ ] `docs/py/viz/texture-labels.md` covers all `TextureLabelStyle` fields
- [ ] `docs/py/viz/texture-labels.md` explains all 3 content modes (math, mixed, plain)
- [ ] `docs/py/viz/texture-labels.md` documents sphere and plane behavior with examples
- [ ] `docs/py/viz/texture-labels.md` explains the ``default_tex_label_style`` per-kind defaults
- [ ] `docs/py/viz/texture-labels.md` explains the convenience API vs explicit style
- [ ] `docs/py/viz/index.md` links to `texture-labels.md`
- [ ] All inline code examples are syntactically correct Python