# Viz structural Protocols (remove `getattr`/`hasattr` duck-typing) — Overview

**Created:** 2026-10-06 | **Status:** Done | **Branch:** `fix/viz-control-refactor`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Replace the remaining structural `getattr`/`hasattr` duck-typing in the viz
view/control tree with explicit, typed `@runtime_checkable` `Protocol`s and
`isinstance` narrowing — mirroring the completed `ControlView.__getattr__` /
`menu_view` work.  This covers three subsystems:

1. `toolbar_view._apply_toolbar_variant` — the same `hasattr(ctrl, "variant")`
   pattern already removed from `menu_view`.
2. `functions.py` tree-walk — `getattr(view, "scene"/"children"/"overlay", …)`.
3. `_layout.py` — `hasattr(view, "position")`, `getattr(v, "id", …)`,
   `getattr(ctrl, "on_click"/"on_change"/"root"/"file_filter"/"folders_only", …)`.

## Architecture (short)

- **Controls** already expose `self.control: C` (typed) and concrete `*View`
  subclasses already forward fields explicitly (previous plan).  The remaining
  duck-typing is in *containers* that walk or decorate the tree without knowing
  the concrete type.
- The structural contracts are expressed once as runtime-checkable `Protocol`s:
  - `VariantControl` (`variant: EControlVariant`) — control-level, lives in
    `_controls.py` (moved out of `menu_view.py`).
  - `HasOnChange` (`on_change: ControlHandler | None`) — control-level, lives in
    `_controls.py`.
  - `HasChildren` / `HasOverlay` / `HasScene` / `Positionable` — view-level,
    live in `views/_base.py`.
- This follows `docs/dev/architecture/typing-and-annotations.md` Rule 2 (avoid
  `Any`; prefer `Protocol`) and Rule 4 (prefer `isinstance`/`Protocol` over
  `hasattr` duck-checks).

### Fixed contract (do not change across phases)

1. `VariantControl` is defined **once** in `_controls.py` and imported by both
   `menu_view.py` and `toolbar_view.py` (no local re-definition).
2. View-tree `Protocol`s (`HasChildren`, `HasOverlay`, `HasScene`,
   `Positionable`) are defined **once** in `views/_base.py`, all
   `@runtime_checkable`, and imported by `functions.py` and `_layout.py`.
3. No `getattr`/`hasattr` remains for the structural checks listed above; each
   becomes an `isinstance` check against a `Protocol` (or a concrete class where
   a single class owns the field, e.g. `Button`/`FileChooser`).
4. **No behavior change** — only the duck-typing mechanism is replaced.  The
   public API, serialization, and wire format are untouched.

## Decisions (confirmed)

- Use `@runtime_checkable` `Protocol`s (not `getattr`/`hasattr`, not `Any`).
- `VariantControl` and `HasOnChange` live in `_controls.py`; the four view-tree
  `Protocol`s live in `views/_base.py`.
- `on_click` is owned solely by `Button`, so `_layout.py` narrows it with
  `isinstance(ctrl, Button)` (no `HasOnClick` Protocol needed); `on_change`
  spans many controls, so it uses the `HasOnChange` Protocol.
- `OverlayContainer` overlay storage and `add()` are tightened from `Any` to
  `View` (the sole caller `visualizer.py:704` already guards `isinstance(obj,
  View)`), which removes the `getattr(v, "id", …)` reads entirely.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-shared-protocols.md](./01-shared-protocols.md) | Hoist `VariantControl` to `_controls.py`; add `HasOnChange` + view-tree Protocols; update `menu_view.py` import |
| 2 | [02-toolbar-variant.md](./02-toolbar-variant.md) | `toolbar_view._apply_toolbar_variant` uses `ControlView` + `VariantControl` |
| 3 | [03-functions-tree-walk.md](./03-functions-tree-walk.md) | `functions.py` tree-walk uses `HasScene`/`HasChildren`/`HasOverlay` |
| 4 | [04-layout-duck-typing.md](./04-layout-duck-typing.md) | `_layout.py` uses `Positionable`/`View`/`Button`/`HasOnChange`/`FileChooser` |
| 5 | [05-tests-docs-changelog.md](./05-tests-docs-changelog.md) | Tests + docs + changelog |

## Testing as you go

```bash
uv run ty check                                    # correctness (phases 1-5)
uv run ruff check .                                # lint + ANN coverage (phases 1-5)
uv run pytest py/tests/viz -q                      # Python side (phases 1-5)
uv run mkdocs build --strict                       # docs (phase 5)
```

## Non-goals

- No change to the `Control` dataclass fields, the `View` hierarchy, the wire
  format, or runtime behavior.
- No change to `Control.register_handlers` (its `getattr(self, f.name)`
  metaprogramming is intentional — see the plan notes).
- **Not** covering the other `getattr`/`hasattr` clusters (geometry `transform.py`
  vector/rotation coercion, camera-config duck-typing in `_gltf.py`/`frustum.py`,
  style/entity duck-typing in `serializer.py`/`_nodes.py`/`sdf/serializer.py`) —
  those are tracked separately in `dev/todos/viz-remaining-getattr-todos.md`.
- **Not** touching the C++ binding dispatch (`matrix/_dispatch.py`,
  `blade_mask/_dispatch.py`), which resolves names by string and is a documented
  `# ty: ignore` false positive.
