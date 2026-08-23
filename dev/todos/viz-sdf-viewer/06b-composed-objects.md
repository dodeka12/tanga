# Phase 06b — Primitive object library + `Composed` objects

**Status:** Done

## Goal

Expose the Phase 1 SDF primitive library as **first-class, directly addable
objects**, and add a **`Composed`** drawable object that combines several
constituents into a single object with a per-constituent combine mode. This is
the "fundamental objects → composed drawables" layering:

- **Layer 1** — fundamental objects described directly by a distance function
  (`sphere`, `box`, `cylinder`, `torus`, …), each addable on its own.
- **Layer 2** — a `Composed` object that is a combination of Layer 1 objects
  (or entities/operators/other `Composed`), where **each constituent's combine
  mode** (`union` / `intersection` / `subtract`) is settable.

Before this phase, primitives existed only as an internal vocabulary: the six
analytic entities were hard-coded compositions, and there was no way to add a
raw cylinder/box or a "sphere with a cylinder removed" as one object.

## Files

- Modify: `py/pytanga/viz/sdf/primitives.py` (`SdfNode.combine` field,
  `group()`, named primitive constructors)
- New: `py/pytanga/viz/sdf/composed.py` (`Composed`)
- Modify: `py/pytanga/viz/sdf/serializer.py` (`_dispatch_object`,
  `_composed_tree`)
- Modify: `py/pytanga/viz/sdf/visualizer.py` (accept `SdfNode`/`Composed`)
- Modify: `py/pytanga/viz/sdf/__init__.py` (exports)
- Modify: `py/pytanga/viz/templates/sdf/objects/combinators.js` (`group` fold)
- Modify: `py/pytanga/viz/templates/sdf/objects/primitives.js` (new emitters)

## Data model

- `SdfNode` gains an optional `combine` field (`union`/`intersection`/
  `subtract`). It is meaningful only when the node is a child of a `group`
  node; `to_dict()` omits it when unset.
- `group(children)` builds `SdfNode(kind="group", children=[...])`, folded in
  order with each child's own `combine` (vs `combine(op, …)`, which applies one
  op to all children).
- `Composed(*parts)` — each part is a bare object (default `union`) or an
  `(object, combine_mode)` pair. `object` may be an entity, an operator, an
  `SdfNode`, or another `Composed` (nesting). It serializes to a single `group`
  node = **one** scene object with **one** material (color/opacity).

## Steps

- [x] `SdfNode.combine` field + serialization.
- [x] `group()` helper + a left-fold `group` emitter in `combinators.js`.
- [x] `Composed` dataclass with per-part combine validation.
- [x] `_dispatch_object` / `_composed_tree` in the serializer so `SdfNode` and
      `Composed` pass through without entity dispatch.
- [x] `SdfVisualizer.add` accepts `SdfNode`/`Composed` (short-circuit in
      `_resolve`).
- [x] Named primitive constructors (`sphere`, `box`, `cylinder`,
      `capped_cylinder`, `cone`, `capped_cone`, `torus`, `ellipsoid`,
      `round_box`, `capsule`, `segment`, `plane`).
- [x] `primitives.js` emitters for the primitives added in Phase 1 but not yet
      wired (`cone`, `cappedCone`, `ellipsoid`, `capsule`, `segment`, `plane`).

## Unit tests

- `py/tests/viz/sdf/test_composed.py` (new): group serialization, default
  union, nesting, invalid combine, single material, direct `SdfNode`
  serialization, `SdfVisualizer` integration.
- `py/tests/viz/sdf/test_primitives.py` (extended): `group()` + `combine`
  field, named primitive helpers.

## Verification

- [x] `uv run pytest py/tests/viz/sdf` passes.
- [x] Node smoke (`dev/src/sdf_composer_smoke.mjs`) emits a `group` fold and
      the new primitive emitters.
- [x] `uv run python py/examples/viz/demo_sdf_composed.py` runs (sphere with a
      cylinder removed via `Composed`).

## Reserved future seams (not implemented here)

- **UV mode** — a per-object surface parameterization for texture mapping will
  be an additive `SdfNode` field + a parallel `emitUv` emitter.
- **Signed displacement field** — a per-object distance modifier folded with
  `add`/`min`/`max` at the object-expression boundary, covering displacement
  maps and emboss/engrave glyph relief (the MSDF atlas is one such distance
  texture). The `group` emitter already returns a scalar distance at the object
  level, so an offset term can be appended there without touching tree internals.
- **Texture binding** — sampler uniforms join the `uMaterial` array later; the
  material table stays a single swappable module.
