# Image Labeling App

A `VisualizerApp` that labels images in the
[labelme](https://github.com/wkentaro/labelme) JSON format: draw shapes on an
image, select/delete them, and load/save the result as labelme annotations.

Run it with:

```bash
uv run python py/examples/apps/image_labeling_app.py [labels.json]
```

Pass a `.json` path to load an existing labelme file, or a plain image
(`.jpg` / `.jpeg` / `.png`) to use it as the background.

## What it does

- **Drawing tools** — a toolbar of six tools (rectangle, ellipse, circle, line,
  polygon, point).  Rect/ellipse/circle/line are drag-to-create; the polygon
  starts as a two-vertex segment you extend with Ctrl+drag; the point is a
  single click.
- **Selection & editing** — click a shape to select it (it highlights and shows
  its translate/rotate handles); Delete/Backspace removes the selection; Escape
  deselects and cancels an in-progress draw.
- **labelme I/O** — a File menu (Open…/Save/Save As…/Exit) and a command-line
  argument load/save labelme JSON (shapes plus an embedded or referenced image).

## Architecture

The reusable logic lives in `ImageLabeler`, a self-contained pane that the thin
`ImageLabelingApp` shell wraps.  All three live in
`py/examples/apps/image_labeling_app.py`:

- `ImageLabelingApp` — the `VisualizerApp` subclass: builds the File menu, keeps
  the current file path, and wires the menu entries to the labeler's
  `load` / `save` / `to_document`.
- `ImageLabeler` — owns the `ImageCanvas`, the tool toolbar, and the
  `list[LabeledShape]` state; exposes `.view` (a `StackView` of toolbar-over-
  canvas) plus `.canvas` / `.handle`.
- `LabeledShape` — a small dataclass (`act`, `style`, `label`) whose `as_pair()`
  yields the `(object, label)` tuple that
  `LabelMeStore.shapes_from_objects` consumes.

## Pytanga features used

| Feature | Role here |
|---------|-----------|
| `VisualizerApp` | app lifecycle (`init`, `run`, `request_shutdown`) |
| `ImageCanvas` / `ImageData` | the image pane; a numpy buffer as the background |
| `StackView` / `ToolbarView` / `MenuView` / `ButtonView` | layout (menu + toolbar + canvas) and controls |
| `ActRectangle2D` / `ActEllipse` / `ActCircle` / `ActLine` / `ActPolygon` / `ActPoint` | the interactive shapes |
| `DragPreview` / `DragBinding` | drag-to-create preview lifecycle + button/modifier binding |
| `LabelMeStore` / `LabelMeDocument` | labelme JSON load/save |
| `CirclePointStyle` (screen-space) / `SquarePointStyle` | handle and point markers |
| `Rectangle2DStyle` / `EllipseStyle` / `CircleStyle` / `LineStyle` / `PointPathStyle` | per-shape styles |
| `FileChooserDialog` | Open / Save As dialogs |
| `StackView(fill=True)` | make the labeler pane fill the available space |

The shape handles use `CirclePointStyle(size=…, screen_space=True)`, so they stay
a constant on-screen size regardless of image zoom — see
[Styling](../styling/styles.md).

## Reusing the ImageLabeler

`ImageLabeler` is meant to be copied and adapted, not imported.  Its `.view` is
a plain `StackView`, so drop it into any layout or split pane:

```python
# ImageLabeler is defined in py/examples/apps/image_labeling_app.py
labeler = ImageLabeler(viz)
layout = SplitView("horizontal", [labeler.view, other_view])
```

The menu bar is deliberately **not** part of `ImageLabeler` — the host app
builds it.  Adapt the styling by overriding `_style_for_act` / `_style_for_mode`,
and pass `default_label`, `fill_color`, `selected_color`, plus the `on_change` /
`on_select` callbacks to react to edits and selection.
