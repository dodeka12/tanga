# Active shape labeling (ActEllipse / ActPolygon / selection / keyboard) — Overview

**Created:** 2026-09-28 | **Status:** Done | **Branch:** `feat/more-act-entities`

## Goal

Extend `pytanga.viz` with two new active scene objects — `ActEllipse` (a
draggable, resizable, rotatable ellipse) and `ActPolygon` (an editable
open/closed `PointPath` whose start/end vertices can be extended with Ctrl+drag
and trimmed with Ctrl+right-click) — plus selection support (`on_click` on the
composite act bodies) and a general per-scene keyboard-shortcut facility
(`on_key`). Then extend the `py/examples/viz/image/rectangle_labeling.py`
example into a multi-shape labeling tool that can select, re-edit, and delete
shapes (Delete/Backspace/Escape).

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`) for the subsystem(s) this work touches, so the new
> code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs (the keyboard facility extends
> the documented interaction contract — see phase 08).

## Architecture (short)

- **New act composites** live in `py/pytanga/viz/_active.py` as `ActSceneObject`
  subclasses mirroring `ActRectangle2D`: a visual-only body entity plus `ActPoint`
  handles; `remove()` removes body + handles; a shared private `_ActWithHandles`
  base holds the handle bookkeeping so the three composites don't triplicate it.
- **Selection is body-`on_click`.** The three composites accept `on_click` and
  emit a body `CLICK` trigger when set (reusing `ActSceneObject`'s existing click
  wiring). Existing `rectangle_labeling.py` behaviour is unchanged until it opts
  in.
- **Keyboard folds into the existing interaction path** (per the
  `dev/todos/viz-keyboard-shortcuts.md` sketch, with per-pane focus — confirmed):
  handlers register in the one `ControlHandlerRegistry` under
  `(key:{scene}:{key}, "key")`; the per-scene key list rides on
  `SceneConfig.keyboard`; the frontend sends `interaction:key` from a per-pane
  `keydown` listener attached to each `ThreeJsView` pane's DOM element.

## Fixed contract (up front)

### ActPoint — new bindings (phase 1)

```python
ActPoint(x, y=0.0, z=0.0, *,
         drag_mode=None, act_style=None, handler=None,
         on_drag_start=None, on_drag_end=None, on_click=None, cursor=None,
         drag_bindings: list[DragBinding[ActSceneObject]] | None = None,
         click_bindings: list[ClickBinding[ActSceneObject]] | None = None)
```

`interaction_config` additionally emits one `DRAG` trigger per `drag_bindings`
entry (`mouse_button` + `modifiers` + `drag_mode`) and one `CLICK` trigger per
`click_bindings` entry (`mouse_button` + `modifiers`), mirroring
`ActImagePlane.interaction_config`.

### ActRectangle2D — body `on_click` (phase 2)

```python
ActRectangle2D(center=None, size=None, *,
               show_translate_handle=True, handle_style=None, act_style=None,
               on_corner_drag=None, on_translate=None, on_change=None,
               on_click: ActClickHandler | None = None)
```

When `on_click` is set, `interaction_config` is `enabled=True` with a `CLICK`
trigger (`mouse_button=LEFT`).

### ActEllipse (phase 3)

```python
ActEllipse(center=None, radius_u=1.0, radius_v=0.5, *, angle=0.0,
           show_translate_handle=True, show_rotate_handle=True,
           handle_style=None, act_style=None,
           on_radius_drag=None, on_translate=None, on_rotate=None,
           on_change=None, on_click=None)
```

`entity` → `Ellipse` whose `dir_u`/`dir_v` encode `angle` (radians). `on_change`
receives the new `Ellipse`. Handles: two radius handles, one translate handle,
one rotate handle.

### ActPolygon (phase 4)

```python
ActPolygon(points, *, closed=True, show_translate_handle=True,
           handle_style=None, act_style=None,
           on_vertex_drag=None, on_translate=None, on_change=None, on_click=None)
