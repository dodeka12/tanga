# Phase 1 — Per-tile event contract (backend)

## Goal

Extend the `image_status` record so per-tile events carry `tile_x` / `tile_y`,
before the frontend starts emitting them.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/tests/viz/test_image_status.py`

## Steps

- [ ] **1.1 — `ImageStatusRecord.tile_x` / `tile_y` (`_controls.py`)**
  - Add `tile_x: int | None = None` and `tile_y: int | None = None` to
    `ImageStatusRecord` (documented as 0-based tile coords at `level`).

- [ ] **1.2 — Parse them in `ImageStatus.handle_event` (`_controls.py`)**
  - Read `payload.get("tile_x")` / `payload.get("tile_y")` into the record.

- [ ] **1.3 — Tests (`test_image_status.py`)**
  - Extend the tile-payload test to include `tile_x`/`tile_y` and assert they are
    parsed; assert the `image_loaded` payload leaves them `None`.

## Validation

```
uv run pytest py/tests/viz/test_image_status.py -q
```

## Notes

- No wire-map change: `image_tile_load` / `image_tile_loaded` already map through
  `_EVENT_MSG_MAP`; only the record fields are additive (backward compatible).
