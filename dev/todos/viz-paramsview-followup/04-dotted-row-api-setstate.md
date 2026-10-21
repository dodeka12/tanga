# Phase 4 — Dotted row API + recursive `set_state` (item 4)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (the `ParamsView`
> composite + row-state methods) and `viz-architecture.md`.  This routes the
> existing row API through a dotted-key resolver; no new wire message.

## Goal

`set_value("surface.scale", 2.0)` / `set_visible("surface.angle", False)` work by
dotted key, and `set_state` rebinds nested groups recursively (without firing
`on_change`).

## Files

- **Edit** `py/pytanga/viz/views/params_view.py` — `_resolve()`, route row API,
  recursive `set_state`.
- **Edit** `py/tests/viz/test_params_view.py`.

## Steps

- [x] **4.1 — `_resolve(dotted_key)`**
  - Add `_resolve(key)` that splits on `"."`, walks `self._control_views` down
    `GroupView.children[0]` for each segment, and returns the leaf
    `(view, leaf_key)` (or `(self, key)` when the key does not resolve).
- [x] **4.2 — route the row API through `_resolve`**
  - `set_value`/`set_visible`/`set_enabled`/`set_title`/`set_options` call
    `_resolve` and delegate to the leaf view (a `ControlView` for fields, or the
    `GroupView` from Phase 3 for group rows).
- [x] **4.3 — recursive `set_state`**
  - In `set_state`, after rebinding top-level `instance`/`values`/`_field_types`,
    update value rows as today, and for each group row call
    `nested.set_state(new_value)` (recursing; no `on_change`).
- [x] **4.4 — tests**
  - `set_value("surface.scale", …)` mutates the nested field + pushes; dotted
    `set_visible` hides a nested field; `set_state(Params(grid=7,
    surface=Surface(scale=4.0)))` rebinds `instance.surface` and updates the
    nested control (and never fires `on_change`).

## Validation

```bash
uv run pytest py/tests/viz/test_params_view.py -q
```

## Notes

- `set_state` must rebind the nested **instance** too (the nested dataclass
  object), not just push values, so later edits hit the new object.
- Dotted resolution reuses `GroupView.children[0]` (the nested `ParamsView`)
  exactly as the request describes; no new public accessor.
