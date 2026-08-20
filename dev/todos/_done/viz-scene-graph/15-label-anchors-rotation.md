# Phase 15 — Per-entity label anchors + screen-plane label rotation

**Status:** Done

## Goal

1. Give every entity type an explicit, extensible **anchor point** — the 3D
   position where its label attaches — computed from the entity's own geometry
   and a per-kind `along` parameter (scalar, or 2-/3-tuple) that parameterizes
   the entity's extent.
2. Add **screen-plane label rotation** about the final anchor, so labels (e.g.
   coordinate-axis tick labels) can be tilted to avoid overlap.

## Current state

- Label position is computed by `_label_frame.compute_label_position(entity,
  offset_local)` → `offset_local` applied in the entity's local frame, relative
  to the entity's **mesh origin**. The "natural anchor" is implicit (== mesh
  origin); there is a dead `get_label_anchor()` in `_label.py` that computes
  the entity-specific anchor but is never wired in.
- `LabelStyle` carries `offset_local` (3D, baked into position on the backend,
  stripped on serialize) and `offset_2d` + `align` (2D, applied on the frontend
  as CSS in `scene-builder.js buildOverlay` and `axis.js makeLabel`).
- Axis value labels are drawn in `axis.js addAxis` via `makeLabel`, applying
  `offset_2d`/`align` as CSS transforms — no rotation.
- Line length: `_serialize_line` sends `0` for infinite lines; the frontend
  `line.js resolveLength()` falls back to `LineStyle.length` (default 20.0).

## Design

### 1. `LabelStyle.along` — anchor parameterization

`along: float | tuple[float, float] | tuple[float, float, float] | None = None`

Normalized to `(u, v, w)`:

- `None` → per-kind default
- scalar `s` → `(s, 0, 0)`
- `(a, b)` → `(a, b, 0)`
- `(a, b, c)` → `(a, b, c)`

Each entity uses the first `dim` components (dim = 1 / 2 / 3):

| Entity | dim | meaning | default |
|---|---|---|---|
| Line / ReflectionLine | 1 | `u` = fraction along segment (0=origin, 0.5=mid, 1=end) | `0.5` |
| Direction | 1 | `u` = fraction along arrow (0=origin, 1=tip) | `0.0` |
| PointPair | 1 | `u` = fraction A→B (0.5 = midpoint) | `0.5` |
| Plane / ReflectionPlane | 2 | `u,v` = fractions along the two in-plane axes (0,0 = ref point) | `(0,0)` |
| Circle | 2 | `u` = angle fraction (0→2π), `v` = radius fraction (0=center, 1=rim) | `(0,0)` |
| Sphere / Inversion | 3 | `u` = radius fraction, `v,w` = two angle fractions | `(0,0,0)` |
| Point / HPoint / Space / other ops | 0 | ignored | — |

### 2. `_label_anchor.py` — per-entity anchor registry (new module)

`compute_label_anchor(entity, style)` returns the anchor **relative to the
entity's mesh origin**, dispatched by type through a registry of `_anchor_*`
functions. Adding a new entity type = one function + one registry entry.

- Line: `normalize(dir) * (u * length)` — needs the resolved length (§4).
- ReflectionLine: same, via `entity.line`.
- Direction: `normalize(dir) * (u * 2.0)` (rendered arrow length).
- PointPair: `(u - 0.5) * (point_b - point_a)` (mesh is at the midpoint).
- Plane / ReflectionPlane: `u * span_u + v * span_v` (or derived from `extent`
  when `span_u`/`span_v` are absent).
- Circle: `v * radius * (cos(2π·u)·x + sin(2π·u)·y)` in the circle's plane
  frame (x/y perpendicular to the normal).
- Sphere / Inversion: spherical direction from `(u, v, w)` scaled by `radius`.
- default → `(0, 0, 0)`.

Consolidate the dead `get_label_anchor()` from `_label.py` into this module
(remove the dead copy once no caller remains).

### 3. `LabelStyle.rotation` — screen-plane rotation

`rotation: float | None = None` (degrees, screen plane, about the final anchor;
positive = clockwise, matching CSS).

Applied on the frontend by appending `rotate(...)` to the existing CSS
transform and setting `transform-origin` to the align point, so the rotation
is about the anchor rather than the element centre:

```js
div.style.transformOrigin = `${align[0] * 100}% ${align[1] * 100}%`;
div.style.transform =
  `translate(${off2d[0]}px, ${off2d[1]}px) translate(${tx}%, ${ty}%) rotate(${rotation}deg)`;
```

Applied in **both** `scene-builder.js buildOverlay` (entity labels) and
`axis.js makeLabel` (axis value labels). `rotation` is serialized in the label
style (a frontend concern, like `offset_2d`/`align`).

### 4. Backend line length resolution (prerequisite)

`resolve_line_length(line, *, styles_map, props)`:

- finite `line.length` → it
- else `props["style"].length` override → it
- else `styles_map["Line"].length` (canonical default 20.0)

Used by `_serialize_line` (emit a valid length instead of `0`) and by the Line
anchor, so backend and frontend agree on the rendered length.

## Sub-plans

The implementation is split into four detailed sub-plans:

| Sub-plan | Covers |
|---|---|
| [15a-label-style-and-length.md](./15a-label-style-and-length.md) | `LabelStyle.along`/`rotation` fields, Line default, strip-on-serialize, `resolve_line_length` + `_serialize_line` — **DONE** |
| [15b-label-anchor-module.md](./15b-label-anchor-module.md) | `_label_anchor.py` — normalization, per-entity anchor registry + formulas — **DONE** |
| [15c-anchor-position-wiring.md](./15c-anchor-position-wiring.md) | `compute_label_position` + `visualizer.py`/`scene.py` callers + remove dead `get_label_anchor` — **DONE** |
| [15d-label-rotation.md](./15d-label-rotation.md) | Frontend screen-plane rotation (`buildOverlay` + `axis.js`) — **DONE** |

Remaining (do last):

- [x] Changelog: add to the existing unreleased `docs/changelog/2026-08-17_13b30f7.md`.
- [x] Docs: `docs/py/viz/labels.md` (`along` + `rotation`; `styles.md` has no
      `LabelStyle` section).

## Tests

- `along` normalization (scalar / 2-tuple / 3-tuple / None).
- Line anchors: `u=0/0.5/1`; infinite line default length; style-override length.
- Direction / PointPair / Plane / Circle / Sphere anchors (default and non-default `along`).
- `rotation` is serialized; `along` is stripped from the serialized label style.
- Frontend smoke: label rotated about its anchor in live viewer + export;
  axis value labels rotated.
- `uv run pytest py/tests/viz -q` still passes.

## Verification

- Line labels sit at the segment midpoint by default; `along=0`/`1` at the ends.
- Non-line labels are unchanged (anchor `(0,0,0)`).
- `rotation` tilts labels about their anchor in both live and export.
- Axis tick labels can be rotated so longer labels don't overlap.

