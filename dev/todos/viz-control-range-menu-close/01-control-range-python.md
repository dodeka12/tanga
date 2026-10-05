# Phase 1 — Control range (Python model/view/API)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add `set_min` / `set_max` / `set_step` / `set_range` to `SliderView` and
`ValueEditView`, and expose `Visualizer.set_control_range` (via `LayoutHost`),
so a mounted control's numeric range can be changed at runtime without
re-pushing `view_layout`.

## Files

- Edit: `py/pytanga/viz/views/control_views.py`
- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_views.py`
- Edit: `py/tests/viz/test_layout_api.py`

## Steps

- [x] **1.1 — `SliderView` range setters (`control_views.py`)**
  - Add `set_min(v)`, `set_max(v)`, `set_step(v)`, and
    `set_range(min=None, max=None, step=None)`.
  - Each coerces `float`, mutates `self.control.<field>`, then clamps
    `self.control.value` into `[min, max]`.
  - Push changed fields via `self._push_state(self.id, {...})`; when the value
    was clamped, also push `self._push(self.id, self.control.value)`.

- [x] **1.2 — `ValueEditView` range setters (`control_views.py`)**
  - Mirror 1.1 for `ValueEditView` (`min`/`max`/`step` only; leave
    `digits`/`editable` untouched).

- [x] **1.3 — `LayoutHost.set_control_range` (`_layout.py`)**
  - Add `set_control_range(cid, *, min=None, max=None, step=None)` next to
    `set_control_enabled`: `resolve_control(cid)`; no-op when `None`; mutate
    `min`/`max`/`step`; clamp `value`; push `control_state` (changed fields)
    and `control_update` when the value changed.

- [x] **1.4 — `Visualizer.set_control_range` (`visualizer.py`)**
  - One-line forwarder `self._layout.set_control_range(control_id, min=min,
    max=max, step=step)` mirroring `set_control_enabled`.

- [x] **1.5 — Tests**
  - `test_views.py`: `SliderView.set_range` / `ValueEditView.set_range` mutate
    `control`, push via a stubbed `_push_state` / `_push`, and clamp an
    out-of-range value (a value push is fired).
  - `test_layout_api.py` (`TestControlStatePush`): `set_control_range` mutates
    + pushes for a mounted slider / value-edit; no-op on unknown id.

## Validation

```bash
uv run pytest py/tests/viz/test_views.py py/tests/viz/test_layout_api.py -q
```

## Notes

- `ControlView._serialize` already merges `control.serialize()`, so a changed
  range persists on the next full layout push with no extra work.
