# Active object unification — Overview

**Created:** 2026-10-06 | **Status:** Done | **Branch:** `feat/active-elements`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`) for the subsystem(s) this work touches, so the new
> code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Give **every** active object — a bare `ActPoint` and every composite
(`ActRectangle2D`/`ActEllipse`/`ActCircle`/`ActPolygon`/`ActLine`) — the same
public handle API, and fix the labeling-app issues that fell out of live
testing:

- one `set_handles_visible` / `set_handles_enabled` / `set_drag_modifiers` that
  works uniformly (no `hasattr`, no `enabled, *modifiers` combo);
- an active point renders as an **active handle** style while enabled and as its
  **content `Point`** style while disabled-but-visible;
- selecting a second entity clears the first (selection highlight fix);
- a click with the line tool no longer produces an absurdly long line.

## Architecture (short)

Rename the private `_ActWithHandles` base to a public **`ActiveObject`**, and
make **`ActPoint` a subclass of it**.  A point's `_reshape_handles()` returns
`[self]`, so the same bulk methods work for both:

```python
class ActiveObject(ActSceneObject):
    def set_handles_enabled(self, enabled: bool = True) -> None: ...   # over _all_handles()
    def set_handles_visible(self, visible: bool) -> None: ...          # over _all_handles()
    def set_drag_modifiers(self, *modifiers: ModifierKey) -> None: ... # over _all_handles()

class ActPoint(ActiveObject):
    def set_handles_enabled(self, enabled: bool = True) -> None: ...   # leaf: set_enabled + style swap
    def set_drag_modifiers(self, *modifiers: ModifierKey) -> None: ... # leaf: _required_drag_modifiers
    def _reshape_handles(self) -> list[ActPoint]: return [self]
```

## Decisions (confirmed)

- Rename `_ActWithHandles` → **`ActiveObject`** (public, exported from
  `pytanga.viz`); `ActPoint` inherits it.
- A bare `ActPoint` has **two** rendering styles: `handle_style` (active/draggable
  appearance, e.g. square) and `style` (content `Point` appearance, e.g. round).
  `set_handles_enabled` swaps between them; `set_handles_visible` hides/shows.
- `set_handles_enabled(enabled)` takes **only** a bool — the `*modifiers` gating is
  split into the separate `set_drag_modifiers(*modifiers)` (needed on **all**
  active objects).
- `ActiveObject.__init__` accepts the **union** of point + composite kwargs, with
  `translate_handle_style=None` / `rotate_handle_style=None` defaults; `ActPoint`
  does **not** expose translate/rotate handle styles (the point itself is the
  translation handle).
- No `hasattr` — use `isinstance(act, ActiveObject)` / `isinstance(act, ActPoint)`.
- Selection highlight must restore an **explicit** color (a `None` color is dropped
  by both `to_dict()` and the frontend, so it never clears the highlight).
- Drag-to-create must clamp an over-large drag delta / line length.

## Contract (fixed)

```python
# _active.py
class ActiveObject(ActSceneObject):      # renamed from _ActWithHandles
    def __init__(self, *, handler=None, on_drag_start=None, on_drag_end=None,
                 on_click=None, drag_bindings=None, click_bindings=None,
                 cursor=None, style=None, handle_style=None,
                 translate_handle_style=None, rotate_handle_style=None,
                 act_style=None) -> None: ...
    def set_handles_enabled(self, enabled: bool = True) -> None: ...
    def set_handles_visible(self, visible: bool) -> None: ...
    def set_drag_modifiers(self, *modifiers: ModifierKey) -> None: ...

class ActPoint(ActiveObject):
    def __init__(self, x, y=0.0, z=0.0, *, drag_mode=None, act_style=None,
                 handle_style=None, style=None, handler=None,
                 on_drag_start=None, on_drag_end=None, on_click=None,
                 cursor=None, drag_bindings=None, click_bindings=None) -> None: ...
    def set_handles_enabled(self, enabled: bool = True) -> None: ...
    def set_drag_modifiers(self, *modifiers: ModifierKey) -> None: ...
    def _reshape_handles(self) -> list[ActPoint]: ...
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-rename-active-object.md](./01-rename-active-object.md) | Rename `_ActWithHandles` → `ActiveObject` + export |
| 2 | [02-actpoint-as-active-object.md](./02-actpoint-as-active-object.md) | `ActPoint` inherits `ActiveObject`, gains `handle_style` |
| 3 | [03-unified-handle-controls.md](./03-unified-handle-controls.md) | Unified `set_handles_*` + `set_drag_modifiers` + style swap |
| 4 | [04-example-apps.md](./04-example-apps.md) | Selection fix + type-driven gating in both apps |
| 5 | [05-drag-delta-clamp.md](./05-drag-delta-clamp.md) | Clamp drag delta / line length |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Developer docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q`
- `uv run ruff check .` + `uv run ty check`
- `node --test 'js/dev/tests/*.test.mjs'` + `node js/dev/tests/check-syntax.mjs`
- `uv run mkdocs build --strict` (phase 6)
- Manual smoke: `uv run python py/examples/apps/calibrated_labeling_app.py`
  and `uv run python py/examples/apps/image_labeling_app.py`

## Non-goals

- No new interaction model; `ActSceneObject` / `InteractionSurface` /
  the `(id, event)` registry stay as-is.
- No change to the composite handle *spawning* mechanism (handles still get their
  style at `_spawn_handle` time; only the public API + `ActPoint` change).
- No removal of `set_translate_handle_visible` / `set_rotate_handle_visible`.
