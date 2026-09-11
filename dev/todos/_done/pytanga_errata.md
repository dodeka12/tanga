# pytanga Errata

Inconsistencies between the **pytanga docs** (`.dep-docs/pytanga`) and
**examples** (`.dep-examples/pytanga`) and the *actual* functionality
encountered while writing the visualization tutorials. Each entry lists the
source, what it claims, and what the library actually does (verified against
the installed `pytanga` package).

Legend: 🔴 = broken as written (raises / does not run), 🟡 = misleading or
incomplete (works but trips the reader up).

---

## 🔴 `wireframe=True` is not a valid `add()`/`new()`/`viz(...)` keyword

- **Sources**
  - `.dep-docs/pytanga/py/viz/index.md` — *Quick Start* and *Multiple Scenes*
  - `.dep-docs/pytanga/py/viz/use-cases-scripts.md` — *Interactive Visualizer*
  - `.dep-docs/pytanga/py/viz/use-cases-notebooks.md` — *Interactive Visualizer*
  - `.dep-examples/pytanga/viz/styling/custom_defaults.py` (line 42)
- **Claimed:** `viz(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.4)`
  opts the sphere into wireframe rendering via a `wireframe=` shortcut.
- **Actual:** `Visualizer.add()`, `Visualizer.new()`, and the `viz(...)`
  callable (`Visualizer.__call__`) have **no** `wireframe` parameter. Passing it
  raises `TypeError: Visualizer.new() got an unexpected keyword argument
  'wireframe'`.
- **Correct usage:**
  ```python
  viz.add(Sphere(Point(0, 0, 0), 2.5), style=SphereStyle(wireframe=True), opacity=0.4)
  ```

---

## 🔴 `Sphere(0, 0, 0, 2)` does not match the constructor signature

- **Source:** `.dep-docs/pytanga/py/viz/styles/styles.md` (wireframe example)
- **Claimed:** `viz.add(Sphere(0, 0, 0, 2), style=SphereStyle(...))`.
- **Actual:** `Sphere.__init__(self, center, radius=None, is_imaginary=False)`.
  Four positional coordinates plus the style argument is five positional
  arguments → `TypeError: Sphere.__init__() takes from 2 to 4 positional
  arguments but 5 were given`.
- **Correct usage:** `viz.add(Sphere(Point(0, 0, 0), 2), style=SphereStyle(...))`.

---

## 🔴 Wireframe dash classes are not importable from `pytanga.viz`

- **Source:** `.dep-docs/pytanga/py/viz/styles/styles.md`
  - `from pytanga.viz import DashedWireframe, DottedWireframe, SolidWireframe`
  - `from pytanga.viz import DashedWireframe`
- **Claimed:** `SolidWireframe` / `DashedWireframe` / `DottedWireframe` (and the
  `WireframeDashPattern` base) are exported from the top-level `pytanga.viz`.
- **Actual:** they are defined in the private submodule `pytanga.viz._styles`
  and are **not** re-exported by `pytanga.viz.__init__`.
- **Correct usage:**
  ```python
  from pytanga.viz._styles import DashedWireframe, DottedWireframe, SolidWireframe
  ```

---

## 🟡 `ModifierKey` and `KeyModifier` are two *different* enums

- **Sources**
  - `.dep-docs/pytanga/py/viz/visualizer/object-interaction.md` (uses
    `ModifierKey` for interaction triggers)
  - `.dep-docs/pytanga/py/viz/visualizer/animation.md` (uses `KeyModifier` for
    `enable_server_stop_key(...)` / `animate(stop_modifiers=...)`)
- **Claimed (implicitly):** a single modifier-key enum for everything.
- **Actual:** both are exported from `pytanga.viz`, but they are distinct:
  - `ModifierKey` = `{CTRL, SHIFT, ALT}` — used by the pointer-interaction
    system (`InteractionTrigger.modifiers`).
  - `KeyModifier` = `{CTRL, SHIFT, ALT, META}` — used by keyboard bindings
    (`enable_server_stop_key`, `animate(stop_modifiers=...)`).
- **Note:** the two enums are **not** interchangeable (passing a `KeyModifier`
  into `InteractionTrigger.modifiers` or vice-versa is a type error).

---

## 🟡 Docs/examples import public API from private submodules

