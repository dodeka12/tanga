# Viz Scene-Graph Refactor — Current State Summary

> Handoff notes for continuing work on another machine. Branch: `feat/viz-objects`.

## Task & Governing Instruction

Implement the viz-scene-graph plan phase by phase, step by step. After a step is implemented
successfully and tests pass, mark it complete in the plan, then create a commit, then continue
with the next step/phase. If an ambiguous formulation arises and it's unclear how to proceed,
stop and ask instead of guessing.

## Completed Phases

- **Phase 1 — Transform math** (`_transforms.py` + tests): DONE, committed.
- **Phase 2 — Style defaults holder** (`VizStyleDefaults`): DONE, committed
  (`90aaca9`, then `b7168a0` marking the phase complete).
- **Phase 3 — Node hierarchy** (`_nodes.py` + Scene integration): DONE, committed (`bc9c238`).

All tests pass (308 in `py/tests/viz`); ruff is clean on new/modified files. The pre-existing
13 errors in `visualizer.py` (E402 imports and F821 `TextureLabelStyle`/`ActPointStyle`) are
left unchanged; the `make_defaults` import is local to avoid adding a new lint error.

## Plan Files (`dev/todos/viz-scene-graph/`)

- `01-transform-math.md` — Done
- `02-style-defaults.md` — Done
- `03-node-hierarchy.md` — Done
- `04-node-serialization.md` — Planned (NEXT)
- `05-object-ref.md` — Planned
- `06-entry-points.md` — Planned
- `07-frontend-scene-graph.md` — Planned
- `08-export-static.md` — Planned
- `09-end-to-end.md` — Planned
- `10-example.md` — Planned
- `11-docs.md` — Planned
- `12-changelog.md` — Planned
- `README.md`

## Key Technical Concepts

- **Layer split**: `VizSceneObject` (scene layer, has `Transform` + parent/child graph) vs
  `VizOverlayObject` (overlay layer, has `position` + `attach_to`, no `Transform`);
  `VizGroup` is a `VizSceneObject` with `kind="VizGroup"`, no entity/style.
- **Aspect-dirty tracking**: each `VizNode` keeps `_dirty_aspects` set of
  `{"full"}`/`{"style"}`/`{"transform"}`; `mark(kind)` (full clears others),
  `consume_dirty()`, `dirty_for(aspect)`.
- **Resolved style at creation**: `Scene._make_scene_node` uses
  `_style_to_output(props.get("style"), kind, styles_map=self.default_styles)` then overlays
  `props["color"]`/`props["opacity"]` → the node's `.style` is a resolved dict (dict-backed).
