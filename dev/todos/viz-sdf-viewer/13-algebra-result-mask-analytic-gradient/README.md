# Phase 13 — Active result mask + per-object analytical step gradient

**Status:** Planned

## Goal

Two coupled optimizations to the algebra (`mv_sdf`) rendering path:

1. **Active result mask** — shrink each object's `M` matrix from the full result
   algebra (`2^dim × NP`) to the *exact* non-zero result blades returned by
   `product_blade_mask(point_mask, entity_mask, product)`, cutting `u_M` by up to
   ~32× and the per-leaf matmul by the same factor.
2. **Per-object analytical step gradient** — compute `|∇d|` for each `mv_sdf`
   object in closed form inside its leaf (**option B**: carry it through the
   single composed `map()`), replacing the 4-probe finite-difference
   `calcGradientNorm` in the raymarch hot loop. The derivative uses branchless
   guards (no `if`), per the project's no-branching convention.

Both changes preserve the existing "one composed `map()`, no
algebra/entity/distance branching" contract (Phase 8).

## Parts

| Part | Plan | Summary | Test gate |
|---|---|---|---|
| A | [part-a-active-result-mask.md](part-a-active-result-mask.md) | Backend: shrink `M` to the active result mask (scalar + pseudoscalar kept) | `uv run pytest py/tests/viz/sdf/test_algebra_embedding.py py/tests/viz/sdf/test_calibration.py` |
| B | [part-b-analytical-step-gradient.md](part-b-analytical-step-gradient.md) | Frontend: per-mask distance fn + `vec3 map()` carrying analytical `|∇d|` | `node dev/src/sdf_algebra_smoke.mjs && node dev/src/sdf_composer_smoke.mjs` |
| C | [part-c-tests-and-docs.md](part-c-tests-and-docs.md) | Test updates, docs, changelog | `uv run pytest py/tests/viz/` (full suite) |

Order: **A → B → C** (B depends on A's wire shape; C depends on A+B). Each
part's steps are individually testable; run the per-part gate after each part.

## Background

### Result mask — why it is the full algebra today

`embed_entity_mv` already contracts the *entity* axis away on the backend and
keeps the *point* axis minimal (the OPNS point blades only: e3=3, p3=4, n3=5,
pga3=7). The **result** axis, however, is deliberately the full algebra:

```python
# algebra_embedding.py (design note)
# The result blade mask is the full algebra (all blades, scalar at slot 0,
# pseudoscalar at the last slot), because the distance functions (e.g. the
# default `scalar_pseudo`) read the scalar, the pseudoscalar, and the
# magnitude of every other grade.
result_mask = BladeMask(alg, _result_ids(alg))   # sorted(range(algebra_dim))
```

So `M` is `2^dim × NP` with mostly-zero rows. The exact output mask already
exists: `product_blade_mask(point_mask, entity_mask, product=…)` (the same
function `product_tensor(..., c_mask=None)` calls internally). Measured against
the Phase 10 demo (`demo_sdf_algebra.py`):

| entity | full `M` | active `M` | reduction |
|---|---|---|---|
| pga3 plane | 224 (32×7) | 28 (4×7) | 8× |
| p3 line | 64 (16×4) | 20 (5×4) | 3.2× |
| n3 sphere | 160 (32×5) | 10 (2×5) | 16× |
| n3 circle | 160 (32×5) | 35 (7×5) | 4.6× |
| **total** | **608** | **93** | **~6.5×** |

Verified exact (not a superset): dropping the all-zero rows of the full `M`
reproduces the active-mask `M` for each entity (`mask_exact=True`, `match=True`).

**Design note — always keep scalar + pseudoscalar:** the result mask is the
pure-active mask *plus* the scalar (blade `0`) and pseudoscalar blades. Those two
extra rows are structurally zero for entities that don't produce them, so they
contribute nothing to any distance function; keeping them means the scalar always
sits at slot `0` and the pseudoscalar at a valid `SLOT_PSEUDO` (never absent).
The distance-function snippets in `distances.js` therefore stay unchanged (they
already read `r[0]` and `SLOT_PSEUDO`), and no `-1` sentinel handling is needed.

### Step gradient — why it is finite-difference today

`raymarch.glsl` steps `d` directly for analytic objects (proper SDFs, `|∇d|=1`),
but for algebraic objects it probes the **entire composed `map()`** 4× with a
tetrahedral stencil:

```glsl
float calcGradientNorm(vec3 p) { … 4 × map(p) probes, e = 0.001 … }
…
if (matId >= 0 && matId < uMaterialCount && u_ObjectParams[matId].w > -0.5) {
    stepSize = d / max(calcGradientNorm(p), 1.0);
}
```

That 4× scene re-traversal is the dominant per-iteration cost for algebraic
scenes (the step runs up to 256×/ray).

## Decisions

1. **Active result mask** via `product_blade_mask(point_mask, entity_mask,
   product=product)` — exact, already unit-tested, and already used internally
   by `product_tensor` when `c_mask=None`.
2. **Per-object distance/derivative emission** keyed by `(algebra, result_ids,
   distance, params)`, replacing the current per-algebra dedup. Objects of the
   same kind/algebra still share one `distOf` (their masks are identical).
3. **Option B** for the gradient: each leaf returns `vec2(d, |∇d|)`; the composed
   `map()` returns `vec3(d, m, g)` and threads the winner's `g` through the fold
   exactly as it already threads `m`. Analytic objects contribute `g = 1.0`.
4. **Branchless guards** for every `1/sqrt(rest)` denominator — no
   `if (rest < eps)`; see the construction below. The `u_ObjectParams.w` "is
   algebraic" sentinel becomes obsolete and is dropped (the carried `g` already
   encodes analytic=1.0 vs algebraic).
