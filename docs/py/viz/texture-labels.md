# Texture Labels

Texture labels render **text, KaTeX formulas, or mixed text+formula content**
directly onto entity surfaces using a Canvas → `THREE.CanvasTexture` pipeline.
Labels wrap around spheres (e.g. formulas tiled along the equator) and cover
planes (stretched, fitted, or tiled).

No additional browser dependencies — KaTeX is already loaded for annotation
rendering.

## Quick Start

The simplest way to add a texture label is via the `tex_label` convenience
parameter on `Visualizer.add()`:

```python
from pytanga.geometry import Sphere, Point
from pytanga.viz import Visualizer, TextureLabelStyle

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
is centered at the equator by default (UV offset `V=0.25`). Use
`repeat_u=4` to tile the label four times around the equator.

## `TextureLabelStyle`

All texture label rendering properties are controlled by
`TextureLabelStyle`. Pass it to `tex_label_style=` on `add()`, or
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
| `offset_v` | `float \| None` | `None` | UV offset along V. Spheres default to `0.25` (equator). Planes default to `0.0`. |
| `align` | `str \| None` | `None` | Plane-only: `"stretch"` (fill quad), `"fit"` (preserve aspect ratio), `"repeat"` (tile). Ignored for spheres. |
| `background` | `str \| None` | `"#ffffff"` | Canvas background CSS color. `None` or `"transparent"` for no background. |
| `resolution` | `int \| None` | `512` | Canvas width in pixels (height = width / 2). Higher = sharper, more GPU memory. |
| `color` | `str \| None` | `"#000000"` | Text/formula CSS color. |
| `font_size` | `int \| None` | `48` | Font size in CSS pixels for plain text. Ignored when `math_mode=True`. |

## Content Modes

### Math Mode (`math_mode=True`)

The entire `text` is treated as a KaTeX formula:

```python
TextureLabelStyle(text=r"\mathcal{S}_1", math_mode=True)
```

All KaTeX macros are supported: `\frac`, `\sqrt`, `\int`, `\sum`,
`\mathbf`, `\mathbb`, `\nabla`, Greek letters, etc.

### Mixed Mode (`math_mode=False` with `$` delimiters)

When `text` contains `$...$` (inline math) or `$$...$$` (display math),
KaTeX formulas are rendered alongside plain text:

```python
TextureLabelStyle(
    text="Radius $$r=2.5$$ cm",
    math_mode=False,
)
```

- `$...$`: Inline formula — renders on the same line as surrounding text.
- `$$...$$`: Display formula — renders centered on its own line.

### Plain Text Mode (`math_mode=False`, no `$`)

When no math delimiters are present, the text is rendered as-is:

```python
TextureLabelStyle(text="Sphere A", font_size=64, color="#ffffff")
```

## Sphere-Specific Behavior

Spheres use `SphereGeometry` UV mapping:

- U=0..1 wraps around the equator (longitude)
- V=0..1 maps from south pole to north pole
- The equator is at V=0.5

Per-kind defaults for spheres: `offset_v=0.25` (centers a single label at
the equator), `background=None` (transparent), `repeat_u=1`.

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

Planes use `PlaneGeometry` UV mapping. The `align` field controls layout:

| `align` | Behavior |
|---------|----------|
| `"stretch"` (default) | Label fills the entire quad. May stretch the aspect ratio. |
| `"fit"` | Label preserves its aspect ratio, centered on the quad. |
| `"repeat"` | Label tiles across the quad using `repeat_u`/`repeat_v`. |

Per-kind defaults for planes: `offset_v=0.0`.

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
`default_tex_label_style` property:

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

The `default_tex_label_style` property supports both class-based access
(`viz.default_tex_label_style[Sphere]`) and string-based access
(`viz.default_tex_label_style["Sphere"]`).

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

When both `tex_label` and an explicit `style.texture_label` are set, the
explicit style takes precedence.

## Demo Scripts

| Script | Topic |
|--------|-------|
| [`demo_texture_label_sphere.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_texture_label_sphere.py) | Plain text, KaTeX, and mixed content on spheres |
| [`demo_texture_label_plane.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_texture_label_plane.py) | Align modes (stretch/fit/repeat) and mixed content on planes |

Run with:

```
uv run python py/examples/viz/demo_texture_label_sphere.py
uv run python py/examples/viz/demo_texture_label_plane.py
```

## Graceful Fallback

If KaTeX fails to load (CDN issue), the label renders as plain text. If
`text` is `None` or the `texture_label` key is absent, the entity
renders with its plain material color — no texture is applied.