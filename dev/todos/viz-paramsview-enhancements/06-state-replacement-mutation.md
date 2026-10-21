# Phase 6 — Whole-state replacement + add/remove rows

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (`control_update`,
> layout re-push) and `docs/dev/architecture/viz-architecture.md` (layout
> reconcile).  `add`/`remove` re-push the `params_view` node (rows), reusing the
> existing `view_layout` reconcile.

## Goal

`set_state(new_instance_or_dict)` replaces the state silently; `add`/`remove`
mutate the rows at runtime.

## Files

- **Edit** `py/pytanga/viz/views/params_view.py`.
- **Edit** `py/tests/viz/test_params_view.py`.

## Steps

- [x] **6.1 — `set_state`**
  - `set_state(new)` rebinds `instance`/`values` (re-deriving `_field_types`),
    updates every row's value (no `on_change`), and pushes the new state; document
    the silent contract.
- [x] **6.2 — `add` / `remove`**
  - `add(key, value, ui)` builds a child control and appends the row;
    `remove(key)` tears it down and forgets its handler; both re-serialize.
- [x] **6.3 — tests**
  - `set_state` updates values and does not fire `on_change`; `add`/`remove`
    update the serialized rows and registered handlers.

## Validation

```bash
uv run pytest py/tests/viz/test_params_view.py -q
```
