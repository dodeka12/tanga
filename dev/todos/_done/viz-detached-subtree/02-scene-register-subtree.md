# Phase 2 — `Scene.add_subtree` + node-first update

## Goal

Register a pre-built `VizSceneObject` tree (root + descendants) into the scene
so every descendant is individually addressable, backfill each node's partial
style from the scene defaults, and make `update`/`update_entity` work for
node-only entries.

## Files

- Edit: `py/pytanga/viz/scene.py`
- Edit: `py/tests/viz/test_nodes.py` (or new `py/tests/viz/test_scene_subtree.py`)

## Steps

- [x] **2.1 — `Scene.add_subtree(root, *, object_id=None) -> str`**
  - DFS pre-order with a visited set; per node: `node.id = node.id or
    generate_id()`; register `_nodes[id]` (raise `ValueError` on id collision
    with a different node); append only the root to `_order` if absent; return
    root id.  Skip non-`VizSceneObject` nodes (none expected in a scene subtree).

- [x] **2.2 — Backfill partial styles per descendant**
  - For each scene node, resolve `node.style` against the scene's per-kind
    defaults via `_style_to_output(node.style, node.kind,
    styles_map=self.styles.kind)` (reusing `_make_scene_node`'s merge incl.
    top-level `color`/`opacity`); set `node.style` to the result and
    `node._styles_map = self.styles.kind`.  A `style=None` node gets the full
    canonical defaults.

- [x] **2.3 — Node-first `Scene.update`**
  - When `object_id` is in `_objects`, keep existing behaviour; otherwise look
    up `_nodes.get(object_id)`, and if it is a `VizSceneObject`, call
    `node.apply_props(dict(properties))` (and skip `_objects` bookkeeping).

- [x] **2.4 — Node-first `Scene.update_entity`**
  - Same fallback: if the id is only in `_nodes`, call `node.set_entity(entity)`;
    otherwise keep the `_objects` path.

- [x] **2.5 — Verify `remove` / `set_interaction` on node-only entries**
  - Confirm `remove(child_id)` and `set_interaction(child_id, cfg)` behave for a
    child registered only in `_nodes` (they already tolerate `_objects` absence);
    add a regression test.

- [x] **2.6 — Tests**
  - `add_subtree` registers root + descendants; a child with a partial style
    gets backfilled to the canonical per-kind defaults; `get_node(child_id)`
    works; `update(child_id, color=...)` and `update_entity(child_id, ...)`
    work; `remove(child_id)` removes only that child; id collision raises.

## Validation

`uv run pytest py/tests/viz/test_nodes.py -q && uv run ruff check py/pytanga/viz/scene.py py/tests/viz/test_nodes.py`

## Notes

- Do **not** add descendants to `_order`; `_dfs_preorder` reaches them through
  `parent.children`, and `_order` must only list true top-level nodes.
- Reuse `_make_scene_node`'s style-merge logic (or extract a shared helper) so
  backfill stays identical to the `viz.add` path.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture. If this
work introduces or changes architecture, update the developer docs.