- **Sources**
  - `.dep-docs/pytanga/py/viz/scene-objects/active-elements/*.md`
    (`from pytanga.viz._active import ActPoint`)
  - `.dep-docs/pytanga/py/viz/visualizer/object-interaction.md`
    (`from pytanga.viz._interaction import ...`)
  - `.dep-examples/pytanga/viz/interaction/*.py`, `.dep-examples/pytanga/viz/sdf/objects.py`
- **Claimed (implicitly):** these names live only in `pytanga.viz._active` /
  `pytanga.viz._interaction`.
- **Actual:** `ActPoint`, `ActSceneObject`, `InteractionConfig`,
  `InteractionTrigger`, `InteractionEventType`, `MouseButton`, `ModifierKey`,
  `DragMode`, `ClickEvent`, `DragEvent`, `ScrollEvent`, `Camera`, and `Handler`
  are all re-exported from the public `pytanga.viz` package.
- **Note:** the private imports still work, but are inconsistent with the public
  API surface used everywhere else.

---

## 🟡 `CoordinateSystem` constructor parameters are under-documented

- **Source:** `.dep-docs/pytanga/py/viz/scene-objects/coordinate-system.md`
  (*Data coordinate system* table)
- **Claimed:** the documented data-range parameters are
  `xlim`/`ylim`/`xscale`/`yscale`/`size`/`align`/`axis_origin`/`min_x_span`/
  `base`/`value_format`/`labels`.
- **Actual:** `CoordinateSystem.__init__` additionally accepts `grid`, `axes`,
  `plane`, `camera`, `border_px`, `border_world`, and `group_name`, which are
  not listed in that table (several appear only later in the page's prose).
- **Note:** not a runtime bug — the table is simply incomplete.

---

## 🟡 SDF primitive names are snake_case, not camelCase

- **Sources** (in the *plan*, plus implied by entity naming):
  `dev/todos/tutorial/viz/tutorial_overview.md` §3/§19 mention the
  `partialDisk` / `regularPolygon` SDF primitives.
- **Actual:** the `pytanga.viz.sdf` primitive library exports
  `partial_disk` and `regular_polygon` (snake_case), alongside `sphere`, `box`,
  `cylinder`, `capped_cylinder`, `cone`, `capped_cone`, `torus`, `ellipsoid`,
  `round_box`, `capsule`, `segment`, `plane`, `bound_box`.
- **Correct usage:**
  ```python
  from pytanga.viz.sdf import partial_disk, regular_polygon
  ```

---

## 🔴 `add(..., label=...)` returns the entity id, not an `(entity_id, label_id)` tuple

- **Source:** `.dep-docs/pytanga/py/viz/styles/labels.md` (*Convenience Shortcut*)
- **Claimed:** `viz.add(Point(...), label="P")` returns `(entity_id, label_id)`
  as a 2-tuple.
- **Actual:** `add()` returns the entity id `str` only. The attached label ids
  are available via `viz.get_label_ids(entity_id)` (a `list[str]`).
- **Correct usage:**
  ```python
  eid = viz.add(Point(0, 0, 0), label="P")
  lid = viz.get_label_ids(eid)[0]
  viz.update_label(lid, text="…", style=LabelStyle(...))
  ```

---

## 🟡 Text / color / checkbox `View` classes are not re-exported from `pytanga.viz`

- **Source:** `.dep-docs/pytanga/py/viz/visualizer/split-views.md`
  (mentions the text / color / checkbox control views alongside the other
  `View` classes); the plan ("every panel control has a matching `View` class")
  implies they are all importable from `pytanga.viz`.
- **Actual:** `TextFieldView`, `TextAreaView`, `ColorPickerView`, and
  `CheckboxView` exist in the `pytanga.viz.views` submodule but are **not**
  re-exported by `pytanga.viz.__init__` (which only re-exports `ButtonView`,
  `DropdownView`, `FileChooserView`, `GroupView`, `SceneView`, `SliderView`,
  `SpacerView`, `SplitView`, `StackView`, `ValueEditView`, and `View`).
- **Correct usage:**
  ```python
  from pytanga.viz.views import CheckboxView, ColorPickerView, TextAreaView, TextFieldView
  ```

---

*More entries are appended as additional inconsistencies are discovered while
implementing the tutorials.*
