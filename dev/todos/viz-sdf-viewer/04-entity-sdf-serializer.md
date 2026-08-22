# Phase 4 — Analytic entity → SDF primitive-tree mapping

**Status:** Planned

## Goal

Map the initially-supported geometry entities to compositions of the Phase 1
primitive/combinator library. This is the "base modules → entity" library: each
entity is expressed as a small SDF tree, serialized to a frontend-consumable
descriptor.

## Initial entity scope

Only these six geometric entities are implemented in this phase (others are
deferred):

- `Point`, `Line`, `Plane`, `Sphere`, `Circle`, `PointPair`

Operators, `Direction`, `Space`, and any other entity kinds are **out of scope**
for now; unsupported kinds raise a clear `TypeError` in the serializer rather
than silently dropping.

## Style scope (initially)

The serializer reads a small, per-kind subset of style values:

- `color` and `opacity` (all entity kinds).
- `size` — used only by `Point` (sphere radius).
- `thickness` — used by `Line` / `Circle` (and the `PointPair` connecting
  segment) as the cylinder/tube radius.

All other style flags (e.g. `wireframe`) are **ignored** for now and may be
honoured as additional style properties in a later phase.

## Files

- New: `py/pytanga/viz/sdf/primitives.py` (primitive/combinator descriptors)
- New: `py/pytanga/viz/sdf/serializer.py` (Entity → SDF tree)
- New: `py/pytanga/viz/templates/sdf/scene-builder.js` (SDF tree → GLSL
  expression + uniforms)
- New: `py/pytanga/viz/templates/sdf/objects/` (per-kind GLSL expression
  builders dispatching from `scene-builder.js`, mirroring the existing
  `renderers/` layout)

## Descriptor model (Python side)

A primitive node carries:
- `kind` (`"sphere"`, `"cappedCylinder"`, `"torus"`, `"slab"`, …) or
  combinator (`"union"`, `"intersect"`, …),
- `transform` (position / rotation / scale, to place the primitive in world
  space or clip it to a bound),
- typed parameters (radius, length, half-extents, …),
- optional `children` for combinators.

An entity object carries `style.color` / `style.opacity` (and the per-kind
`size`/`thickness`) plus a per-object **combine mode** (or `polarity`) prop —
`combine: "union" | "intersection" | "subtract"` (equivalently
`polarity: "positive" | "negative"`). This is emitted with the serialized tree
so the compositor (Phase 5) can fold negative objects correctly.

The tree serializes to a flat list with parent indices (or nested JSON) so the
JS side can emit the matching GLSL composition without any per-entity branching
beyond a `switch`-on-kind dispatcher, exactly like the existing `factory.js`.

## Entity → primitive mapping

| Entity | Shape (SDF primitive) | Style-driven parameters |
|--------|-----------------------|-------------------------|
| Point | small filled **sphere** | `radius = size` |
| Sphere | filled **sphere** | `radius = radius` (entity) |
| Line (finite) | **capped cylinder** along the direction | `radius = thickness` |
| Line (infinite) | `intersect(cappedCylinder(…), bound)` | `radius = thickness` |
| Circle | **torus** (a cylinder bent into a ring) | `tubeRadius = thickness` |
| Plane | `intersect(slab(point, normal, extent), bound)` | finite slab |
| PointPair | `union(sphere(A), sphere(B), cappedCylinder(A→B))` | point spheres (`size`), connecting segment (`thickness`) |

## Steps

- [ ] `primitives.py`: dataclasses for primitive/combinator descriptors and a
      `to_dict()` serializer.
- [ ] `serializer.py`: per-kind functions for the six supported entities above,
      each returning an SDF tree; handle infinite entities by adding an
      explicit `bound` region.
  - [ ] Map `Point`→sphere (`size`), `Line`→capped cylinder (`thickness`),
        `Circle`→torus (`thickness`), `Sphere`→filled sphere,
        `Plane`→bounded slab, `PointPair`→two spheres + connecting segment.
  - [ ] Read `color`/`opacity` plus the per-kind `size`/`thickness`; ignore
        `wireframe` and other flags.
  - [ ] Raise `TypeError` for unsupported kinds (operators, `Direction`,
        `Space`, …).
- [ ] `sdf/scene-builder.js` + `objects/*`:
  - [ ] `switch (obj.kind)` dispatcher that builds the GLSL `sd*`/`op*`
        expression string and collects its uniforms.
  - [ ] Uniform packing (primitive params + transform) with per-object stable
        uniform naming.
- [ ] `renderers`-style per-kind module split so adding an entity = one
      `objects/<kind>.js` + one serializer branch.

## Unit tests

Files: `py/tests/viz/sdf/test_primitives.py`, `py/tests/viz/sdf/test_serializer.py`

- [ ] `test_primitives_to_dict` — each primitive dataclass serializes to the
      expected `kind` + typed params + `transform`.
- [ ] `test_serialize_every_supported_kind` — `serializer.py` emits a valid
      tree for each of the six supported entities (structure + params asserted):
  - [ ] Point → sphere with `radius == size`
  - [ ] Line → capped cylinder with `radius == thickness`
  - [ ] Circle → torus with `tubeRadius == thickness`
  - [ ] Sphere → filled sphere with entity `radius`
  - [ ] PointPair → two spheres + connecting capped cylinder
  - [ ] Plane → bounded slab
- [ ] `test_serialize_infinite_bound` — infinite Line / Plane emit a non-empty
      `bound` region.
- [ ] `test_unsupported_kind_raises` — operators / `Direction` / `Space` raise
      `TypeError`.
- [ ] `test_style_scope` — `color`/`opacity` + `size`/`thickness` are
      forwarded on the relevant kinds; `wireframe` is ignored.
- [ ] `test_serialize_combine` — `combine`/`polarity` are forwarded to the
      emitted object.

## Verification

- [ ] `serializer.py` produces a valid SDF tree for every supported entity kind
      (unit test asserts structure/params).
- [ ] JS dispatcher emits compilable GLSL for a sphere + a line + a circle
      (manually concatenated into the Phase 2 raymarcher).
- [ ] Infinite line/plane serialize with a non-empty `bound`.
- [ ] `uv run pytest py/tests/viz/sdf/test_primitives.py py/tests/viz/sdf/test_serializer.py` passes.