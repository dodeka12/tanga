# Phase 15b — `_label_anchor.py` (per-entity anchor registry)

**Parent:** [15-label-anchors-rotation.md](./15-label-anchors-rotation.md)
**Status:** Done

## Goal

New module `py/pytanga/viz/_label_anchor.py` that computes, per entity type,
the 3D anchor (relative to the entity's mesh origin) where its label attaches,
driven by `LabelStyle.along`.

## Interface

```python
def compute_label_anchor(entity, *, along=None, line_length=None) -> tuple[float, float, float]:
```

- `along`: raw `LabelStyle.along` (scalar / 2-tuple / 3-tuple / `None`).
- `line_length`: resolved line length (used only by Line/ReflectionLine).
- Returns the anchor relative to the mesh origin (added to `offset_local` in
  `compute_label_position`).

## Normalization

`_normalize_along(along) -> tuple[float, float, float] | None`:

- `None` → `None`
- scalar `s` → `(s, 0.0, 0.0)`
- len-2 → `(a, b, 0.0)`
- len-3 → `(a, b, c)`
- other lengths → `ValueError`

## Per-entity anchors (relative to mesh origin)

| Entity | formula (default when `along` is `None`) |
|---|---|
| Line | `normalize(dir) · (u · length)` — u default 0.5 (midpoint) |
| ReflectionLine | `_anchor_line(entity.line, …)` |
| Direction | `normalize(dir) · (u · 2.0)` — u default 0.0 |
| PointPair | `(u − 0.5) · (point_b − point_a)` — u default 0.5 |
| Plane | span case `(u−0.5)·span_u + (v−0.5)·span_v`; extent case derive in-plane axes from `normal` scaled by `extent` — u,v default 0.5 (centre) |
| ReflectionPlane | `_anchor_plane(entity.plane, …)` |
| Circle | `v · radius · (cos(2πu)·x̂ + sin(2πu)·ŷ)` in the circle plane — u,v default 0 (centre) |
| Sphere / Inversion | `u·radius · (sin(πw)·cos(2πv), sin(πw)·sin(2πv), cos(πw))` — u,v,w default 0 (centre) |
| default (Point, HPoint, Space, operators) | `(0, 0, 0)` |

`None` → each function's documented default (Line → midpoint; others → the
reference point, i.e. `(0,0,0)` relative).

## Registry

`_ANCHOR_FUNCS: dict[type, Callable]` mapping the entity classes to their
functions; `compute_label_anchor` walks it with `isinstance`. Adding an entity
type = one function + one entry.

## Helpers

Re-implement `_normalize`, `_cross`, `_perpendicular` locally (identical to
`_label_frame.py`, but duplicated to avoid a circular import — `_label_frame.py`
will import `compute_label_anchor`).

## Notes to verify during implementation

- Plane span case: the renderer (`plane.js`) only uses `extent` (a square of
  half-side `extent` centred on `point`), so the anchor uses the same extent
  geometry and ignores `span_u`/`span_v`.
- Circle normal may be `None` → default `(0, 0, 1)`.

## Tests

- `_normalize_along(0.3) == (0.3, 0, 0)`; `(0.1, 0.2) == (0.1, 0.2, 0)`;
  `None is None`; len-4 raises.
- Line `along=0 / 0.5 / 1` → start / mid / end (with a known length).
- Direction default → origin; `along=1` → tip.
- PointPair default → `(0,0,0)`; `along=0`/`1` → endpoints relative to midpoint.
- Circle `along=(0.25, 1)` → rim point; `(0, 0)` → centre.
- Sphere `along=(1, 0, 0)` → pole at distance radius.
- Non-registered entity → `(0,0,0)`.
