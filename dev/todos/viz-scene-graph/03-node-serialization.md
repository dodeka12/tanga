# Phase 3 — Node serialization

**Status:** Planned

## Goal

Move the serialization logic out of `serializer.py`'s large `isinstance`
dispatch and into `VizObject.serialize()` (per-kind methods). The existing leaf
field layout (`position`, `center`, `normal`, `radius`, `style:{...}`) must
remain stable so the frontend renderers keep working without changes.

## Files

- Modify: `py/pytanga/viz/_nodes.py` (add per-kind `serialize()`)
- Modify: `py/pytanga/viz/serializer.py` (remove dispatch, keep helpers)
- Modify: `py/pytanga/viz/scene.py` (call node `serialize()` in flush/full_state)

## Steps

- [ ] Add a `serialize()` base contract on `VizNode` returning a dict with
      `id`, `layer`, `kind`, `parent_id`, `transform`, `visible`.
- [ ] Migrate each `_serialize_*` function body from `serializer.py` into a
      `VizObject` subclass or a per-kind `_serialize_<kind>()` method:
  - [ ] `Point`, `Direction`, `HPoint`
  - [ ] `PointPair` (incl. `ImagPointPair`)
  - [ ] `Line`, `Plane`
  - [ ] `Circle` (incl. `ImagCircle`), `Sphere` (incl. `ImagSphere`), `Space`
  - [ ] `PointPath`
  - [ ] `Axis`, `Axes2D`, `Axes3D`, `Grid`
  - [ ] Operators: `ReflectionLine`, `ReflectionPlane`, `ReflectionPoint`
        (`ReflectionOrigin`), `Inversion`, `Rotor`, `Translator`, `Dilator`,
        `Motor`, `GeneralRotor`
- [ ] Reuse `_apply_defaults` / `_style_to_output` / `_style_for_kind` as the
      canonical-style source when building the resolved style at node creation
      time (Phase 2), not at serialization time.
- [ ] Implement `VizObject.serialize()`:
  - [ ] Start from `VizNode.serialize()` base dict.
  - [ ] Add geometry fields (same keys as before).
  - [ ] Add the resolved `style` via `style.to_dict()` merged into the node's
        explicit color/opacity overrides (mirror current `_apply_defaults`
        effective output).
- [ ] Delete the `isinstance`/`elif` dispatch in `serializer.serialize_entity`;
      keep `serialize_scene_update`, `_serialize_label`, and shared helpers
      still referenced elsewhere.
- [ ] Update `Scene.flush()` / `Scene.full_state()` to walk the node tree in
      DFS pre-order and call `node.serialize()`, preserving `removed` handling
      and interaction injection.
- [ ] Confirm `export`, `_animation_recording`, `_figure_html`, and
      `display_static` continue to read from `Scene.full_state()` unchanged.

## Unit tests

File: `py/tests/viz/test_serializer.py` (extend) and/or a new
`py/tests/viz/test_node_serialization.py`.

- [ ] `test_point_serialize` — point node output matches previous leaf layout
      plus `parent_id`/`transform`.
- [ ] `test_representative_kinds_serialize` — parametrized over
      `Point` / `Line` / `Plane` / `Sphere` / `Circle` / `PointPair` /
      `PointPath` / `Grid` / `Axis` / operators.
- [ ] `test_resolved_style_present` — serialized `style` dict is the fully
      resolved merged style.
- [ ] `test_imaginary_variants` — `ImagPointPair` / `ImagCircle` / `ImagSphere`.
- [ ] `test_full_state_equiv` — `Scene.full_state()` matches the prior
      `serialize_entity` output modulo the added keys.
- [ ] `test_removed_tracking` — add/update/remove cycles report correct ids.
- [ ] `test_group_serialize_shape` — `VizGroup` serializes with
      `kind == "VizGroup"`.

## Verification

- [ ] `uv run pytest py/tests/viz/test_serializer.py py/tests/viz/test_node_serialization.py` passes.
- [ ] `Scene.full_state()` output is byte-for-byte equivalent (modulo
      intentionally added `parent_id`/`transform` keys) to the previous
      `serialize_entity` output for a set of representative entities/operators.
- [ ] `removed` tracking still works across add/update/remove cycles.
- [ ] No `Unknown entity type` regression for all supported kinds.
- [ ] Existing viz smoke/export tests pass.
