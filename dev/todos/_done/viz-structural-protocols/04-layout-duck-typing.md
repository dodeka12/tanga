# Phase 4 — `_layout.py` duck-typing

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Replace the four `getattr`/`hasattr` sites in `_layout.py` with typed narrowing
(`Positionable`, `View`, `Button`, `HasOnChange`, `FileChooser`), and tighten the
`OverlayContainer` overlay storage from `Any` to `View`.

## Files

- Edit: `py/pytanga/viz/_layout.py`

## Steps

- [x] **4.1 — tighten `OverlayContainer` overlay storage to `View`**
  - Change `self._global_overlay: list[Any]` → `list[View]` and
    `self._scene_overlays: dict[str, list[Any]]` → `dict[str, list[View]]`.
  - Change `add(self, view: Any, …)` → `add(self, view: View, …)`.
  - Verify the sole caller (`visualizer.py:704`) already passes a `View`
    (`isinstance(obj, View)` guard is in place).

- [x] **4.2 — `add()` position**
  - Import `Positionable` from `.views._base` (or `.views`).
  - Replace `if anchor is not None and hasattr(view, "position"):` with
    `if anchor is not None and isinstance(view, Positionable):`.

- [x] **4.3 — `remove_view()` id reads**
  - With `overlays` now `list[View]`, replace `getattr(v, "id", None)` and
    `getattr(view, "id", None)` with the direct `v.id` / `view.id` (`.id` is on
    the `View` base).

- [x] **4.4 — `_register_banner()` handler registration**
  - Import `Button` and `HasOnChange` from `._controls`.
  - Replace:
    ```python
    if getattr(ctrl, "on_click", None) is not None: …
    elif getattr(ctrl, "on_change", None) is not None: …
    ```
    with:
    ```python
    if isinstance(ctrl, Button) and ctrl.on_click is not None: …
    elif isinstance(ctrl, HasOnChange) and ctrl.on_change is not None: …
    ```
  - Preserve the `if`/`elif` ordering and the exact events (`click`, `change`).

- [x] **4.5 — `_handle_file_browser_navigate()` file-chooser fields**
  - Import `FileChooser` from `._controls`.
  - Replace the `getattr(ctrl, "root"/"file_filter"/"folders_only", …)` reads
    with an `if isinstance(ctrl, FileChooser):` branch (default `None`/`""`/
    `False` otherwise), reading `ctrl.root` / `ctrl.file_filter` /
    `ctrl.folders_only` directly.

## Validation

```bash
uv run ty check && uv run ruff check . && uv run pytest py/tests/viz -q
```

## Notes

- `resolve_control()` returns `Any | None`, so `FileChooser`/`Button` narrowing
  is done via `isinstance` at the call site (Rule 2/4 — keep the narrowing local,
  not a `cast`).
- Do not change `Control.register_handlers` or `_register_banner`'s *behavior*
  (which events get registered); only the mechanism of the check changes.
