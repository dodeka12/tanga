# Phase 2 — Nested shared `on_change` + dotted `event.key` (item 3)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (`ControlEvent`,
> `ControlHandler`, the `(id, event)` registry, and how `ParamsView` fills
> `event.key`/`event.value`).  This reuses the existing handler signature; it
> only changes how a nested `ParamsView` is constructed.

## Goal

Editing a nested-group field fires the parent `on_change` with the full panel
state and a dotted `event.key` (`"surface.scale"`), instead of silently only
mutating the nested dataclass.

## Files

- **Edit** `py/pytanga/viz/views/params_view.py` — `key_prefix`, nested handler
  wrapper, `_build_group` forwarding.
- **Edit** `py/tests/viz/test_params_view.py`.

## Steps

- [x] **2.1 — `key_prefix` on `ParamsView`**
  - Add `key_prefix: str = ""` to `__init__` and store `self.key_prefix`.
  - In `_make_handler` / `_make_click_handler`, set
    `event.key = f"{self.key_prefix}{key}"`.
- [x] **2.2 — nested handler wrapper + `_build_group`**
  - `_build_group` creates the nested view as
    `ParamsView(value, id=f"{self.id}.{key}", key_prefix=f"{key}.",
    on_change=self._make_group_handler())`.
  - `_make_group_handler()` returns an async handler that calls
    `self.on_change(self._state(), event)` when set (the parent's full state,
    already mutated because the nested instance is a field of it).
- [x] **2.3 — tests**
  - A nested field change fires the shared handler once with
    `event.key == "surface.scale"` and the top-level instance as `state`; a
    per-field `on_change` on the nested field still fires (with the dotted key).

## Validation

```bash
uv run pytest py/tests/viz/test_params_view.py -q
```

## Notes

- The parent `on_change` still receives the **parent's** `_state()` (top-level
  dict/instance), not the nested view's state — that is the point of one
  handler per panel.
- `key_prefix` is private plumbing; it is not part of the public API surface.
