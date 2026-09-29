# Phase 2 — Per-role handle styles + composite handle switch

## Goal

Add `translate_handle_style` / `rotate_handle_style` to the composites and switch
their default handles from square markers to circle (vertices/corners/radii) and
icon (translate/rotate) markers, using the Phase 1 styles.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  This stays inside the existing `_ActWithHandles`
> composite recipe; no architecture change.

## Files

- Edit: `py/pytanga/viz/_active.py` (`_ActWithHandles`, `ActRectangle2D`,
  `ActEllipse`, `ActPolygon`, `ActPoint`)
- Edit: `py/examples/viz/image/image_labeling.py` (drop now-redundant explicit styles)
- Edit: `py/tests/viz/test_act_*.py` (assert new defaults)

## Steps

- [x] **2.1 — Broaden handle style types**
  - Change `handle_style` param types from `SquarePointStyle | None` to
    `PointStyle | None` in `_ActWithHandles` and the three composites.
- [x] **2.2 — `_ActWithHandles` gains per-role style slots**
  - Add `translate_handle_style` / `rotate_handle_style` storage + a
    `_resolve_handle_style()` that applies defaults:
    - vertex/corner/radius handle → `handle_style` or `CirclePointStyle()`;
    - translate handle → `translate_handle_style` or
      `IconPointStyle(icon="material:open_with")`;
    - rotate handle → `rotate_handle_style` or
      `IconPointStyle(icon="material:rotate_right")`.
- [x] **2.3 — Thread params through the composites**
  - Add `translate_handle_style` to `ActRectangle2D`, `ActEllipse`, `ActPolygon`,
    and `rotate_handle_style` to `ActEllipse` (and `ActRectangle2D` in Phase 3).
  - Pass them into `_spawn_handles`; use `translate_handle_style` for the
    centroid handle and `rotate_handle_style` for the rim handle.
- [x] **2.4 — `ActPoint` default**
  - Leave `ActPoint` defaulting to `PointStyle` (sphere) unless a `handle_style`
    is given — composites now pass `CirclePointStyle` explicitly so `ActPoint`'s
    own default is unchanged.
- [x] **2.5 — Update the example + tests**
  - In `image_labeling.py`, replace the explicit `SquarePointStyle` handle/vertex
    styles with the new circle/icon defaults (or keep explicit overrides where
    the color differs).
  - Update `test_act_*` assertions that assumed square handles to expect circle.

## Validation

```
uv run pytest py/tests/viz -q
uv run python tools/build-viewer-js.py --check
```

## Notes

- Keep the default style change **opt-in per composite** so a bare `ActPoint`
  still renders as a sphere — only composites default their handles to circle/icon.
