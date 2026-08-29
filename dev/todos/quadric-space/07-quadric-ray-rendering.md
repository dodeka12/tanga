# Phase 7 — Quadric3D ray rendering (RayQuadricStyle + shader)

## Goal

`Quadric3D` renders via the analytic ray renderer by default: `RayQuadricStyle`,
serializer wire contract, and the quadric intersection shader (substitute the ray
`o + t·d` into `xᵀ Q x = 0`, solve the quadratic, shade with normal `2 A x + b`).

## Files

- New: `py/pytanga/viz/_styles/_ray_style.py` add `RayQuadricStyle`
- Modify: `py/pytanga/viz/_styles/__init__.py` + `_DEFAULT_STYLE_FOR_KIND`
- Modify: `py/pytanga/viz/serializer.py` (`_serialize_quadric`)
- New: `py/pytanga/viz/templates/renderers/ray/quadric.glsl`
- Modify: `py/pytanga/viz/templates/renderers/ray.js` (quadric intersect wiring)
- New: `py/tests/viz/test_quadric_ray.py`

## Steps

- [ ] **7.1 — `RayQuadricStyle`** — derives `RayStyle` (no extra knobs); set as the
  canonical default style for `Quadric3D` so ray is the default renderer.

- [ ] **7.2 — serializer** — `_serialize_quadric`: `kind:"ray"`, the 10 coeffs
  (or the resolved 4×4 matrix + a conservative AABB `bound`), color/opacity from the
  style chain.

- [ ] **7.3 — `quadric.glsl`** — analytic ray/quadric intersection + normal +
  `gl_FragDepth` write; reuse the SDF proxy lighting/uniform model.

- [ ] **7.4 — AABB bound** — derive a conservative proxy bound from the quadric
  matrix (or the scene bounds); document the heuristic.

- [ ] **7.5 — Tests**
  - Serializer emits `kind:"ray"` with the quadric coeffs + style.
  - `RayQuadricStyle` is the default for `Quadric3D` in `make_styles()`.
  - `node --input-type=module --check` on `ray.js`; `quadric.glsl` has no `main`.
  - `uv run pytest py/tests/viz/test_quadric_ray.py py/tests/viz/test_export_renderers.py -q`.

- [ ] **7.6 — Validate** — `uv run pytest py/tests/viz/test_quadric_ray.py
  py/tests/viz/test_export_renderers.py -q`.

## Validation

`uv run pytest py/tests/viz/test_quadric_ray.py py/tests/viz/test_export_renderers.py -q`

## Notes

- The quadratic `a t² + b t + c = 0` from `(o + t d)ᵀ Q (o + t d) = 0` is exact —
  no marching; take the nearest positive root, discard when the discriminant < 0.
- A degenerate (`a ≈ 0`) ray means the ray direction is tangent/asymptotic; handle
  by falling back to the linear root.
