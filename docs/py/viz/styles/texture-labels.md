# Texture Labels

Texture labels render **text, KaTeX formulas, or mixed text+formula content**
directly onto entity surfaces using a Canvas → `THREE.CanvasTexture` pipeline.
Labels wrap around spheres (e.g. formulas tiled along the equator) and cover
planes (stretched, fitted, or tiled).

No additional browser dependencies — KaTeX and html2canvas are already loaded
in the viewer page.

## Quick Start

The simplest way to add a texture label is via the `tex_label` convenience
parameter on `Visualizer.add()`:

```python
from pytanga.geometry import Sphere, Point
from pytanga.viz import Visualizer, TextureLabelStyle

viz = Visualizer()

# Plain text label on a sphere
viz.add(Sphere(Point(0, 0, 0), 2.0), tex_label="S₁")

# KaTeX formula label using $$ delimiters
viz.add(
    Sphere(Point(3, 0, 0), 2.0),
    tex_label=r"$$\mathcal{S}_1$$",
    tex_label_style=TextureLabelStyle(repeat_u=4),
)

# Mixed text + inline math
viz.add(
    Sphere(Point(6, 0, 0), 2.0),
    tex_label="Radius $$r=2$$ cm",
    tex_label_style=TextureLabelStyle(font_size=48),
)

viz.run()
```

When `tex_label` is passed to `add()`, the visualizer automatically:

- **Disables wireframe** on the sphere/plane so it doesn't obscure the texture
- **Enables `double_sided`** rendering on spheres so the label stays visible when the camera moves inside
- **Defaults the label background** to the entity's fill color so the label blends in seamlessly

## Content Modes

Texture labels auto-detect content type based on `$` and `$$` delimiters:

| Mode | Detection | Example |
|------|-----------|---------|
| Plain text | No `$` delimiters | `"Sphere A"` |
| Inline math | `$...$` | `"Radius $r=2.5$ cm"` |
| Display math | `$$...$$` | `"$$\nabla^2 \phi = 0$$"` |
| Mixed | Both `$` and `$$` | `"Radius $$r=2.5$$ cm"` |

KaTeX formulas between `$$...$$` render as centered display math (larger). Formulas between `$...$` render inline with surrounding text.

## `TextureLabelStyle`

All texture label rendering properties are controlled by `TextureLabelStyle`.
Pass it to `tex_label_style=` on `add()`, or set it directly on a style class:

```python
from pytanga.viz import TextureLabelStyle, SphereStyle

viz.add(
    Sphere(Point(0, 0, 0), 2.0),
    style=SphereStyle(
        texture_label=TextureLabelStyle(
            text="$$\nabla^2 \phi = 0$$",
            repeat_u=4,
            offset_v=0.0,
            resolution=1024,
        ),
    ),
)
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | `str \| None` | `None` | Label content. Can contain `$...$` (inline math) and `$$...$$` (display math) delimiters. |
| `repeat_u` | `float \| None` | `None` | Texture repeat count along U (longitude on sphere, X on plane). |
| `repeat_v` | `float \| None` | `None` | Texture repeat count along V (latitude on sphere, Y on plane). |
| `offset_u` | `float \| None` | `None` | UV offset along U. Shifts the label horizontally. |
| `offset_v` | `float \| None` | `None` | UV offset along V. Sphere default `0.0`, plane default `0.0`. |
| `align` | `str \| None` | `None` | Plane-only: `"stretch"` (fill quad), `"fit"` (preserve aspect ratio), `"repeat"` (tile with `repeat_u`/`repeat_v`). |
| `background` | `str \| None` | `None` | Canvas background color. `None` or `"transparent"` means the entity's own fill color is used (label blends in). Set to a CSS color like `"#ffffff"` to force a specific background. |
| `resolution` | `int \| None` | `1024` | Canvas width in pixels (height = width / 2). Higher = sharper, more GPU memory. |
| `color` | `str \| None` | `"#000000"` | Text/formula color. |
| `font_size` | `int \| None` | `48` | Font size in px for plain text portions. |
| `scale` | `float \| None` | `None` | Overall size multiplier for the content. `1.0` = native, `2.0` = twice as large. |
| `aspect` | `float \| None` | `None` | Height‑to‑width ratio of the texture content. `1.0` = square, `0.5` = half as tall (counters sphere UV stretching). Sphere per-kind default is `1.0`. |

## Sphere-Specific Behavior

Spheres use `SphereGeometry` UV mapping:

- U=0..1 wraps around the equator (longitude)
- V=0..1 maps from south pole (V=0) to north pole (V=1)
- The equator is at V=0.5

### Per-Kind Defaults (Sphere)

| Field | Default | Notes |
|-------|---------|-------|
| `repeat_u` | `4` | Four copies around the equator |
| `repeat_v` | `1` | Single band |
| `offset_v` | `0.0` | Centered at equator |
| `aspect` | `1.0` | Square content |
| `scale` | `0.8` | Slightly reduced from native size |

**Tiling a label around the equator:**

```python
TextureLabelStyle(
    text="Label",
    repeat_u=6,      # appears 6 times
    repeat_v=1,      # single band
    offset_v=0.0,    # equator position
)
```

### `double_sided` Rendering

When `tex_label` auto-creates a `SphereStyle`, it sets `double_sided=True`
so the label remains visible from inside the sphere. To disable:

```python
viz.add(
    Sphere(...),
    tex_label="text",
    style=SphereStyle(double_sided=False),
)
```

### Custom Background

By default the texture background matches the sphere's fill color:

```python
# Label blends into the orange sphere
viz.add(Sphere(Point(0, 0, 0), 2.0), tex_label="S₁", color="#ffaa00")
```

To force an explicit background color:

```python
viz.add(
    Sphere(Point(0, 0, 0), 2.0),
    tex_label="S₁",
    tex_label_style=TextureLabelStyle(background="#ffffff"),
)
```

## Plane-Specific Behavior

Planes use `PlaneGeometry` UV mapping. The `align` field controls layout:

| `align` | Behavior |
|---------|----------|
| `"stretch"` (default) | Label fills the entire quad. May stretch the aspect ratio. |
| `"fit"` | Label preserves its aspect ratio, centered on the quad. |
| `"repeat"` | Label tiles across the quad using `repeat_u`/`repeat_v`. |

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
`styles.tex_label_kind` property:

```python
from pytanga.viz import Visualizer, TextureLabelStyle

