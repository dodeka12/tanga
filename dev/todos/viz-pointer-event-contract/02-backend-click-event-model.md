# Phase 2 — Backend: `ClickEvent` carries the picking ray

## Goal

Give `ClickEvent` the same `ray_origin`/`ray_direction` fields as `DragEvent`
and parse them from the wire, so the backend can resolve the ideal anchor from
the frontend's ray.

## Files

- Edit: `py/pytanga/viz/_interaction.py`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [x] **2.1 — Add `ray_origin`/`ray_direction` to `ClickEvent`**
  - Added `ray_origin: Point` / `ray_direction: Direction` (default `Point(0,0,0)`
    / `Direction(0,0,0)`), documented as the picking ray.
- [x] **2.2 — Parse them in `_parse_event` (CLICK/DBLCLICK branch)**
  - Read `ray_origin` / `ray_direction` and pass them into `ClickEvent`.

## Validation

`uv run pytest py/tests/viz -q`

## Notes

- Defaults are `Point(0,0,0)` / `Direction(0,0,0)` so an event without the ray
  (older frontend / hand-built event) still parses; the anchor-resolution
  fallback is handled in Phase 3.
