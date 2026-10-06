# Phase 1 — `screen_space` flag on point styles

## Goal

Add `screen_space: bool = False` to `PointStyle` and serialize it, so every point
style (`SquarePointStyle`, `CirclePointStyle`, `IconPointStyle`,
`CrossHairPointStyle`) can request screen-space sizing.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> style dataclass / `to_dict()` serialization recipe, so the new field aligns
> with the documented style model.  No architecture change is expected.

## Files

- Edit: `py/pytanga/viz/_styles/_entity_styles.py` (`PointStyle`)
- Edit: `py/tests/viz/test_square_point_style.py` (and/or
  `test_circle_icon_point_style.py`)

## Steps

- [x] **1.1 — `PointStyle.screen_space` field**
  - Add `screen_space: bool = False` to `PointStyle` (after `size`).
- [x] **1.2 — `to_dict()`**
  - In `PointStyle.to_dict()`, emit `result["screen_space"] = True` when
    `self.screen_space` is truthy; omit otherwise (keeps the wire minimal and
    the frontend defaults to false).
- [x] **1.3 — Tests**
  - `PointStyle()` default omits `screen_space`; `PointStyle(screen_space=True)`
    emits `"screen_space": true`.
  - Each subclass (`SquarePointStyle`, `CirclePointStyle`, `IconPointStyle`,
    `CrossHairPointStyle`) round-trips the flag through `to_dict()` (they already
    call `super().to_dict()`).

## Validation

```
uv run pytest py/tests/viz -q
```

## Notes

- `screen_space` lives on the `PointStyle` base so all subclasses inherit it with
  no per-subclass changes.
