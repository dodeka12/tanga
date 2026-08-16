# Phase 14 — Unify live/export render pipeline

**Status:** Planned

## Goal

Make the live viewer and the static/animated HTML export construct the
three.js scene through **one code path**, so a change to the render pipeline
is made once and the export is guaranteed to match the live view.

The per-entity renderers are already shared; this phase extracts the remaining
duplicated *glue* — scene-object construction (transform + parenting) and
overlay/label creation — into shared JS modules, and unifies the wire format
onto `objects` / `attach_to`.

## Current state

**Already shared (single source of truth):** `templates/renderers/*.js`
(`createEntityMesh`, `updateEntityMesh`, per-kind renderers). The export
bundles them via `_RENDERER_FILES` in `export/_bootstrap/_html.py`
(`generate_bootstrap_js` strips `import`/`export` and concatenates them).

**Duplicated glue (the problem):**

| Concern | Live viewer | Export |
|---|---|---|
| Entity → node (transform wrap + `parent_id`) | `viewer.js upsertObject` | `_bootstrap/_entities.py js_entity_creation` |
| Overlay/label (parenting + offset/align) | `upsertObject` overlay branch (`attach_to`) | `js_label_creation_static`/`js_label_creation` (`parentId`) |
| Camera autofit | `view_mode.js fitCamera` | `_bootstrap/_scene.py js_autofit_camera` |
| Scene setup / render loop / resize | `viewer.js` + `view_mode.js` | `_bootstrap/_scene.py` |

**Wire-format split:** live = unified `objects` (`layer`/`parent_id`/
`attach_to`); export = split `entities` (`full_state()`) + `labels`
(`_serialize_labels()`, legacy `parentId`).

## Scope & decision (Option A)

Unify the **scene-graph construction** (the geometry-correctness path). The
interactive session (WebSocket, controls, interaction, tweens) and the
animated playback engine stay context-specific — they are not "rendering".

Camera fit / scene setup / render loop unification (Option C) is a possible
follow-up, not in this phase.

## Steps

### 1. New shared module `templates/scene-builder.js`

- [ ] Move `wrapWithNodeTransform` / `isIdentityTransform` /
      `applyTransformToObject` out of `viewer.js` (exported).
- [ ] `buildSceneObject(obj, scene, registry)`:
      `createEntityMesh(obj)` → `wrapWithNodeTransform(mesh, obj.transform)` →
      parent under `registry.get(obj.parent_id)?.obj` or `scene` →
      `registry.set(obj.id, {obj, mesh, data:{...obj}, layer:'scene'})`.
- [ ] `buildOverlay(obj, scene, registry)`:
      dispatch `label` (CSS2DObject + `attach_to` parenting + offset/align),
      `annotation`, `title`; use `obj.attach_to ?? obj.parentId`.
- [ ] `removeObject(id, registry, scene)`: unified disposal (scene →
      `removeEntityMesh`; overlay → `removeFromParent`/`element.remove`/
      `el.remove`).

### 2. `viewer.js` delegates to the module

- [ ] `upsertObject` scene branch → `buildSceneObject`; overlay branch →
      `buildOverlay`.
- [ ] `removeSceneObject` → `removeObject`.
- [ ] Delete the moved local helpers.

### 3. Export bootstrap delegates to the module

- [ ] Add `scene-builder.js` to `_RENDERER_FILES`.
- [ ] Replace `js_entity_creation` + `js_label_creation_static` bodies with a
      thin loop calling `buildSceneObject`/`buildOverlay` over one `objects`
      array.
- [ ] `render_export_html`/`render_export_figure`: embed `objects` JSON only
      (drop the separate `labels` array).

### 4. Unify the wire format

- [ ] Export consumes `Scene.full_state()` (already unified `objects`).
- [ ] Remove `Scene._serialize_labels()` + the `parentId` label path if no
      other caller remains (check `visualizer.py`).
- [ ] Update `test_export_static.py`/`test_export_renderers.py` expectations.

### 5. Animated export

- [ ] Ensure its initial hierarchy also uses `buildSceneObject`/`buildOverlay`
      (it already reuses `createEntityMesh`/`updateEntityMesh`).

### 6. Changelog

- [ ] Add a changelog entry per `dev/workflows/changelog.md`.

## Unit / smoke tests

- [ ] `node --check` on `scene-builder.js` and existing templates.
- [ ] `uv run pytest py/tests/viz -q`.
- [ ] Export a `VizGroup` + non-identity transform + `attach_to` label; diff
      visually against the live viewer (must be identical).

## Verification

- [ ] Export and live view render identically for the same scene.
- [ ] `js_entity_creation`/`js_label_creation_static` no longer contain
      transform/parenting logic (delegate to `scene-builder.js`).
- [ ] No `_serialize_labels`/`parentId` usage remains in the export path.
- [ ] All viz tests pass.

## Alternatives (why not)

- **Option B — export reuses `viewer.js` in "static mode":** requires
  separating the WebSocket/controls/interaction/tween session from the
  renderer core; large and risky, no rendering benefit over Option A.
  Deferred.
- **Do nothing:** export already renders correctly today; this phase removes a
  maintenance hazard (two places to edit geometry), not a visible bug.
