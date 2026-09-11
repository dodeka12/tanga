# CircleLineStyle / ArcLineStyle — draw circles and arcs as lines

**Created:** 2026-08-25 | **Status:** Planned

## Goal

Allow `Circle` and `Arc` entities to be rendered as **lines** (a thin
screen-space line loop / arc) instead of their default torus tubes.

This is **not** implemented as a flag on the existing `CircleStyle`/`ArcStyle`.
Instead we add two new style classes — `CircleLineStyle` and `ArcLineStyle` —
whose serialized `style_type` makes the frontend switch to dedicated line
renderers. This mirrors the existing `CrossHairPointStyle` pattern.

## Background / analysis

### Current behaviour

- `Circle` renders as a **torus** (`templates/renderers/circle.js` →
  `THREE.TorusGeometry(radius, tubeRadius, 16, 64)`). `CircleStyle.tube_radius`
  (serializer default `tubeRadius: 0.03`) controls the tube thickness.
- `Arc` renders as a **partial torus** (`templates/renderers/arc.js` →
  `THREE.TorusGeometry(radius, tubeRadius, 16, 64, angle)`), with an optional
  cone arrow tip when `ent.arrow` is set. `Arc.tube_radius` lives on the
  **entity** (not the style).
- `CircleStyle`/`ArcStyle` only offer a `wireframe` overlay — a `WireframeGeometry`
  **cage** of the torus (radial + longitudinal triangle edges), not a clean
  circular line. There is currently no way to get a single line-loop.

### Precedent to follow: `CrossHairPointStyle`

- `_styles/_operator_styles.py::CrossHairPointStyle(PointStyle)` is a separate
  style class that overrides `to_dict()` to set
  `result["style_type"] = "CrossHairPointStyle"`.
- `templates/renderers/factory.js` dispatches on that style type:
  ```js
  case 'Point':
  case 'HPoint':
      if (ent.style?.style_type === 'CrossHairPointStyle') {
          mesh = createCrossHairPoint(ent);
      } else {
          mesh = createPoint(ent);
      }
      break;
  ```
- `templates/renderers/crosshair_point.js` is a dedicated renderer module.

### Style resolution already supports this

`_styles/__init__.py::_style_to_output` merges a user-supplied `VizStyle` over the
canonical default for the kind. The merged dict's `style_type` comes from the
user's `to_dict()`, so a `CircleLineStyle` flows to the frontend as
`style_type == "CircleLineStyle"` (the inherited `tube_radius` from the canonical
`CircleStyle` remains in the dict but is simply ignored by the line renderer).

The serializers `_serialize_circle` (`serializer.py:753`) and `_serialize_arc`
(`serializer.py:848`) already emit the resolved `style` and all geometry fields
(`center`/`normal`/`radius`; `origin`/`axis`/`radius`/`angle`/`startDirection`/
`arrow`), so **no serializer geometry changes are required** — the line renderers
read the same fields.

### Line-drawing infrastructure already exists

`templates/renderers/utils.js` provides screen-space fat lines (`Line2` +
`LineMaterial`, `makeLineMaterial` with dashed support, `makeFatSegmentsFromFlat` /
`makeFatSegmentsColored`), already used by `point_path.js`. A line loop/arc can be
built by generating `n` points on the circle and feeding them to a `Line2` with
`LineGeometry`.

### glTF caveat

`export/_gltf.py` currently emits a **torus** for `Circle` (`_make_primitives`,
`kind == "Circle"`) and does **not** export `Arc` at all. A line-styled circle
would therefore still export as a torus unless the exporter is extended — treat
that as a follow-up (see Non-goals).

## Design decisions

1. **Two new style classes, no flags.** `CircleLineStyle(CircleStyle)` and
   `ArcLineStyle(ArcStyle)`; each overrides `to_dict()` to set its own
   `style_type` (`"CircleLineStyle"` / `"ArcLineStyle"`). Existing styles are
   untouched.
