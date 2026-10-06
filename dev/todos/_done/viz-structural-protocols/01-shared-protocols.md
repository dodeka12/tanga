# Phase 1 — Shared Protocols

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Introduce the single-source structural `Protocol`s that phases 2–4 consume, and
relocate the `VariantControl` `Protocol` out of `menu_view.py` into
`_controls.py`.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/views/_base.py`
- Edit: `py/pytanga/viz/views/menu_view.py`

## Steps

- [x] **1.1 — hoist `VariantControl` into `_controls.py`**
  - Move the `@runtime_checkable class VariantControl(Protocol)` definition
    (currently in `menu_view.py`) into `_controls.py`, next to `EControlVariant`
    (it declares `variant: EControlVariant`).
  - Add the needed `Protocol`/`runtime_checkable` imports to `_controls.py`.
  - Update `menu_view.py` to import `VariantControl` from `.._controls` and
    delete its local definition (keep `ControlView` import there as-is).

- [x] **1.2 — add `HasOnChange` to `_controls.py`**
  - Add `@runtime_checkable class HasOnChange(Protocol)` declaring
    `on_change: ControlHandler | None`.
  - Place it near `ControlHandler` (it references that alias).

- [x] **1.3 — add view-tree `Protocol`s to `views/_base.py`**
  - Add four `@runtime_checkable` `Protocol`s next to `View`:
    - `HasChildren` — `children: list[View]`
    - `HasOverlay` — `overlay: list[View]`
    - `HasScene` — `scene: str`
    - `Positionable` — `position: EAnchor | str | None`
  - Import `Protocol`, `runtime_checkable` from `typing` and `EAnchor` from
    `.._anchor` (no circular import — `_anchor.py` is a standalone `StrEnum`).

## Validation

```bash
uv run ty check && uv run ruff check . && uv run pytest py/tests/viz -q
```

## Notes

- `Protocol`s are data-only (attribute declarations), so `isinstance` against
  them works at runtime because they are `@runtime_checkable`.
- `View` is referenced inside `views/_base.py` itself; `from __future__ import
  annotations` is already present, so the forward references are fine.
- Keep `VariantControl` and `HasOnChange` in `_controls.py` (control-level), and
  the view-tree `Protocol`s in `_base.py` (view-level) — this matches the
  "contract lives next to the type it describes" convention.
