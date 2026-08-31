# Phase 3 — `raymarch.glsl`: fullscreen SDF viewer AA

> **Status: Deferred** (user decision, 2026-08-26). The plan's `mix(bg, col, aa)`
> fade is a no-op in the fullscreen viewer (on a miss `col` is already `bg`, and
> on a hit `res`≈ε so `aa`≈1), so it does not soften the silhouette. Correctly
> fading it requires shading the *closest-approach* point on a near-miss. The
> standard-viewer proxy (Phases 1–2) is unaffected and already anti-aliased.
> Revisit this phase with the closest-approach shading when fullscreen AA is
> wanted.

## Goal

Apply the same silhouette fade to the fullscreen `SdfVisualizer` raymarcher
(`templates/sdf/shaders/raymarch.glsl`). This is the easier path — the shader
already computes its own background (`bg`), so there is no transparency/depth
complication.

## Files

- Modify: `py/pytanga/viz/templates/sdf/shaders/raymarch.glsl`

## Steps

- [ ] **3.1 — Track `res` during the march**
  - Before the loop (`float t = uCameraNear;`), add `float res = maxDist;`.
  - In the loop, after `float d = m.x;`, add `res = min(res, d);`.

- [ ] **3.2 — Fade the silhouette in `main()`**
  - Compute the one-pixel edge scale after the loop:
    ```glsl
    float edgePx = length(vec2(dFdx(t), dFdy(t)));
    float aa = 1.0 - smoothstep(0.0, max(edgePx, 1e-6), res);
    ```
  - Replace the `if (hit) { ... } else { col = bg; }` with:
    ```glsl
    if (hit) {
        vec3 p = ro + rd * t;
        vec3 n = calcNormal(p);
        float matId = map(p).y;
        col = shade(ro, rd, p, n, matId);
    } else {
        col = bg;
    }
    col = mix(bg, col, aa);   // fade the silhouette into the background
    ```
  - `aa` is `0` at a grazing miss and `1` on a solid hit, so the blend only
    affects the ~1px silhouette.

- [ ] **3.3 — Keep the overlay compositing order**
  - Apply `applyOverlays(...)` **after** the `mix` (unchanged position), so
    grid/axis overlays still depth-composite on top of the AA'd surface.

- [ ] **3.4 — Validate**
  - `uv run pytest py/tests/viz/sdf/test_raymarch_shader.py -q`.

## Validation

`uv run pytest py/tests/viz/sdf/test_raymarch_shader.py -q`

## Notes

- `bg` is hard-coded `vec3(0.10, 0.10, 0.18)` in this shader, so the fade blends
  against that exact colour (consistent with the current hard `col = bg`).
- No `discard`, no `gl_FragDepth`, no transparency changes — the fullscreen
  viewer renders a single full-screen quad.