- **Style defaults snapshot**: `VizStyleDefaults` bundles `default_styles` (a `_StyleDict`),
  `default_label_style`, `default_label_styles`, `default_annotation_style`,
  `default_tex_label_style`, `default_tex_label_styles`; `make_defaults()` from `_style_dict`
  factories; `copy()` via `copy.deepcopy`. `ActPointStyle`, figure style, anim style are NOT
  bundled. Snapshots are deep-copied per Scene (via the Visualizer's `_style_defaults.copy()`);
  resolution still reads the Visualizer's `_default_*` properties until Phase 4.
- **Transform conventions**: TRS position + Euler `"XYZ"` rotation + scale; `matrix()` =
  `T @ Rx@Ry@Rz @ S` (column-vector); `scale_by` avoids clashing with `.scale` field;
  `set_matrix`/`from_matrix` via `_transforms.to_trs`; `apply_matrix(m, space="local"|"world")`.
- **Style merge helpers** in `_nodes.py`: `_merge_style_into` (instance/dict aware, non-None),
  `_assign_style_field` (dict/instance aware copy-then-set), plus `_merge_style` re-exported
  from `_style_dict`.
- **Wire shape (Phase 4 onward)**: scene node
  `{id, layer, kind, parent_id, transform:{position,rotation,scale}, visible, ...geometry..., style:{...}}`;
  overlay `{id, layer:"overlay", kind:"label", position, attach_to, visible, text, style}`;
  patch messages `{type:"object_update", scene, patches:[{id, aspect, value}], removed}`.
- **Commit conventions**: `docs(viz): ...` for plan/status edits, `feat(viz): ...` for
  implementation; changelog via `dev/workflows/changelog.md` (`YYYY-MM-DD_<short-hash>.md`,
  "Changes since version <last-public-release>", sections New Features/Breaking/Bug Fixes/Refactor).
- **ruff config**: `unfixable=["F401"]`.

## Relevant Files & Code

- `py/pytanga/viz/_transforms.py` (existing, Phase 1): `translation_matrix`, `rotation_matrix`,
  `scale_matrix`, `to_trs`, `translator_to_matrix`, `rotor_to_matrix`, `general_rotor_to_matrix`,
  `motor_to_matrix`, `dilator_to_matrix`, `operator_to_matrix`, `operator_to_trs`, `to_matrix`,
  `to_trs_tuple`. Rotation order `"XYZ"`.
- `py/pytanga/viz/_style_defaults.py` (new): `VizStyleDefaults` dataclass + `make_defaults()`.
- `py/pytanga/viz/visualizer.py` (modified): `self._style_defaults = make_defaults()` (local
  import); `Scene(..., style_defaults=self._style_defaults.copy())` in `__init__` and `scene()`;
  `_default_*` backing properties forwarding to `self._style_defaults`; public `default_styles`
  returns `_StyleDict(self._default_styles)`; `default_label_style.setter` writes
  `self._style_defaults.default_label_style`.
- `py/pytanga/viz/scene.py` (modified): `Scene.__init__(config=None, *, name="", style_defaults=None)`
  stores `self.style_defaults`; `self._nodes = {}`; `add_object` also calls `self._make_node(obj)`;
  `get_node`, `add_node`, `add_group(name=None) -> VizGroup`, `group_ids`, `_dfs_preorder`;
  `remove`/`clear`/`flush` handle `_nodes`. Accessor properties `default_styles` etc.
  - `_make_scene_node(obj)`: resolves style via
    `_style_to_output(props.get("style"), kind, styles_map=self.default_styles)` then overlays
    color/opacity; returns `VizSceneObject(obj.id, obj.data, merged, name=obj.kind, kind=kind)`.
  - `_make_overlay_node(obj)`: label → `VizOverlayObject(id, kind="label",
    style=label.style or default_label_style, position=label.position, attach_to=label.parent_id,
    payload=label.text)`; else dict-based annotation/title.
  - `remove`: `if object_id in self._objects or object_id in self._nodes:
    self._removed_ids.append(...)`; `clear` iterates both; `flush` pops both `_objects` and `_nodes`.
- `py/pytanga/viz/_nodes.py` (new): full node classes; `Transform`, `VizNode`,
  `VizSceneObject`, `VizOverlayObject`, `VizGroup` (all setters aspect-correct).
- `py/tests/viz/test_style_defaults.py` (new): 5 tests.
- `py/tests/viz/test_nodes.py` (new): 24 tests (Transform, aspects, parenting, overlay, group,
  Scene integration).
- Existing context modules (not modified in this window): `serializer.py` (907 lines;
  `serialize_entity` dispatch, `_apply_defaults`, `_serialize_<kind>` leaf helpers,
  `_serialize_label`), `_styles/__init__.py` (`_DEFAULT_STYLE_FOR_KIND`, `_style_to_output`,
  `_style_for_kind`), `_style_dict.py` (`_StyleDict`, `_merge_style`, `_make_default_*`,
  `_resolve_*`), `_props.py` (`_normalize_color`, `_extract_non_none`), `_label.py` (`Label`
  dataclass: text/position/parent_id/style), `_types.py`, `_scene_handle.py`, `__init__.py`
  (exports).

## Next Steps — Phase 4 (Node serialization / aspect patches)

Per `dev/todos/viz-scene-graph/04-node-serialization.md`:

- Move serialization dispatch into `VizNode.serialize()` / `VizSceneObject.serialize()` /
  `VizOverlayObject.serialize()` / `VizGroup.serialize()` (add `parent_id`, `transform`,
  geometry fields, resolved `style`; reuse per-kind `_serialize_<kind>` helpers from `serializer.py`).
- Add `VizNode.patch(aspect)` returning `full`/`style`/`transform` patch dicts.
- `Scene.flush()` walks DFS pre-order collecting patches via `consume_dirty()` and returns
  `(patches, removed)`; add `serialize_object_update(patches, removed)` in `serializer.py`;
  keep `serialize_scene_update` and the `SceneObject`/`scene_update` backward-compat path.
- `visualizer.py` `_flush_scene_async` pushes patches via a new push path or `push_raw`.
- Unit tests: extend `py/tests/viz/test_serializer.py` + new
  `py/tests/viz/test_node_serialization.py` (point serialize, representative kinds, resolved
  style, imaginary variants, aspect full/style/transform patches, overlay label patch,
  full_state equivalence, removed tracking, group serialize shape).
- Then commit, mark Phase 4 done, and continue to Phase 5 (`VizObjectRef`), Phase 6 (entry
  points), Phase 7 (frontend), Phases 8–12.