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

- Only **`color`** and **`opacity`** are read from the entity styles and
  forwarded to the SDF object.
- All other style flags (e.g. `wireframe`, `size`, `thickness`, `extent`, …)
  are **ignored** for now. They may be honoured as additional style properties
  in a later phase, but are not implemented here.

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
- `kind` (`"sphere"`, `"segment"`, `"torus"`, `"slab"`, …) or combinator
  (`"union"`, `"intersect"`, …),
- `transform` (position / rotation / scale, to place the primitive in world
  space or clip it to a bound),
- typed parameters (radius, length, half-extents, …),
- optional `children` for combinators.

An entity object carries `style.color` (and optionally `style.opacity`) plus a
per-object **combine mode** (or `polarity`) prop — `combine: "union" |
"intersection" | "subtract"` (equivalently `polarity: "positive" | "negative"`).
This is emitted with the serialized tree so the compositor (Phase 5) can fold
negative objects correctly.

The tree serializes to a flat list with parent indices (or nested JSON) so the
JS side can emit the matching GLSL composition without any per-entity branching
beyond a `switch`-on-kind dispatcher, exactly like the existing `factory.js`.

## Entity → primitive mapping

| Entity | Composition |
|--------|-------------|
| Point | `sphere(center, size)` |
| Line (finite) | `segment(origin, origin+dir*length, thickness)` |
| Line (infinite) | `intersect(cappedCylinder(origin,dir,extent,thickness), bound)` |
| Plane | `intersect(slab(point,normal,extent), bound)` (finite slab) |
| Sphere | `sphere(center, radius)` |
| Circle | `torus(center, normal, radius, tubeRadius)` |
| PointPair | `union(sphere(A), sphere(B))` (segment for the connecting line) |

## Steps

- [ ] `primitives.py`: dataclasses for primitive/combinator descriptors and a
      `to_dict()` serializer.
- [ ] `serializer.py`: per-kind functions for the six supported entities above,
      each returning an SDF tree; handle infinite entities by adding an
      explicit `bound` region.
  - [ ] Read only `color`/`opacity` from the style; ignore `wireframe`/sizing
        flags.
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
      tree for each of the six supported entities (structure + params asserted).
- [ ] `test_serialize_infinite_bound` — infinite Line / Plane emit a non-empty
      `bound` region.
- [ ] `test_unsupported_kind_raises` — operators / `Direction` / `Space` raise
      `TypeError`.
- [ ] `test_style_scope` — only `color`/`opacity` are forwarded; `wireframe`
      and other flags are ignored.
- [ ] `test_serialize_combine` — `combine`/`polarity` are forwarded to the
      emitted object.

## Verification

- [ ] `serializer.py` produces a valid SDF tree for every supported entity kind
      (unit test asserts structure/params).
- [ ] JS dispatcher emits compilable GLSL for a sphere + a line (manually
      concatenated into the Phase 2 raymarcher).
- [ ] Infinite line/plane serialize with a non-empty `bound`.
- [ ] `uv run pytest py/tests/viz/sdf/test_primitives.py py/tests/viz/sdf/test_serializer.py` passes.