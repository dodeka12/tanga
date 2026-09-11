# Conic Visualization Rendering — Overview

**Created:** 2026-09-11 | **Status:** In progress | **Branch:** `feat/quadric-space`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs. Relevant
> today: `docs/dev/architecture/viz-architecture.md` (styles ownership
> `Scene.styles`, the add-entity data flow, `_resolve_scene_entity`).

## Goal

Make the raw `Conic` entity directly drawable in the viewer by auto-refining it
to its specific 2D entity inside the viz resolver, and complete the style +
renderer coverage for the 2D conic family (and the missing 3D `Cone`), so that a
refined conic renders as a **2D line** (ellipse, hyperbola, parabola, line pair,
parallel line pair, circle) with a coherent `ConicStyle` / `Quadric3DStyle`
style hierarchy. Also fix a silent-exception swallow that hides serialization
failures, and clean up nonsensical wireframe parameters on thick-line styles.

## Architecture (short)

- **Auto-refine** happens once, eagerly, in `scene._resolve_scene_entity`: an
  `MV` is analyzed to a `Conic`/`Quadric3D`; a raw `Conic` is then refined to its
  specific entity (`Ellipse`/`Hyperbola`/`Parabola`/`Line`/`LinePair`/
  `ParallelLinePair`/`Circle`). `Quadric3D` is **not** refined — it already
  renders via the analytic ray path (`RayQuadricStyle`).
- **Styles** live in `_styles/_entity_styles.py`, canonical defaults in
  `_styles/__init__.py:_DEFAULT_STYLE_FOR_KIND`, bundled by
  `_viz_styles.make_styles()`. Serializers resolve a style via
  `_styles._style_to_output(user_style, kind, styles_map)` — the merge already
  gives precedence to the user's non-`None` style fields, so the
  "user `ConicStyle` wins over the refined kind's default" requirement needs no
  new merge function, only a test.
- **Serializers** live in `serializer.py` (`_dispatch_entity` + `_serialize_*`).
- **Frontend** renderers live in `templates/renderers/*.js`, dispatched by
  `factory.js` on `ent.kind` (with style-variant dispatch on `style_type`).

## Wire contract (fixed up front)

- Ellipse (2D line): `{"kind":"Ellipse","center":[x,y,z],"radiusU":ru,
  "radiusV":rv,"normal":[nx,ny,nz]}` + style
  `{"style_type":"EllipseStyle","color","opacity","thickness"}` (no wireframe).
- Circle tube (default): existing `{"kind":"Circle","center","normal","radius",
  "tubeRadius","isImaginary"}` + style
  `{"style_type":"CylinderCircleStyle","color","opacity","tube_radius",
  wireframe…}`.
- Circle thick line (opt-in): same geometry + style
  `{"style_type":"CircleStyle","color","opacity","thickness"}`.
- Hyperbola: `{"kind":"Hyperbola","center","dir1","dir2","a","b"}` + style
  `{"style_type":"HyperbolaStyle","color","opacity","thickness","extent"}`.
- Parabola: `{"kind":"Parabola","vertex","direction","p"}` + style
  `{"style_type":"ParabolaStyle",...,"extent"}`.
- LinePair: `{"kind":"LinePair","line1":{origin,direction},
  "line2":{origin,direction}}` + `{"style_type":"LinePairStyle",...}`.
- ParallelLinePair: `{"kind":"ParallelLinePair","line1","line2"}` + style
  `{"style_type":"ParallelLinePairStyle","color","opacity","thickness","length"}`.
- Cone: `{"kind":"Cone","vertex":[x,y,z],"axis":[nx,ny,nz],"halfAngle":a}` +
  style `{"style_type":"ConeStyle","color","opacity", wireframe…}`.

Content fields are camelCase; style fields are snake_case (existing convention).

## Decisions (confirmed)

- `_resolve_scene_entity` refines `Conic`; leaves `Quadric3D` alone.
- `ConicStyle(VizStyle)` base (`color`, `opacity`, `thickness`); subclasses
  `EllipseStyle`, `HyperbolaStyle`, `ParabolaStyle`, `LinePairStyle`,
  `ParallelLinePairStyle`. `Quadric3DStyle(VizStyle)` base; subclasses
  `SphereStyle`, `EllipsoidStyle`, `CylinderStyle`, `PlaneStyle`, `ConeStyle`.
- Line width parameter name is `thickness` (matches `LineStyle.thickness`).
- `Ellipse` is a 2D line-drawn entity (keep `normal`, drop filled-slab +
  wireframe semantics).
- Rename current tube `CircleStyle` → `CylinderCircleStyle` (default for
  `Circle`); new `CircleStyle` renders the circle as a thick line. (This
  supersedes the earlier "LineCircleStyle" name.)
- Circular conic → `Circle` (tube) unchanged for now.
- Remove wireframe params from thick-line styles (`LineStyle`); keep them on
  solid/tube styles.
- `except Exception: pass` around `_push_full_state` becomes
  `logger.exception(...)`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-wireframe-cleanup.md](./01-wireframe-cleanup.md) | Remove wireframe from thick-line styles |
| 2 | [02-circle-style-split.md](./02-circle-style-split.md) | `CylinderCircleStyle` + thick-line `CircleStyle` |
| 3 | [03-conic-quadric-style-hierarchy.md](./03-conic-quadric-style-hierarchy.md) | `ConicStyle`/`Quadric3DStyle` + all style classes |
| 4 | [04-conic-refine-and-error-logging.md](./04-conic-refine-and-error-logging.md) | Auto-refine `Conic` + log silent errors |
| 5 | [05-serializers-dispatch.md](./05-serializers-dispatch.md) | Python wire serializers + dispatch |
| 6 | [06-frontend-renderers.md](./06-frontend-renderers.md) | JS renderers (ellipse line, cone) + factory |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Docs + changelog + full regression |

## Testing as you go

- Python: `uv run pytest py/tests/viz -q` (fast) then `uv run pytest -q` (full).
- JS: `node --input-type=module --check <renderer>` per touched renderer;
  `uv run pytest py/tests/viz/test_export_renderers.py -q` keeps the export
  bundle in lockstep.
- Docs: `uv run mkdocs build --strict`.

## Non-goals

- Dimension-aware 2D/3D default styles — separate idea, see
  `dev/notes/dimension-aware-styles.md`.
- General 3D quadric intersection analysis (already deferred elsewhere).
- `SdfQuadricStyle` / SDF fallback for `Quadric3D`.
