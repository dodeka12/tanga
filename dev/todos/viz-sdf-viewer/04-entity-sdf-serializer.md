# Phase 4 — Analytic entity → SDF primitive-tree mapping

**Status:** Planned

## Goal

Map each standard geometry entity and operator dataclass to a composition of
the Phase 1 primitive/combinator library. This is the "base modules → entity"
library: each entity is expressed as a small SDF tree, serialized to a
frontend-consumable descriptor.

## Files

- New: `py/pytanga/viz/sdf/primitives.py` (primitive/combinator descriptors)
- New: `py/pytanga/viz/sdf/serializer.py` (Entity/Operator → SDF tree)
- New: `py/pytanga/viz/templates/sdf/scene-builder.js` (SDF tree → GLSL
  expression + uniforms)
- New: `py/pytanga/viz/templates/sdf/objects/` (per-kind GLSL expression
  builders dispatching from `scene-builder.js`, mirroring the existing
  `renderers/` layout)

## Descriptor model (Python side)

A primitive node carries:
- `kind` (`"sphere"`, `"box"`, `"cylinder"`, `"cone"`, `"torus"`, `"segment"`,
  …) or combinator (`"union"`, `"subtract"`, `"intersect"`, `"smooth_union"`,
  …),
- `transform` (position / rotation / scale, to place the primitive in world
  space or clip it to a bound),
- typed parameters (radius, half-extents, length, angle, …),
- optional `children` for combinators.

An entity object also carries a per-object **combine mode** (or `polarity`)
prop — `combine: "union" | "intersection" | "subtract"` (equivalently
`polarity: "positive" | "negative"`). This is emitted with the serialized tree
so the compositor (Phase 5) can fold negative objects correctly.

The tree serializes to a flat list with parent indices (or nested JSON) so the
JS side can emit the matching GLSL composition without any per-entity branching
beyond a `switch`-on-kind dispatcher, exactly like the existing `factory.js`.

## Entity → primitive mapping

| Entity | Composition |
|--------|-------------|
| Point | `sphere(center, size)` |
| Direction | `union(cylinder(origin→tip), cone(tip))` (arrow: shaft + head) |
| Line (finite) | `segment(origin, origin+dir*length, thickness)` |
| Line (infinite) | `intersect(cappedCylinder(origin,dir,extent,thickness), bound)` |
| Plane | `intersect(slab(point,normal,extent), bound)` (finite slab) |
| Circle | `torus(center, normal, radius, tubeRadius)` |
| Sphere | `sphere(center, radius)` |
| PointPair | `union(sphere(A), sphere(B))` (segment for the connecting line) |
| Space | `box(extent)` (bounding region glyph) |

Operator glyphs (Phase 4 initial set, refine in later phases):
- Rotor → arc/partial torus (`arc(axis, angle, discRadius)`);
- Translator → arrow (`union(cylinder, cone)`);
- Dilator → concentric rings (`torus` rings around origin);
- Inversion → `sphere(center, radius)` outline;
- ReflectionLine/Plane/Point → the corresponding entity glyph.

## Steps

- [ ] `primitives.py`: dataclasses for primitive/combinator descriptors and a
      `to_dict()` serializer.
- [ ] `serializer.py`: per-kind functions for the entity/operator table above,
      each returning an SDF tree; handle infinite entities by adding an
      explicit `bound` region.
- [ ] `sdf/scene-builder.js` + `objects/*`:
  - [ ] `switch (obj.kind)` dispatcher that builds the GLSL `sd*`/`op*`
        expression string and collects its uniforms.
  - [ ] Uniform packing (primitive params + transform) with per-object stable
        uniform naming.
- [ ] `renderers`-style per-kind module split so adding an entity = one
      `objects/<kind>.js` + one serializer branch.

## Verification

- [ ] `serializer.py` produces a valid SDF tree for every supported entity and
      operator kind (unit test asserts structure/params).
- [ ] JS dispatcher emits compilable GLSL for a sphere + a direction arrow
      (manually concatenated into the Phase 2 raymarcher).
- [ ] Infinite line/plane serialize with a non-empty `bound`.