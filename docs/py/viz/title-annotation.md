# Title & Annotation

The viewer supports a title overlay and a Markdown annotation panel with
LaTeX math rendering. Both are fixed-position DOM elements — always readable,
independent of camera orientation.

See the example script [`demo_title_annotation.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_title_annotation.py)
for a runnable demonstration.

## Title

The `title` parameter (constructor or `set_title()`) displays a fixed-position
heading at the top of the viewport:

```python
viz = Visualizer(title="PGA3 — Sphere Visualization")
viz.set_title("Updated Title")
```

The `TitleStyle` controls appearance (`font_size`, `color`, `background`).

## Annotation Panel

The `annotation` parameter (constructor or `set_annotation()`) renders
**Markdown** text with **LaTeX math** in a fixed-position, scrollable panel
at the bottom of the viewport. The browser uses the `marked` library for
Markdown → HTML conversion and `KaTeX` for math formula rendering.

```python
viz = Visualizer(annotation="""## Step 1

The sphere is defined by: $S = o - \\frac{1}{2} r^2 \\infty$

In conformal GA:
$$S \\cdot X = 0$$
""")

# Live update during animation
viz.set_annotation("## Step 2\n\n$R = e^{-i\\theta/2}$")

# Hide the panel
viz.set_annotation(None)
```

## `AnnotationStyle`

Controls the panel's visual appearance:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `width` | `str` | `"100%"` | CSS width |
| `max_width` | `str` | `"800px"` | CSS max-width |
| `max_height` | `str` | `"250px"` | CSS max-height (scrollable if exceeded) |
| `font_size` | `float` | `13` | Font size in px |
| `font_family` | `str` | `"sans-serif"` | CSS font-family |
| `color` | `str` | `"#cccccc"` | Text color |
| `background` | `str` | `"rgba(0,0,0,0.75)"` | Panel background |
| `link_color` | `str` | `"#88ccff"` | Hyperlink color |
| `code_background` | `str` | `"rgba(255,255,255,0.1)"` | Inline code background |
| `padding` | `str` | `"10px 16px"` | CSS padding |
| `border_radius` | `str` | `"4px"` | CSS border-radius |

Mutate the global default via `viz.default_annotation_style`.

## LaTeX Math

Inline math uses `$...$`, display-style math uses `$$...$$`. KaTeX
auto-detects and renders all delimiters in the annotation text. Supported
features include fractions, exponents, Greek letters, integrals, and matrices.

The same rendering pipeline is used for math in figure export footers and
in KaTeX-formatted entity labels.

## Live Updates

```python
viz.set_annotation("## Angle: 45°\n\n$\\theta = \\pi/4$")
viz.set_annotation(None)  # hide
```

`set_annotation()` pushes immediately via `flush()` — no manual flush
needed.