5. **Analytical normals deferred** (optional follow-on): the same `∇d` gives the
   surface normal direction, but `calcNormal` runs once per hit (not per step),
   so it is lower priority.

## Reference — derivative math

The leaf is `d = D(r) · scale − thickness`, `r[k] = Σₘ M[k,m]·a[m](p)`.

```
g[k]  = ∂D/∂r[k]              (derivative of the distance fn)
h[m]  = Σₖ M[k,m]·g[k]  = (Mᵀg)[m]
∇d_j  = Σₘ h[m] · ∂a[m]/∂p_j   (algebra-specific point Jacobian)
|∇d|  = length(∇d)  →  step = d / max(scale·|∇d|, 1.0)
```

**Distance-function derivative `g` (per registry entry, added to `distances.js`):**

| distance | `g[k]` |
|---|---|
| `scalar_pseudo` | `1` for the scalar & pseudo slots; `r[k]·invRest` otherwise |
| `magnitude` | `r[k]·invRest` (over the whole vector) |
| `scalar` | `δ[k, scalar]` |
| `grade` | `r[k]·invGrade` on the selected grade, else `0` |
| `component` | `δ[k, blade_id]` |

`invRest` is the branchless inverse-sqrt of the relevant squared norm.

**Point Jacobian `∂a/∂p` (per algebra, added to `embeds.js`; `h = Mᵀg`):**

| algebra | `∇d` in terms of `h` |
|---|---|
| `e3`, `p3` | `(h₀, h₁, h₂)` |
| `n3` | `(h₀ + x(h₃+h₄), h₁ + y(h₃+h₄), h₂ + z(h₃+h₄))` |
| `pga3` | `(−h₃−h₆, h₂+h₅, −h₁−h₄)` |

**Branchless sqrt guard** (replaces `if (rest < eps) g = 0`; the comparison
yields `0.0/1.0`, so the epsilon is added only when the norm is tiny — a single
predicated-select op, never a divergent branch):

```glsl
// EPS_SQ ~ 1e-6 (sqrt ~ 1e-3, the same scale as the FD step e=0.001). Any of
// these are branchless and equivalent; prefer the first (matches the
// `x + (x < eps)*eps` pattern):
float invRest  = inversesqrt(rest + float(rest < EPS_SQ) * EPS_SQ);
// or: float invRest = inversesqrt(max(rest, EPS_SQ));
// or: float invRest = inversesqrt(rest + (1.0 - step(EPS_SQ, rest)) * EPS_SQ);
```

At `rest == 0` the numerator `r[k]` is also `0`, so `g[k] = 0` and `|∇d| = 0`
→ the `max(|∇d|, 1.0)` floor keeps `step = d` (the same behaviour the FD probe
produces there, without its numerical noise). The distance function *itself*
(`sqrt(rest)`) needs no guard — `sqrt(0)` is defined; only the derivative's
`1/sqrt` does.

## Measured baselines (validation)

Analytical `∇d` vs the existing finite-difference `calibration.gradient()` at
`(0.7, −0.3, 1.1)`:

| entity | `|∇d|` analytic | `|∇d|` FD | direction error |
|---|---|---|---|---|
| pga3 plane | 1.41421 | 1.41421 | 0.0 |
| p3 line | 1.00000 | 1.00000 | 7.5e-10 |
| n3 sphere | 0.48132 | 0.48132 | 1.0e-12 |
| n3 circle | 0.60006 | 0.60006 | 8.7e-11 |

This also confirms the field is *both* over-1-Lipschitz (pga3 `√2`) and
under-1 (n3 sphere/circle), so the `max(|∇d|, 1.0)` floor stays.