2. **Line-specific parameters** (on top of inherited `color`/`opacity`):
   - `line_thickness: float | None` — screen-space pixel width (like
     `PointPathStyle.line_thickness`); frontend default `2`.
   - `segments: int | None` — number of polyline segments used to approximate the
     circle/arc; frontend default `64` (full circle).
   - `dash: WireframeDashPattern | None` — optional dashed line (reuse the
     existing `WireframeDashPattern`; maps to `LineMaterial` `dashSize`/`gapSize`/
     `dashScale`).
   - `tube_radius` is **not** meaningful for a line and is ignored by the line
     renderers (it may still appear in the merged dict from the canonical default).
3. **Frontend dispatch on `style_type`** in `factory.js`, exactly like
   `CrossHairPointStyle`:
   ```js
   case 'Circle':
       mesh = (ent.style?.style_type === 'CircleLineStyle')
           ? createCircleLine(ent)
           : createCircle(ent);
       break;
   case 'Arc':
       mesh = (ent.style?.style_type === 'ArcLineStyle')
           ? createArcLine(ent)
           : createArc(ent);
       break;
   ```
   Two new renderer modules: `circle_line.js` and `arc_line.js`.
4. **Renderer shape.** `createCircleLine` builds a **closed** `Line2` loop from
   `center`/`normal`/`radius` (orientation via `rotationFromNormal`, as
   `circle.js`). `createArcLine` builds an **open** `Line2` arc from
   `origin`/`axis`/`radius`/`angle`/`startDirection` (reuse the `orientArc`
   logic), and still draws the `ent.arrow` cone tip when present (reuse the cone
   code from `arc.js`).
5. **Imaginary circles.** `ImagCircle` serializes with `kind == "Circle"` (see
   `_serialize_circle`), so `CircleLineStyle` works for it too; the dispatch is on
   `style_type`, not `is_imaginary`.
6. **In-place updates.** Structural changes (radius/angle/segments/`arrow`) must
   **rebuild** the line (as `point_path.js::updatePointPath` returns `false`).
   Either add `updateCircleLine`/`updateArcLine` returning `false` on such changes
   and wire them into `factory.js::updateEntityMesh`, or rely on the existing
   rebuild-on-dirty fallback — this is decided during implementation, but must be
   handled so animated arcs/circles update correctly.

## Changes

### Step 1 — Style classes & exports

**Files:** `py/pytanga/viz/_styles/_entity_styles.py`,
`py/pytanga/viz/_styles/__init__.py`, `py/pytanga/viz/__init__.py`

- [ ] Add `CircleLineStyle(CircleStyle)` with fields `line_thickness`, `segments`,
      `dash` and a `to_dict()` that sets `style_type = "CircleLineStyle"`.
- [ ] Add `ArcLineStyle(ArcStyle)` with the same fields and
      `style_type = "ArcLineStyle"`.
- [ ] Import both in `_styles/__init__.py` and add them to the `ObjVizStyle` union.
- [ ] Export both from `py/pytanga/viz/__init__.py` (alongside the existing style
      imports).

### Step 2 — Frontend renderers + dispatch

**Files:** `py/pytanga/viz/templates/renderers/circle_line.js` (new),
`py/pytanga/viz/templates/renderers/arc_line.js` (new),
`py/pytanga/viz/templates/renderers/factory.js`

- [ ] `circle_line.js`: sample `segments` points around the circle, build a closed
      `Line2` loop (fat line), orient by `normal`, position at `center`; honor
      `line_thickness`/`dash`; `tagEntity`.
- [ ] `arc_line.js`: sample `segments` points over `angle` from `startDirection`,
      build an open `Line2` arc, orient via axis + start direction; draw the
      `arrow` cone tip when `ent.arrow` is set; honor `line_thickness`/`dash`;
      `tagEntity`.
- [ ] `factory.js`: add the `Circle`/`Arc` style-type dispatch (above) and import
      the two new renderers.
- [ ] Decide + implement the update path (dedicated `updateCircleLine`/`updateArcLine`
      returning `false` for structural changes, wired into `updateEntityMesh`).

### Step 3 — Serialization (verify only)

**Files:** `py/pytanga/viz/serializer.py` (no change expected)

- [ ] Confirm `_serialize_circle` / `_serialize_arc` already forward the resolved
      style (`style_type`, `line_thickness`, `segments`, `dash`) via
      `_apply_defaults` + `styles_map`; add a small assertion test rather than new
      serializer code.
