# Phase 3 — Wire `add_viz` `VizGroup` branch + integration tests

## Goal

Make `viz.add(group)` / `viz.new(group)` register the whole detached subtree,
and prove the end-to-end behaviour (render + addressability + style/tex-label
preservation).

## Files

- Edit: `py/pytanga/viz/scene.py`
- Edit: `py/tests/viz/test_scene_graph_e2e.py` (or a new subtree test file)

## Steps

- [x] **3.1 — Replace `add_node` with `add_subtree` in the `VizGroup` branch**
  - In `Scene.add_viz`'s `isinstance(obj, VizGroup)` branch, call
    `self.add_subtree(obj, object_id=gid)` instead of `self.add_node(obj,
    object_id=gid)`; keep the `parent_id` re-parenting.

- [x] **3.2 — End-to-end test: detached tree round-trip + backfill**
  - Build `VizGroup` + children (one child with a **partial** style, one with
    `SphereStyle(texture_label=TextureLabelStyle(text="S₁", ...))`),
    `viz.new(group)` → `flush()` → `full_state()` lists root before children
    with correct `parent_id`; the partial-style child has the scene's canonical
    per-kind defaults merged in, and the texture label is present in the styled
    child's `style`.

- [x] **3.3 — Addressability test**
  - `get_node(child_id)`; `update(child_id, opacity=0.5)`; `update_entity(child_id,
    Sphere(...))`; `set_interaction(child_id, cfg)` then `remove(child_id)`.

- [x] **3.4 — Regression: existing `viz.add_group` + re-parent flow unchanged**
  - Confirm `viz.add_group` / `grp.new(...)` / `.parent=` still behave (they
    already register via `add`), so no other path regresses.

## Validation

`uv run pytest py/tests/viz/test_scene_graph_e2e.py py/tests/viz/test_nodes.py -q`

## Notes

- `Scene.add_viz`'s `VizGroup` branch already assigns `gid`; keep that, and let
  `add_subtree` handle descendant registration.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture. If this
work introduces or changes architecture, update the developer docs.
