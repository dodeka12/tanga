# Phase 11 — Documentation update

**Status:** Done

## Goal

Document the new scene-graph features and APIs in the MkDocs viz guides.

## Files

- New: `docs/py/viz/scene-graph.md` (scene graph, transforms, `VizGroup`,
  `VizObjectRef`)
- Modify: `docs/py/viz/index.md` (add a topic row + example script entry)
- (optionally) `docs/py/viz/styles.md` and `docs/py/viz/animation.md` if the
  resolved-style / transform contents affect them

## Steps

### New guide `docs/py/viz/scene-graph.md`

- [x] Explain the node hierarchy (`VizNode`, `VizSceneObject`,
      `VizOverlayObject`, `VizGroup`) and transforms (`Transform` TRS +
      derived matrix).
- [x] Explain the layer split: scene nodes have a `Transform` and parent/child
      graph; overlay nodes have an `attach_to` reference (living in the
      screen/CSS plane) and no rotation/scale.
- [x] Document `VizObjectRef` and all its properties/methods:
  - [x] `entity`, `style`, `color`, `opacity`, `texture_label`
  - [x] `translate`, `rotate`, `scale_by`, `set_transform`, `transform(...)`
  - [x] `label_ids`, `labels`, `update_label`
  - [x] group `add`/`new`/`add_group`
- [x] Document `viz.new(...)` vs backward-compatible `viz.add(...)`.
- [x] Document `viz.add_group(...)` and attaching children.
- [x] Document the aspect-patch update model (`full` / `style` / `transform`)
      and why rotating a `VizGroup` (a `transform` aspect patch) is cheap.
- [x] Document the operator/entity transform affordances (`Rotor`,
      `GeneralRotor`, `Motor`, `Translator`, `Dilator`, `Point`, `Direction`).
- [x] Include a short, runnable snippet mirroring `py/examples/viz/demo_scene_graph.py`.

### Update `docs/py/viz/index.md`

- [x] Add a `[Scene Graph & Transforms](scene-graph.md)` row to the Topics
      table.
- [x] Add `demo_scene_graph.py` to the Example Scripts table (link following
      the existing GitHub blob URL convention).

### Consistency

- [x] Keep terminology consistent with the README/target docs (resolved style,
      `VizGroup`, `VizObjectRef`, `VizSceneObject`, `VizOverlayObject`,
      `parent_id`, `attach_to`, aspect patches).
- [x] Follow the existing MkDocs heading/table style.

## Verification

- [x] `uv run mkdocs build` (or the project's docs build task) succeeds.
- [x] `scene-graph.md` links in `index.md` resolve.
- [x] The documented snippet matches `demo_scene_graph.py` behavior.