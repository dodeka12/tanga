# Phase 1 — `proxy.glsl`: track closest approach + fade the silhouette

## Goal

In the standard viewer's per-object SDF proxy fragment shader
(`templates/renderers/sdf/proxy.glsl`), replace the binary `if (!hit) discard;`
with a smooth ~1-pixel silhouette fade driven by the minimum signed distance the
ray passes the surface by during the march.

## Files

- Modify: `py/pytanga/viz/templates/renderers/sdf/proxy.glsl`

## Steps

- [x] **1.1 — Track `res` during the march**
  - Before the march loop (`float t = tNear;`), add `float res = tFar;`.
  - Inside the loop, after reading `vec2 dm = map(p);`, add `res = min(res, dm.x);`
    (before the `t += dm.x` step). `res` ends as the closest the ray's samples
    came to the surface — `0` for a grazing (silhouette) ray, larger for a
    clear miss.

- [x] **1.2 — Compute the one-pixel edge scale**
  - After the loop (before the `if (!hit) discard;`), compute:
    ```glsl
    float edgePx = length(vec2(dFdx(t), dFdy(t)));
    float aa = 1.0 - smoothstep(0.0, max(edgePx, 1e-6), res);
    ```
  - `t` is the march distance (already in scope). The Euclidean `dFdx/dFdy`
    derivative (rather than `fwidth`) matches `templates/sdf/overlays/factory.js`.

- [ ] **1.3 — Replace the hard discard with a three-way result**
  - Keep the hit path (shade + `gl_FragDepth` write) unchanged.
  - Change the miss path to:
    ```glsl
    if (!hit) {
        if (aa < 0.001) discard;
        // Near-miss: emit a faint flat edge so the silhouette blends out.
        fragColor = vec4(uMaterial[0].rgb, uMaterial[0].a * uOpacity * aa);
        gl_FragDepth = 1.0;   // far depth: the edge never occludes anything
        return;
    }
    ```
  - The flat material colour (`uMaterial[0]`) is a deliberate simplification:
    on a miss there is no valid surface point/normal, so shading is skipped.
    (Shading at the closest-approach point is a possible later enhancement.)

- [ ] **1.4 — Keep the structural contract**
  - Ensure the file still has exactly one `main()`, the `out vec4` output, no
    `#version`/`precision` directives, and writes `gl_FragDepth` on every
    non-`discard` path (GLSL ES 3.0 requires writing it on all paths once it is
    written anywhere).

- [ ] **1.5 — Validate**
  - `uv run pytest py/tests/viz/sdf/test_proxy_shader.py -q`.

## Validation

`uv run pytest py/tests/viz/sdf/test_proxy_shader.py -q`

## Notes

- The march loop and the `map(p)` contract are untouched; only the miss path and
  the `res` accumulation change.
- `uMaterial[0]` is always the single-object material slot (index `m` stays `0.0`
  for non-group proxies) — but prefer `uMaterial[int(clamp(m, 0.0, ...))]` if the
  loop already resolved `m`; see Phase 2 for grouped objects.
- This phase alone does **not** change the visual result until the material is
  made transparent (Phase 2); the `aa` path only activates once blending is on.
