# Phase 10 — Documentation update

**Status:** Planned

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

- [ ] Explain the node hierarchy (`VizNode`, `VizSceneObject`,
      `VizOverlayObject`, `VizGroup`) and transforms (`Transform` TRS +
      derived matrix).
- [ ] Explain the layer split: scene nodes have a `Transform` and parent/child
      graph; overlay nodes have an `attach_to` reference (living in the
      screen/CSS plane) and no rotation/scale.
- [ ] Document `VizObjectRef` and all its properties/methods:
  - [ ] `entity`, `style`, `color`, `opacity`, `texture_label`
  - [ ] `translate`, `rotate`, `scale_by`, `set_transform`, `transform(...)`
  - [ ] `label_ids`, `labels`, `update_label`
  - [ ] group `add`/`new`/`add_group`
- [ ] Document `viz.new(...)` vs backward-compatible `viz.add(...)`.
- [ ] Document `viz.add_group(...)` and attaching children.
- [ ] Document the aspect-patch update model (`full` / `style` / `transform`)
      and why rotating a `VizGroup` (a `transform` aspect patch) is cheap.
- [ ] Document the operator/entity transform affordances (`Rotor`,
      `GeneralRotor`, `Motor`, `Translator`, `Dilator`, `Point`, `Direction`).
- [ ] Include a short, runnable snippet mirroring `py/examples/viz/demo_scene_graph.py`.

### Update `docs/py/viz/index.md`

- [ ] Add a `[Scene Graph & Transforms](scene-graph.md)` row to the Topics
      table.
- [ ] Add `demo_scene_graph.py` to the Example Scripts table (link following
      the existing GitHub blob URL convention).

### Consistency

- [ ] Keep terminology consistent with the README/target docs (resolved style,
      `VizGroup`, `VizObjectRef`, `VizSceneObject`, `VizOverlayObject`,
      `parent_id`, `attach_to`, aspect patches).
- [ ] Follow the existing MkDocs heading/table style.

## Verification

- [ ] `uv run mkdocs build` (or the project's docs build task) succeeds.
- [ ] `scene-graph.md` links in `index.md` resolve.
- [ ] The documented snippet matches `demo_scene_graph.py` behavior.