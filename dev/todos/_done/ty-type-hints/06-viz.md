# Phase 6 — `pytanga/viz`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `viz-architecture.md`, `viz-controls-and-interactions.md`, and
> `viz-theme-system.md`) for the subsystem(s) this work touches, so the new code
> aligns with the documented architecture.  If this work introduces or changes
> architecture, update the developer docs.

## Goal

Annotate `py/pytanga/viz` (64 untyped functions) — the visualizer, scene/views,
serializer, server/transport, styles, SDF, and export modules.  This is the top
consumer of `geometry`/`algebra` types, so annotations use those public aliases.

## Files

- Edit: `py/pytanga/viz/visualizer.py`, `scene.py`, `views.py`
- Edit: `py/pytanga/viz/serializer.py`, `server.py`, `_transport.py`,
  `_scene_objects.py`, `_object_ref.py`, `_scene_handle.py`, `_nodes.py`,
  `_types.py`
- Edit: `py/pytanga/viz/_styles/*.py`, `_themes.py`, `_viz_styles.py`
- Edit: `py/pytanga/viz/sdf/*.py`
- Edit: `py/pytanga/viz/export/*.py`

## Steps

- [x] **6.1 — Core scene/visualizer** — `Visualizer`, `Scene`, `SceneView`,
  `VizObjectRef`, `VizSceneHandle`, and the `add`/`new`/`animate_to` methods
  (entity/operator params via the `Entity` / `Operator` unions, `-> VizObjectRef`).
- [x] **6.2 — Serializer + transport** — `serialize_entity`, `serialize_style`,
  `_nodes`/`_transport`/`_scene_objects` helpers (`-> dict[str, Any]`,
  `-> Transform`); keep `MV` resolution lazy (the existing
  `from pytanga.algebra import MV` inside functions) or under `TYPE_CHECKING`.
- [x] **6.3 — Styles + themes** — the `*Style` dataclasses in `_styles/*.py` and
  `_themes.py` (field types already present; annotate any `__init__`/method and
  `to_dict` / `resolve` helpers `-> dict[str, Any]`).
- [x] **6.4 — SDF + export** — `py/pytanga/viz/sdf/*.py` (`Composed`, `Group`,
  `Object`, `Overlay`, `Visualizer`, `bounds`) and `py/pytanga/viz/export/*.py`
  (`to_html`, `to_gltf`, `to_mp4`, `screenshot`, `_exporter`) with their
  `-> str` / `-> Path` / `-> bytes` returns.

- [x] **6.5 — Resolve `pytanga/viz` ty diagnostics**
  - `uv run ty check py/pytanga/viz` → 0 (baseline: 330 diagnostics — the
    largest triage set).
  - Fix each (real bug / annotation inaccuracy) or add
    `# ty: ignore[<rule>]  # <reason>` for verified false positives.

## Validation

`uv run ruff check --select ANN --ignore ANN401 py/pytanga/viz` → 0
`uv run ty check py/pytanga/viz` → 0
`uv run pytest py/tests/viz -q`

## Notes

- Annotation-only: do **not** touch the unified controls/interactions registry
  (`(id, event)` + `sendEvent`) or any control/view wiring — that is governed by
  `viz-controls-and-interactions.md` and out of scope here.
- `_nodes.py` / `sdf/_compose.py` / `sdf/serializer.py` currently resolve `MV`
  lazily inside functions; keep that pattern (or move it under `TYPE_CHECKING`)
  so the viz ↔ algebra import DAG is unchanged.
