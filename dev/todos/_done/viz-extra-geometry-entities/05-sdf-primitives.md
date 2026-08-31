# Phase 5 — New SDF primitives (`partialDisk`, `regularPolygon`)

## Goal

Add two new SDF primitives so `PartialDisk` and `RegularPolygon` can be rendered
as SDF solids. `Disk`/`Box`/`Ellipsoid`/`Ellipse` reuse existing primitives and
need nothing here. This phase is purely additive.

## Files

- Modify: `py/pytanga/viz/templates/sdf/shaders/primitives.glsl`
- Modify: `py/pytanga/viz/templates/sdf/objects/primitives.js`
- Modify: `py/pytanga/viz/sdf/primitives.py`
- Modify: `py/pytanga/viz/sdf/__init__.py`
- Modify: `py/tests/viz/sdf/test_primitives.py`

## Steps

- [x] **5.1 — GLSL `sdPartialDisk` (`primitives.glsl`)**
  - A capped sector: a slab of half-height `h`, radius `r`, swept over `angle`
    radians starting at the local `+X` axis, in the XZ plane (Y up), matching the
    existing axis conventions. Combine the IQ `sdPie` angular clip with
    `abs(p.y) - h`:
    ```glsl
    float sdPartialDisk(vec3 p, float h, float r, float angle) {
        vec2 c = vec2(sin(0.5 * angle), cos(0.5 * angle));
        p.x = abs(p.x);
        float l = length(p.xz) - r;
        float m = length(p.xz - c * clamp(dot(p.xz, c), 0.0, r));
        float pie = max(l, sign(c.y * p.x - c.x * p.z) * m);
        return max(abs(p.y) - h, pie);
    }
    ```
  - (Adjust the angular form to the canonical IQ `sdArc`/`sdPie` if needed; the
    key requirement is a correct bounded pie slab in XZ.)

- [x] **5.2 — GLSL `sdRegularPolygon` (`primitives.glsl`)**
  - IQ `sdRegularPolygon` (2D, radius `r`, `n` sides) extruded into a slab of
    half-height `h`:
    ```glsl
    float sdRegularPolygon(vec3 p, float h, float r, float n) {
        float an = 3.141592653589793 / n;
        vec2 acs = vec2(cos(an), sin(an));
        vec2 q = abs(p.xz);
        float bn = mod(atan(q.y, q.x), 2.0 * an) - an;
        q = length(q) * vec2(cos(bn), abs(sin(bn)));
        q -= r * acs;
        q.y += clamp(-q.y, 0.0, r * acs.y);
        float d = length(q) * sign(q.x);
        return max(abs(p.y) - h, d);
    }
    ```

- [x] **5.3 — JS emitters (`objects/primitives.js`)**
  - Add `case 'partialDisk'` → `sdPartialDisk(${p}, halfHeight, radius, angle)`.
  - Add `case 'regularPolygon'` →
    `sdRegularPolygon(${p}, halfHeight, radius, sides)`.

- [x] **5.4 — Python constructors (`sdf/primitives.py`)**
  - Add `partial_disk(radius, *, half_height=None, angle=2*math.pi, id=None,
    position=None, rotation=None)` → `primitive("partialDisk",
    {"radius": ..., "halfHeight": ..., "angle": ...}, ...)` (accept a plain
    `angle`; allow `half_height` to be derived from a caller-supplied thickness).
  - Add `regular_polygon(radius, sides, *, half_height=None, id=None,
    position=None, rotation=None)` → `primitive("regularPolygon",
    {"radius": ..., "sides": ..., "halfHeight": ...}, ...)`.

- [x] **5.5 — Exports (`sdf/__init__.py`)**
  - Export `partial_disk` and `regular_polygon`.

- [x] **5.6 — Unit tests (`test_primitives.py`)**
  - `partial_disk(...).to_dict()` and `regular_polygon(...).to_dict()` produce
    the expected `kind`/`params`.
  - Position/rotation/id plumbing works (mirror the existing helper tests).

- [x] **5.7 — Validate**
  - `uv run pytest py/tests/viz/sdf/test_primitives.py -q`.

## Validation

`uv run pytest py/tests/viz/sdf/test_primitives.py -q`

## Notes

- Keep the new GLSL free of `main()` / `#version` / `precision` (the host shader
  supplies them), consistent with `primitives.glsl`.
- Axis conventions: cylinders/cones along `+Y`, radius in XZ, torus in XZ —
  the new primitives follow this (slab along Y, sector in XZ).
- The entity → SDF lowering (Phase 6) is the only consumer; no serializer change
  here.
