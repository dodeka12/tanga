# Phase 4 — Error-collecting loader

## Goal

Malformed shapes are skipped and reported, never crash and never silently drop.
`load`/`loads` return `LabelMeLoadResult(document, errors)`; `add_shapes`/
`iter_objects` return `(result, errors)`.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/labelme.py`
- Edit: `py/examples/apps/image_labeling_app.py`
- Edit: `py/tests/viz/test_labelme.py`

## Steps

- [x] **4.1 — `LabelMeLoadResult`**
  - Add `@dataclass LabelMeLoadResult` with `document: LabelMeDocument` and
    `errors: list[str]`.
- [x] **4.2 — `_validate_points`**
  - Add `_validate_points(shape, expected_min, expected_exact=None) -> str | None`
    shared by `_entity_from_shape`/`_act_from_shape` (message like
    `"shape 3 ('rear_rim_low'): 'rectangle' needs at least 2 points, got 1"`).
- [x] **4.3 — `load`/`loads`**
  - Parse JSON, validate each shape, skip invalid ones, collect errors, return
    `LabelMeLoadResult`. Unknown `shape_type` is reported, not raised.
- [x] **4.4 — `add_shapes`/`iter_objects`**
  - Return `(added, errors)` / `(pairs, errors)`; skip + report construction
    failures.
- [x] **4.5 — App**
  - Unpack `LabelMeLoadResult`, surface errors (log / print), never crash.
- [x] **4.6 — Tests**
  - A 1-point `"rectangle"` loads with one error and zero shapes; mixed valid +
    invalid files return both; unknown shape type is reported.

## Validation

```
uv run pytest py/tests/viz/test_labelme.py -q && uv run ruff check . && uv run ty check
```

## Notes

- Breaking API (see README "Decisions"); keep the existing `load`/`loads`/
  `add_shapes`/`iter_objects` *names*, change only the return type.
