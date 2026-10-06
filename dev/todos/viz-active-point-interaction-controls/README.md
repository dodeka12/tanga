# Active-point interaction controls — Overview

**Created:** 2026-10-06 | **Status:** Done | **Branch:** `feat/active-elements`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`) for the subsystem(s) this work touches, so the new
> code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Give host apps public control over the `Act*` composite handles and fix the
over-broad "navigation yields to drawing" guard, so a labeling UI can:

1. keep right-click panning alive while a left-button draw mode is armed;
2. show/enable control points only for the currently-selected shape;
3. gate handle editing behind a modifier key (e.g. Shift+drag) declaratively.

## Architecture (short)

Two independent, additive seams:

- **Python (`py/pytanga/viz/_active.py`).** `ActPoint` gains a per-point drag
  modifier requirement; `_ActWithHandles` gains a `_reshape_handles()` subclass
  hook plus bulk `set_handles_enabled` / `set_handles_visible` that iterate every
  handle (reshape + translate + rotate).  Reuses the existing
  `ActSceneObject.set_enabled` / `refresh_interaction` re-push and the
  `DragBinding`-style modifier matching already in the frontend.
- **Frontend (`templates/interaction.js`, `templates/views/three-view.js`).**
  `InteractionController` reports *which* button(s) the pane's surface claims for
  drag; the calibrated-pane viewport pan only refuses those buttons (instead of
  refusing any pan button whenever any surface drag is armed).

## Decisions (confirmed)

- Modifier spec uses the **varargs** pattern (`*modifiers: ModifierKey`), matching
  `DragBinding`/`ClickBinding` — not `frozenset` / iterable-of-strings.
- `set_handles_enabled(enabled: bool = True, *modifiers)` = pure enable/disable +
  optional modifier gate; `set_handles_visible(visible)` = hide + enable/disable
  combined (mirrors the existing `set_translate_handle_visible` /
  `set_rotate_handle_visible`).
- "handles" = **all** handles (reshape + translate + rotate); the existing
  `set_translate_handle_visible` / `set_rotate_handle_visible` stay as
  fine-grained controls.
- Navigation-yield scoping is a frontend-only bug fix (no new Python API).

## Contract (fixed)

```python
# ActPoint (_active.py)
def set_drag_modifiers(self, *modifiers: ModifierKey) -> None: ...

# _ActWithHandles (_active.py) — inherited by
# ActRectangle2D / ActEllipse / ActCircle / ActLine / ActPolygon
def _reshape_handles(self) -> list[ActPoint]: ...   # subclass hook
def _all_handles(self) -> list[ActPoint]: ...       # reshape + translate + rotate
def set_handles_enabled(self, enabled: bool = True, *modifiers: ModifierKey) -> None: ...
def set_handles_visible(self, visible: bool) -> None: ...
```

```js
// InteractionController (interaction.js)
armedSurfaceButtons() -> Set<string>   // 'left'|'middle'|'right'; catch-all claims all
hasArmedSurface() -> boolean           // armedSurfaceButtons().size > 0
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-actpoint-drag-modifiers.md](./01-actpoint-drag-modifiers.md) | `ActPoint.set_drag_modifiers` primitive |
| 2 | [02-composite-handle-controls.md](./02-composite-handle-controls.md) | `_ActWithHandles` bulk handle enable/visible |
| 3 | [03-button-scoped-navigation-yield.md](./03-button-scoped-navigation-yield.md) | JS button-scoped surface yield |
| 4 | [04-example-apps.md](./04-example-apps.md) | Update both labeling apps |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Developer docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q`
- `uv run ruff check .` + `uv run ty check`
- `node --test 'js/dev/tests/*.test.mjs'` + `node js/dev/tests/check-syntax.mjs`
- `uv run mkdocs build --strict` (phase 5)
- Manual smoke: `uv run python py/examples/apps/calibrated_labeling_app.py`
  and `uv run python py/examples/apps/image_labeling_app.py`

## Non-goals

- No new interaction model; `ActSceneObject` / `InteractionSurface` /
  the `(id, event)` registry stay as-is.
- No change to `ImageView` / the flat `ImageCanvas` path (already works).
- No per-pane cursor override.
- No removal of `set_translate_handle_visible` / `set_rotate_handle_visible`.
