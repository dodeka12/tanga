# Phase 4 — `Composed`/`SdfGroup` refactor + `viz.add()`/`new()` integration

## Goal

Make `Composed` and `SdfGroup` operate on `SdfElement`s (so members keep their
own style → per-object materials), and let `Visualizer.add()`/`new()` accept
`SdfObject`/`Combine`/`Composed`/`SdfGroup` directly. The serializer emits the
`materials` array (per-member color/opacity) from this phase on; the frontend
material table lands in Phase 5.

## Files

- Modify: `py/pytanga/viz/sdf/composed.py` — `SdfElement` members.
- Modify: `py/pytanga/viz/sdf/group.py` — `SdfElement` members (keep runtime
  transforms + id addressing).
- Modify: `py/pytanga/viz/sdf/serializer.py` — serialize `SdfObject`/`Combine`,
  and add `materials` to `Composed`/`SdfGroup`.
- Modify: `py/pytanga/viz/serializer.py` — detect `SdfObject`/`Combine` in
  `_dispatch_entity`.
- Modify: `py/pytanga/viz/visualizer.py` — `_resolve` pass-through for
  `SdfObject`/`Combine`.
- Modify: tests `test_sdf_group.py`, `test_composed.py`; new
  `test_sdf_object_serialization.py`.

## Steps

- [ ] **4.1 — `Composed` on `SdfElement`** (`composed.py`)
  - Parts normalize to `(SdfElement, ECompose)`: wrap raw entities/`SdfNode`
    via `_entity_to_sdf`; accept unary-tagged elements (`-el`, `~el`) and legacy
    `(obj, mode)` tuples + strings.
  - `Composed.id` stays; `Composed` inherits `SdfElement` (so it composes too).

- [ ] **4.2 — `SdfGroup` on `SdfElement`** (`group.py`)
  - Same member normalization as `Composed`, plus the existing runtime-transform
    machinery (`transforms`, `member_ids`, `_resolve_member_index`,
    `set_member_transform`, `on_change`). Members keep `id` addressing + Rotor→
    Euler rotation (from the shared `_types`).

- [ ] **4.3 — `viz.add()`/`new()` accept SDF elements** (`visualizer.py`,
    `serializer.py`)
  - `_resolve` passes `SdfObject`/`Combine` through.
  - `_dispatch_entity` routes `isinstance(entity, (SdfObject, Combine))` to the
    SDF serializer (before the per-kind leaf dispatch), regardless of a
    `SdfStyle` marker.

- [ ] **4.4 — Serialization** (`sdf/serializer.py`)
  - `SdfObject` → single `kind:"sdf"` object (tree = `to_sdf_node()`, color/
    opacity from `entity.style`, bound from the tree).
  - `Combine` → `kind:"sdf"`, `sdfKind:"Combine"`, nested `combine` tree; XOR →
    `xor` combinator.
  - `Composed`/`SdfGroup` → group object with `tree`, `materials` (one
    `{color, opacity}` per member, from each member's style), and (`SdfGroup`
    only) `members` + `bound`. Member `combine` modes come from the elements'
    `combine`.

- [ ] **4.5 — Backward compatibility**
  - `viz.add(Sphere(...), style=SdfStyle(...))` still emits `kind:"sdf"` (the
    marker path is untouched).
  - Legacy `Composed(sphere(1.0), (capped_cylinder(...), "subtract"))` and
    `SdfGroup(...)` positional/tuple forms keep working.

- [ ] **4.6 — Tests**
  - `SdfObject`/`Combine` via `viz.add()`/`new()` → `kind:"sdf"`.
  - `Composed`/`SdfGroup` emit a `materials` array matching member order, and
    per-member color/opacity comes from the member's style.
  - Operator-built `Combine` serializes to the expected nested tree.
  - Regression: marker path and fullscreen `SdfVisualizer` unchanged.

- [ ] **4.7 — Validate**
  - `uv run pytest py/tests/viz/ -q` + `py/tests/viz/sdf/ -q`.

## Validation

`uv run pytest py/tests/viz/ -q` (existing + new green).

## Notes

- The `materials` array is emitted now but ignored by the frontend until Phase 5
  (which switches the group proxy to `vec2 map()` + the material table). Until
  then, a multi-member object still renders with a single color (first material)
  so no intermediate regression.
- `SdfGroup.set_member_transform`/`update_sdf_group_member`/`VizObjectRef.
  set_member_transform` are unchanged (they already accept `int | str` + `Vec3`/
  `TransformRotation`/`Triple`).