- [ ] Confirm `ImagCircle` routes through `_serialize_circle` and carries
      `CircleLineStyle` correctly.

### Step 4 — Tests

**Files:** `py/tests/viz/test_styles.py` (or `test_serializer.py` /
`test_imaginary_styles.py`), plus `node --check` on the JS.

- [ ] `CircleLineStyle` / `ArcLineStyle` `to_dict()` emits the correct `style_type`
      and only the non-`None` fields (`line_thickness`, `segments`, `dash`, plus
      inherited `color`/`opacity`).
- [ ] `serialize_entity(Circle(...), style=CircleLineStyle(...))` produces a dict
      whose `style.style_type == "CircleLineStyle"` and carries
      `line_thickness`/`segments`.
- [ ] Same for `Arc` + `ArcLineStyle`.
- [ ] `ImagCircle` + `CircleLineStyle` serializes with `style_type ==
      "CircleLineStyle"` (dispatch is style-type based).
- [ ] `node --check` on `circle_line.js`, `arc_line.js`, and `factory.js`.
- [ ] (Headless, if feasible) an exported scene containing a line-styled circle
      includes the new renderer module in the bundle (the existing duplicate-name
      regression test pattern).

### Step 5 — Documentation

**Files:** the viz styles doc (`docs/py/viz/styles.md`) and/or the entity docs
for `Circle`/`Arc`.

- [ ] Document `CircleLineStyle` and `ArcLineStyle` with a short usage snippet:
      `viz.new(Circle(...), style=CircleLineStyle(line_thickness=3, segments=96))`
      and the same for `Arc`.
- [ ] Note the difference from `CircleStyle`/`ArcStyle` (torus) and that the line
      variants are screen-space width (zoom-independent).

### Step 6 — Changelog

**File:** branch changelog per `dev/workflows/changelog.md`

- [ ] Add a New Features bullet for `CircleLineStyle`/`ArcLineStyle`.

## Verification

- [ ] `uv run pytest py/tests/viz -q` and `uv run pytest -q` green.
- [ ] `uv run ruff check` and `uv run ruff format --check` on touched Python files.
- [ ] `node --check` on the new/edited renderer modules.
- [ ] Manual browser check: a `Circle`/`Arc` with the new styles renders as a thin
      line loop/arc (correct orientation, correct arrow tip on arcs); the default
      torus rendering is unchanged for `CircleStyle`/`ArcStyle`.

## Notes / edge cases

- **Closed vs open.** Circle → closed loop (repeat the first point at the end);
  Arc → open polyline (no closing segment).
- **`segments` semantics.** Use the segment count over the swept arc (a full
  circle uses all `segments`; an arc could either use the same count over its
  smaller angle or scale proportionally — decide and document; simplest is to
  keep `segments` absolute over the swept angle).
- **Screen-space width.** `Line2` fat lines use `worldUnits: false`, so thickness
  is in pixels and constant under zoom, consistent with `PointPath`.
- **Non-uniform parent scale.** Lines are unaffected (screen-space width), so the
  line styles are safe under the `CoordinateSystem` data group's scale, unlike a
  torus.
- **Update path.** Structural changes (radius/angle/`segments`/`arrow`) require a
  rebuild; do not attempt a generic in-place update for the line meshes (mirror
  `updatePointPath` returning `false`).
- **glTF export.** Out of scope for the initial change: a `CircleLineStyle` circle
  still exports as a torus, and `Arc` is not exported at all (documented).
- **`ImagCircle`.** Works through the same dispatch; the imaginary dotted-wireframe
  default no longer applies when `CircleLineStyle` is given (the line style fully
  replaces the wireframe/tube appearance).

## Non-goals / follow-ups

- Changing `CircleStyle`/`ArcStyle` or adding any render-mode flag to them.
- glTF/GLB line export for circles/arcs (follow-up).
- Dashed patterns beyond reusing the existing `WireframeDashPattern` (no new
  pattern classes).
- A combined `circle_line.js`/`arc_line.js` module — keep two dedicated modules
  for clarity (or consolidate later if preferred).