```

`entity` → `PointPath` (closed by appending the first vertex when `closed=True`).
`on_change` receives `list[Point]`. Start/end handles: Ctrl+drag inserts a new
endpoint; Ctrl+right-click deletes it (see phase 4).


### Keyboard — API + wire (phases 5–6)

```python
# py/pytanga/viz/_interaction.py (or _keyboard.py)
@dataclass
class KeyEvent(ControlEvent):          # NOT InteractionEvent (no object/camera)
    key: str
    modifiers: frozenset[ModifierKey]
    scene: str = ""

@dataclass
class KeyBinding:
    key: str
    modifiers: frozenset[ModifierKey]
    handler: Callable[[KeyEvent], Awaitable[None]]

# Visualizer / VizSceneHandle / ImageCanvas
on_key(key, handler, *, modifiers=None, scene_name="") -> None
```

Wire contract:

- `SceneConfig.to_dict()` adds, only when non-empty:
  `"keyboard": [{"key": "<k>", "modifiers": ["ctrl", ...]}, ...]`.
- Frontend key message (per-pane keydown):
  `{ "type": "interaction:key", "event_type": "key", "scene": "<name>",
     "key": "<k>", "modifiers": [...], "browser_id": "<id>" }`.
- Backend dispatch: `InteractionHost._dispatch_interaction_event` special-cases
  `msg_type == "interaction:key"` → build `KeyEvent` → look up
  `(f"key:{scene}:{key}", "key")` in `ControlHandlerRegistry` (origin
  `INTERACTION`) → run the handler.

## Decisions (confirmed)

- Key handler folds into the interaction path with **per-pane focus** (keydown
  listener on each `ThreeJsView` pane's DOM element), per the
  `viz-keyboard-shortcuts.md` sketch.
- Key matching uses a bare key string + `modifiers` (reusing `KeyModifier`),
  consistent with `DragBinding`/`ClickBinding`; not a new `KeyChord` type.
- Selection is body `on_click` (reusable), not example-side hit-testing.
- `ActPolygon` models an editable path with explicit start/end; `closed` flag
  controls whether the rendered `PointPath` is closed.
- Example extends `rectangle_labeling.py` in place (keeps filename; docs already
  link to it).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-act-point-bindings.md](./01-act-point-bindings.md) | `ActPoint` gains `drag_bindings`/`click_bindings` + trigger emission |
| 2 | [02-shared-handle-base-rect-on-click.md](./02-shared-handle-base-rect-on-click.md) | `_ActWithHandles` base; refactor `ActRectangle2D`; add body `on_click` |
| 3 | [03-act-ellipse.md](./03-act-ellipse.md) | `ActEllipse` with radius/translate/rotate handles |
| 4 | [04-act-polygon.md](./04-act-polygon.md) | `ActPolygon` with vertex/translate handles + Ctrl insert/delete |
| 5 | [05-keyboard-backend.md](./05-keyboard-backend.md) | `KeyEvent`/`KeyBinding`, `on_key`, `SceneConfig.keyboard`, server dispatch |
| 6 | [06-keyboard-frontend.md](./06-keyboard-frontend.md) | per-pane keydown listener + `interaction:key` send |
| 7 | [07-example-shape-labeling.md](./07-example-shape-labeling.md) | extend example into a multi-shape labeling tool |
| 8 | [08-docs-tests-changelog.md](./08-docs-tests-changelog.md) | docs, tests, dev-docs update, changelog |

## Testing as you go

- Python (each backend phase): `uv run pytest py/tests/viz -q`
- Full backend (final): `uv run pytest -q`
- Example docs (phase 8): `uv run python tools/generate-example-docs.py --check`
- Docs (phase 8): `uv run mkdocs build --strict`
- Frontend (phase 6): manual browser check (no automated JS harness); backend
  `uv run pytest py/tests/viz -q` stays green.

## Non-goals

- No new geometry MV-backed entities — the composites wrap the existing viz-only
  `Ellipse` / `PointPath` / `Rectangle2D`.
- No visible keyboard-shortcut hints in the toolbar (deferred; see sketch).
- No undo/redo for shape edits.
- No polygon interior-vertex insert/delete (only start/end, per request).
- `ActPoint`'s `drag_bindings` is for completeness/symmetry; only
  `click_bindings` is strictly required by `ActPolygon`.