viz = Visualizer()

# Override sphere defaults
viz.styles.tex_label_kind["Sphere"] = TextureLabelStyle(
    repeat_u=6,
    offset_v=0.0,
    resolution=2048,
)

# Override plane defaults
viz.styles.tex_label_kind["Plane"] = TextureLabelStyle(
    align="fit",
    background="#ffffff",
    font_size=36,
)

# Now tex_label picks up the per-kind defaults automatically
viz.add(Sphere(Point(0, 0, 0), 2.0), tex_label="$$\mathcal{S}_1$$")
viz.add(Plane(...), tex_label="z=3")
```

The `styles.tex_label_kind` property supports both class-based access
(`viz.styles.tex_label_kind[Sphere]`) and string-based access
(`viz.styles.tex_label_kind["Sphere"]`).

The global defaults (applied when no per-kind override exists) are:
`font_size=48`, `color="#000000"`, `background=None` (entity color),
`resolution=1024`.

## Style Resolution

Styles are resolved with priority: **user > per-kind > global**.

Only non-`None` fields override lower-priority sources. Example:

```python
# Global default: color="#000000", font_size=48, resolution=1024
# Sphere per-kind: repeat_u=4, aspect=1.0, scale=0.8

viz.add(
    Sphere(...),
    tex_label="hello",
    tex_label_style=TextureLabelStyle(resolution=2048),
)
# Result: color="#000000", font_size=48, resolution=2048, repeat_u=4, aspect=1.0, scale=0.8
```

## Supported Entities

| Entity | Supported | Notes |
|--------|-----------|-------|
| Sphere | ✅ | UV-wrapped; defaults to 4 repeats at equator |
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
explicit style takes precedence over the convenience parameter. However,
`tex_label`'s text value still flows through if the explicit style's
`texture_label.text` is unset.

## Rendering Details

**Material color**: When a texture label is applied, the Three.js material
color is set to white (`#ffffff`) so the texture's own colors pass through
unmodified. This means you control the background via `TextureLabelStyle.background`
and the text color via `TextureLabelStyle.color`.

**Default background**: When `background` is `None` or `"transparent"`, the
texture canvas is filled with the entity's own fill color. This makes the
label appear as if it's painted directly on the surface, with no visible
rectangle around it.

**Wireframe auto-disable**: When `tex_label` triggers auto-creation of a
`SphereStyle` or `PlaneStyle`, `wireframe` is set to `False` so the wireframe
cage doesn't obscure the texture. Explicit user styles always override this.

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