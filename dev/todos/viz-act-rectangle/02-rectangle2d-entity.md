# Phase 2 — `Rectangle2D` entity + `Rectangle2DStyle` + serializer

## Goal

Add the `Rectangle2D` visualization-only entity (frozen dataclass, like `Box` /
`RegularPolygon`) and its `Rectangle2DStyle`, and serialize it as a new
`Rectangle2D` entity kind.

## Files

- New: `py/pytanga/geometry/entities/rectangle.py`
- Edit: `py/pytanga/geometry/entities/__init__.py` (export)
- Edit: `py/pytanga/viz/_styles/_entity_styles.py` (add `Rectangle2DStyle`)
- Edit: `py/pytanga/viz/serializer.py` (map `Rectangle2D` kind)
- Edit: `py/pytanga/viz/__init__.py` (export `Rectangle2DStyle`)
- New: `py/tests/viz/test_rectangle2d.py` (+ extend `py/tests/geometry/test_viz_entities.py`)

## Steps

- [x] **2.1 — `Rectangle2D` frozen dataclass**
  - `center: Point`, `size: tuple[float, float]`, `normal: Direction = +z`,
    `angle: float = 0.0`; `__init__` coerces via `to_point`/`to_triple`-style
    helpers like `Box` (accept `None` defaults and MV-ish inputs via `_coerce`).
    `__repr__` like `Box`.

- [x] **2.2 — `Rectangle2DStyle(VizStyle)`**
  - `color`, `opacity`, `fill: bool = False`, `fill_opacity: float | None`,
    `thickness: float | None`; `to_dict()` emits `style_type: "Rectangle2DStyle"`.

- [x] **2.3 — serializer mapping**
  - Map `Rectangle2D` → `{ "kind": "Rectangle2D", "center": [...], "size": [...],
    "normal": [...], "angle": 0.0 }` (+ merged style), following the `Box`
    mapping in `serializer.py`.  `normal`/`angle` use the same conventions as
    `RegularPolygon`.

- [ ] **2.4 — export + tests**
  - Export `Rectangle2D` (from `pytanga.geometry`) and `Rectangle2DStyle` (from
    `pytanga.viz`).
  - Test entity coercion + `to_dict`/serialize round-trip + style `to_dict`.

## Validation

`uv run pytest py/tests/viz/test_rectangle2d.py -q && uv run ruff check py/pytanga/geometry/entities/rectangle.py py/pytanga/viz/serializer.py py/pytanga/viz/_styles/_entity_styles.py`

## Notes

- `Rectangle2D` is a **visualization-only** entity (no multivector), like `Box`.
- Do not add `angle` handling in `ActRectangle2D` yet — the entity carries it for
  forward-compatibility only.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
