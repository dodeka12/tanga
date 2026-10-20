# Changes since version 2.21.1 (2.21.2-rc1)

## New Features
- **Per-pane runtime visibility** — `SceneView.set_visible(entity_id, visible)`
  toggles an entity in one pane at runtime via a granular `view_visibility`
  message (no layout re-push, no rebuild).
- **Add-time per-view scope** — `Scene.new`/`Scene.add` (and `VizSceneHandle.new` /
  `Visualizer.add`) accept `visible_in={view_ids}` so an entity is never
  constructed in panes outside that scope (default: all views).

## Breaking Changes
- **`SceneView(hide=…, show=…)` removed** — use `SceneView.set_visible(entity_id,
  visible)` at runtime, or pass `visible_in=` when adding the entity.

## Refactor
- **Docs/examples install path** — `install_docs.py` / `install_examples.py` /
  `install_info.py` now install the bundled docs/examples under
  `_dep-info/pytanga` (README and `.gitignore` updated accordingly).
