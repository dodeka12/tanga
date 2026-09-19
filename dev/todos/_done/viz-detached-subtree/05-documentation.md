# Phase 5 — User documentation: composing detached scene subtrees

## Goal

A standalone doc page explaining the detached-composition pattern, the style
contract (partial styles incl. `texture_label` are backfilled from scene
defaults on insert), and the remaining limitations (ids auto-generated on
insert).

## Files

- New: `docs/py/viz/visualizer/composing-scenes.md`
- Edit: `docs/py/viz/visualizer/index.md` (nav) and/or the MkDocs nav
- Edit: `docs/py/viz/visualizer/scene-graph.md` (cross-link)

## Steps

- [x] **5.1 — Write `composing-scenes.md`**
  - Sections: motivation (scene-agnostic part libraries); building a `VizGroup`
    + `VizSceneObject` tree (with a texture-label style example); inserting via
    `viz.add`/`viz.new`; what becomes addressable after insert; how partial
    styles are backfilled from the scene's per-kind defaults.

- [x] **5.2 — Cross-link from `scene-graph.md`**
  - Add a short pointer in `docs/py/viz/visualizer/scene-graph.md` to the new page.

- [x] **5.3 — Register in nav**
  - Add the page to the MkDocs nav so it is reachable; verify with a strict build.

## Validation

`uv run mkdocs build --strict`

## Notes

- Keep it user-facing (no internal `_nodes`/`_ids` details beyond what a caller
  needs); developer details go in phase 7.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture. If this
work introduces or changes architecture, update the developer docs.
