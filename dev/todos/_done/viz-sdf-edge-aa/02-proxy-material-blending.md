# Phase 2 — `sdf.js`: transparent proxy + optional `antialias` knob

## Goal

Make the per-object SDF proxy blend its (now faded) silhouette edge against the
background, and add an opt-out `antialias` toggle to `SdfStyle`. This is what
turns Phase 1's shader change into a visible result.

## Files

- Modify: `py/pytanga/viz/templates/renderers/sdf.js`
- Modify: `py/pytanga/viz/_styles/_sdf_style.py` (optional knob)
- Modify: `py/pytanga/viz/templates/renderers/sdf/glsl.js` (optional uniform)
- Modify: `py/tests/viz/sdf/test_sdf_styles.py` (optional knob test)

## Steps

- [x] **2.1 — Make the proxy material blend**
  - In `sdf.js` `createSdfProxy` (the `new THREE.ShaderMaterial({...})`), set
    `transparent: true` so the edge fragments composite over the clear
    background. Keep `depthWrite: true` and `depthTest: true` — hits still write
    real `gl_FragDepth`, so occlusion against meshes and other proxies is
    unchanged.
  - Confirm the existing `_anyTransparent(...)` logic still works: a fully-opaque
    object should now be `transparent: true` for AA, but its interior is still
    rendered at full opacity (`fragColor.a = mat.a * uOpacity`), so it looks
    opaque.

- [x] **2.2 — (Optional) `antialias` knob on `SdfStyle`**
  - Add `antialias: bool = True` to `SdfStyle` in
    `py/pytanga/viz/_styles/_sdf_style.py`; serialize it in `to_dict()`.
  - In `sdf.js`, read `ent.style.antialias !== false` and pass it as a
    `uAntialias` float uniform; in `proxy.glsl`, gate the near-miss fade
    (`aa = mix(1.0, aa, uAntialias)` or `if (uAntialias < 0.5) discard;`).
  - This keeps a cheap escape hatch if edge blending ever causes artifacts.

- [x] **2.3 — Update the material update path**
  - In `updateSdfProxy`, propagate the new `uAntialias` uniform (and keep
    `transparent` consistent) so runtime style changes work without a rebuild.

- [x] **2.4 — Validate**
  - `uv run pytest py/tests/viz/sdf/test_sdf_styles.py -q` (if 2.2 done).
  - `node --check` on `renderers/sdf.js` (copy to `.mjs` first) and `glsl.js`.

## Validation

`uv run pytest py/tests/viz/sdf/test_sdf_styles.py py/tests/viz/test_export_renderers.py -q`

## Notes

- Making **every** SDF proxy `transparent: true` is the main behavioural change
  and the main risk: three.js renders transparent objects in a sorted pass.
  Because hits write `gl_FragDepth` and near-misses write far depth, overlap
  with meshes and other proxies should still be correct; verify in the browser
  smoke (Phase 4).
- If the knob is omitted (2.2 skipped), the change is just the single
  `transparent: true` line in `sdf.js` plus Phase 1's shader edits.
