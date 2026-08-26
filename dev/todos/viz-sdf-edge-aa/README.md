# Viz SDF Edge Anti-Aliasing — Overview

**Created:** 2026-08-26 | **Status:** Planned | **Branch:** `feat/geo-objects`

## Goal

Remove the jagged silhouette edges on ray-marched SDF objects by replacing the
binary hit/miss `discard` in the raymarching fragment shaders with a ~1-pixel
analytic edge fade. During the sphere-trace, track the minimum signed distance
the ray passes the surface by, then fade the silhouette with a `smoothstep`
falloff scaled by the screen-space pixel footprint (`dFdx`/`dFdy`).

This is the IQ-style analytic AA approach — negligible per-frame cost (a few
extra arithmetic ops, no extra rays) versus the alternative of supersampling
(≈4× fill-rate).

## Scope

Two raymarching paths share the technique:

| Path | Files | Difficulty |
|---|---|---|
| Standard-viewer per-object SDF proxy (the visible one) | `templates/renderers/sdf/proxy.glsl`, `templates/renderers/sdf.js`, (optionally `glsl.js` + `_styles/_sdf_style.py`) | Moderate — transparency/depth care |
| Fullscreen `SdfVisualizer` | `templates/sdf/shaders/raymarch.glsl` | Easy — in-shader background |

## Root cause

`proxy.glsl` / `raymarch.glsl` march a ray and do a binary test:

```glsl
if (dm.x < SDF_EPSILON) { hit = true; break; }
...
if (!hit) discard;                          // proxy
// or:  col = hit ? shade(...) : bg;        // fullscreen
```

MSAA is already enabled (`three-view.js`:
`new THREE.WebGLRenderer({ antialias: true, ... })`), but a `ShaderMaterial`
runs its fragment once per *pixel* (not per sample) and `discard` kills the
whole pixel, so MSAA does not smooth the SDF silhouette.

## Technique (fixed up front)

During the sphere-trace, record `res = min(res, d)` — the closest the ray's
sample points get to the surface. After the loop, compute a one-pixel edge scale
using the Euclidean derivative (matching the AA'd overlays in
`templates/sdf/overlays/factory.js`, which uses `length(vec2(dFdx, dFdy))`
rather than `fwidth`'s `|dx|+|dy|`):

```glsl
float edgePx = length(vec2(dFdx(t), dFdy(t)));
float aa = 1.0 - smoothstep(0.0, max(edgePx, 1e-6), res);
```

- `hit` → full coverage (existing shading + `gl_FragDepth`).
- `!hit` near-miss (`aa > 0.001`) → faint flat edge colour at `alpha * aa`, far depth.
- `!hit` far-miss → `discard`.

`dFdx`/`dFdy` are core in GLSL ES 3.0 (WebGL2), so no portability concern.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-proxy-shader-aa.md](./01-proxy-shader-aa.md) | `proxy.glsl`: track `res`, fade silhouette, far-depth near-miss |
| 2 | [02-proxy-material-blending.md](./02-proxy-material-blending.md) | `sdf.js`: transparent proxy + optional `antialias` knob |
| 3 | [03-fullscreen-raymarch-aa.md](./03-fullscreen-raymarch-aa.md) | `raymarch.glsl`: same technique, in-shader background |
| 4 | [04-tests-docs.md](./04-tests-docs.md) | Structural shader tests + JS checks + browser smoke + changelog |

## Testing

- **No WebGL harness** exists in the repo, so shader correctness is validated by
  structural tests + manual browser smoke.
- **Python/GLSL:** `uv run pytest py/tests/viz/sdf/test_proxy_shader.py
  py/tests/viz/sdf/test_raymarch_shader.py -q` — extend with AA-symbol presence
  assertions.
- **JS:** `node --check` on touched modules; `uv run pytest
  py/tests/viz/test_export_renderers.py -q` (export bundle assembly).
- **Manual:** `uv run python py/examples/viz/sdf/mesh_vs_sdf_grid.py` (proxy),
  and an `SdfVisualizer` example (fullscreen).

## Guiding decisions / no-refactor rule

- The hit path (shading + `gl_FragDepth` + material table) is **unchanged**; only
  the miss path gains a fade.
- Reuse the codebase's existing Euclidean `dFdx`/`dFdy` derivative idiom.
- Keep `depthWrite`/`depthTest` on the proxy so hits still occlude; near-miss
  fragments write far depth.
- The `antialias` knob is **additive** and default-on.

## Deferred / non-goals

- Supersampling (SSAA) — the alternative AA route; not implemented here (too
  costly per-frame). Could be a separate opt-in knob later.
- Internal-crease AA (box/polygon sharp C0 edges) — the `res` fade smooths the
  silhouette; fully smoothing creases would mean rounding the primitives, which
  is out of scope.
