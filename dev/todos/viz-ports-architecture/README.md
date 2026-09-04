# Viz Layout / Overlay / Scene Model — Overview

**Created:** 2026-09-04 | **Status:** In progress | **Branch:** `feat/view-architecture`

## Goal

Rework scene / layout / control ownership so data flows through a single
hierarchy (layout → base/overlay → views/scenes) instead of a set of parallel
"global registry" dicts.  Building on the already-shipped ports work
(`Transport` + `LayoutHost` + hosts), this plan:

- makes `LayoutHost` own the **scenes** (entity containers) *and* the **layouts**;
- introduces a first-class **`Layout`** (a `base` view tree + an
  **`OverlayContainer`** for anchored groups, draggable dialogs, banners, editor);
- makes **`Scene`** own its **entities** and the typed entity API
  (`add`/`new`/`update`/`remove`/`clear`);
- removes the control `add_*` facades and the runtime value API from
  `ControlHost` — controls are `*View` classes that carry their own
  `set_value`/`undo`/`redo` and are added to a layout's **overlay**;
- makes every scene auto-create a same-named single-`SceneView` layout, so URLs
  always name a layout (`/?view=<name>`) and scene URLs come for free.

## Architecture (short)

```
Visualizer (facade + composition root; lifecycle)
├── Transport  (WebSocketTransport)              ← communication
├── LayoutHost
│   ├── scenes:  dict[name, Scene]               ← entity containers (add_scene)
│   │     └── Scene → entities + add/new/update/remove/clear
│   └── layouts: dict[name, Layout]              ← first-class layouts
│         └── Layout
│             ├── base:    View (SplitView/StackView/SceneView)
│             └── overlay: OverlayContainer (anchors, dialogs, banners, editor)
├── ControlHost  ← inbound dispatch only (handle_event); no add_*, no value API
├── ThemeHost / InteractionHost
└── (BannerHost/DialogHost/EditorHost are folded into OverlayContainer)
```

## Canonical contract (fixed up front)

### `Layout`

```python
class Layout:
    base: View                        # the root view of the base layer
    overlay: OverlayContainer          # floats over base (groups/dialogs/banners)
```

### `OverlayContainer`

Owns everything floating above the base layer and provides:

- `add(view, *, anchor=None)` — mount an anchored `GroupView`/`MenuView`.
- `show_dialog(...)` / `remove_dialog(...)` / `clear_dialogs()` — draggable dialogs.
- `show_banner(...)` / `alert(...)` / `confirm(...)` / `remove_banner(...)` / `clear_banners()` — transient banners.
- `open_editor(...)` — one-shot text editor.

### `Scene`

Owns entities and the typed entity API: `add`/`new`/`update`/`remove`/`clear`
(plus `add_object`/`add_group`/`add_label` low-level).  It is referenced by
`SceneView(name)`; one scene can appear in many panes and layouts.

### URL → layout (explicit)

URLs name **layouts**, never scenes.  `add_scene(name)` creates `Scene(name)`
*and* `Layout(name, base=SceneView(name))`; the name is shared (raise if taken).
`/?view=<name>` serves that layout; `/` serves the default `""` layout.

### API surface

```python
viz.add_scene("a")                         # Scene("a") + Layout("a", SceneView("a"))
viz.add_layout("ab", SplitView("h", [SceneView("a"), SceneView("b")]))
viz.set_layout("ab", new_root)             # == viz.layout["ab"].base = new_root

viz.layout                                 # LayoutHost
viz.layout["ab"].base                      # root view of "ab"
viz.layout["ab"].overlay.add(GroupView(...), anchor=...)
viz.layout.base                            # == viz.layout[""].base
viz.layout.overlay                         # == viz.layout[""].overlay

viz.add(Point(3,0,0))                      # entity → main scene
viz.add(GroupView("panel", [SliderView("s", ...)]))   # view → default layout overlay
viz.scene("a").add(Line(...))              # entity → scene "a"

s = SliderView("s", ...); s.set_value(5.0) # controls carry their own value ops
t = TableView("t", ...); t.undo(); t.redo()
```

## Decisions (confirmed)

- `scenes` lives in `LayoutHost`; `add_scene` auto-creates a same-named layout
  (raise if the name is taken) — this supplies the scene-URL sugar.
- Controls are added to a layout's **overlay**, never to a scene.
- `OverlayContainer` is an explicit class (anchors, draggable dialogs, banners);
  `BannerHost`/`DialogHost`/`EditorHost` are folded into it.
- `Scene` owns entities *and* the typed entity API; `Visualizer`/`VizSceneHandle`
  delegate ("pick the right scene").
- Runtime value API is removed from `ControlHost`; each control carries
  `set_value`/`undo`/`redo`; `_control_views` index is deleted (inbound dispatch
  walks the layout tree).
- Control `add_*` (and `add_control_group`/`add_menu`) are deleted; `Visualizer.add`
  becomes polymorphic (entity vs view).
- No `EntityHost`, no `SceneAccess` port (`LayoutHost.scene(name)` is the access).
- `Visualizer.__getattr__` is replaced by explicit thin forwarders.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-layout-overlay-classes.md](./01-layout-overlay-classes.md) | `Layout` + `OverlayContainer` classes |
| 2 | [02-scenes-into-layout-host.md](./02-scenes-into-layout-host.md) | `scenes` into `LayoutHost` + auto-layout on `add_scene` |
| 3 | [03-overlay-container-hosts.md](./03-overlay-container-hosts.md) | Fold banners/dialogs/editor into `OverlayContainer` |
| 4 | [04-entity-api-into-scene.md](./04-entity-api-into-scene.md) | Entity API into `Scene` |
| 5 | [05-value-api-controls.md](./05-value-api-controls.md) | Value API onto controls; delete `add_*`/orphan/`_control_views` |
| 6 | [06-polymorphic-add.md](./06-polymorphic-add.md) | Polymorphic `Visualizer.add()` + `add_layout`/`set_layout` |
| 7 | [07-visualizer-facade.md](./07-visualizer-facade.md) | `Visualizer` facade + explicit forwarders |
| 8 | [08-docs-changelog.md](./08-docs-changelog.md) | Docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz -q` (every phase); `uv run pytest -q` (final).
- **Docs:** `uv run mkdocs build --strict` (final phase).

## Non-goals

- No new wire messages (phases 1–3, 7; phases 4–6 are API changes with test/doc updates).
- No DI framework — plain constructor injection.
- No frontend changes (the `view_layout`/`banner_*`/`dialog_*` messages are unchanged).
- No change to `Transport`/`Control.handle_event` (kept as-is).
