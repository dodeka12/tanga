# Phase 4 — Example apps: selection fix + type-driven gating

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`).
> Example-only change; no architecture change.

## Goal

Fix the selection highlight and make both labeling apps gate editing by the
active tool type (points disabled-but-visible outside point mode; composite
handles hidden outside their type), using `isinstance(act, ActiveObject)`
instead of `hasattr`.

## Files

- Edit: `py/examples/apps/calibrated_labeling_app.py`
- Edit: `py/examples/apps/image_labeling_app.py`
- Edit: `py/tests/viz/test_calibrated_labeling_example.py` (+ any new image-app test)

## Steps

- [x] **4.1 — `calibrated_labeling_app.py`: selection color fix.**
  - In `_set_selected_style`, restore an explicit color instead of the full style:
    `self._world.update_style(shape_act.entity_id, color=(self.selected_color if
    selected else (style.color or "#ffffff")))`.
- [x] **4.2 — `calibrated_labeling_app.py`: `_sync_handles` via `ActiveObject`.**
  - Import `ActiveObject`; replace the `hasattr` branch:
    ```python
    if isinstance(act, ActiveObject):
        act.set_handles_visible(active_type is not None and isinstance(act, active_type))
    elif isinstance(act, ActPoint):
        act.set_handles_enabled(self._mode == "point")
    ```
- [x] **4.3 — `image_labeling_app.py`: migrate `_set_extra_handles`.**
  - Replace `_set_extra_handles` with a `_sync_handles` driven by `set_mode`, using
    `isinstance(act, ActiveObject)` / `isinstance(act, ActPoint)` as above; make
    `_select`/`_deselect` highlight-only.
  - Apply the same explicit-color restore in its selection path.
- [x] **4.4 — Tests.**
  - Extend `test_calibrated_labeling_example.py`: exclusive selection +
    `test_handles_follow_active_type` with a bare point (point disabled but visible
    outside point mode).

## Validation

`uv run pytest py/tests/viz/test_calibrated_labeling_example.py -q && uv run python -m py_compile py/examples/apps/image_labeling_app.py py/examples/apps/calibrated_labeling_app.py && uv run ruff check py/examples/apps/ && uv run ty check py/examples/apps/`

## Notes

- The calibrated app already has `_sync_handles`; only the `hasattr`→`isinstance`
  switch + point branch + selection fix apply there. The image app needs the full
  `_set_extra_handles`→`_sync_handles` migration.
