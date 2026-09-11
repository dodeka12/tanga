# Phase 5 — smooth CSG: frontend fold emission

## Goal

Consume the `smoothness` value emitted by phase 4 and emit the smooth GLSL folds
(`opSmoothUnion`/`opSmoothIntersect`/`opSmoothSubtract`, already defined in
`shaders/combinators.glsl`) in the standard viewer's two SDF fold sites: the
`SdfGroup` proxy fold and the `Combine`/`group` tree emitter.

## Files

- Edit: `py/pytanga/viz/templates/renderers/sdf/glsl.js`
- Edit: `py/pytanga/viz/templates/sdf/objects/combinators.js`
- Edit: `py/tests/viz/sdf/test_proxy_shader.py` (or add a small structural test)

## Steps

- [x] **5.1 — Smooth branches in `buildGroupMap` (`renderers/sdf/glsl.js`)**
  - In the per-member fold loop (where `combine` is read and the
    `subtract`/`intersection`/`xor`/`union` branches live), add
    `smooth_subtract`/`smooth_intersection`/`smooth_union` branches that mirror
    `composer.js`:
    ```js
    const k = floatParam(child.smoothness != null ? child.smoothness : 0.1);
    // smooth_union:
    vec2 sm = opSmoothUnion(d, d${i}, ${k});  d = sm.x;  m = mix(${i}.0, m, sm.y);
    // smooth_intersection: opSmoothIntersect(...)
    // smooth_subtract: opSmoothSubtract(...) (keep the positive accumulator's m)
    ```
  - Import/define a local `floatParam` (reuse the helper from
    `sdf/objects/transform.js`) and a `SMOOTHNESS_DEFAULT = 0.1` matching
    `composer.js`.

- [x] **5.2 — Smooth branches in `objects/combinators.js`**
  - Extend `foldOp(op, a, b, k)` to emit
    `opSmoothUnion(a, b, k)` / `opSmoothIntersect(a, b, k)` /
    `opSmoothSubtract(a, b, k)` for the new modes, returning the `vec2` result.
  - In `emitNode`, accept `smooth_union`/`smooth_intersection`/`smooth_subtract`
    as combinator `kind`s and thread `node.smoothness` (default `0.1`) through
    the fold; in the `group` case, pass `child.smoothness` to `foldOp`.
  - Preserve the existing scalar-returning behavior for the hard modes; note the
    `vec2` smooth result in a comment (the `.x` is distance, `.y` the blend
    factor, consistent with `composer.js`).

- [x] **5.3 — Structural test**
  - In `test_proxy_shader.py`, add an assertion that the `combinators.glsl`
    library still defines the three `opSmooth*` functions (guarding against a
    future removal), and — where a Python/Node path exists to assemble a group
    — that an `SdfGroup` with a `("smooth_union", k)` member emits `opSmoothUnion`.
    If no Node-execution harness exists for `buildGroupMap`, assert the emitted
    source via `node` in a small `dev/src` smoke, or gate on `node --check`.

## Validation

`node --input-type=module --check py/pytanga/viz/templates/renderers/sdf/glsl.js && node --check py/pytanga/viz/templates/sdf/objects/combinators.js && node dev/src/sdf_composer_smoke.mjs && uv run pytest py/tests/viz/sdf/test_proxy_shader.py py/tests/viz/sdf/test_raymarch_shader.py -q`

## Notes

- The smooth GLSL functions return `vec2(distance, blend)`; the hard combinators
  return `float`. The standard viewer's `map()` already returns
  `vec2(distance, materialIndex)`, and `buildGroupMap`/`composer.js` already mix
  the material index by the blend factor — reuse that pattern exactly.
- `composer.js` (the standalone path) already implements the smooth fold and is
  the reference for material-blend semantics; keep the standard-viewer branches
  consistent with it.
- The proxy fragment is assembled by `renderers/sdf/glsl.js` from the
  `combinators.glsl` part, so the `opSmooth*` definitions are already in scope —
  no new GLSL file is needed.
