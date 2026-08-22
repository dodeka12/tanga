# Phase 7 — Algebra embedding (Python): ordering, `M`, `embed_src`, normalize, bound

**Status:** Planned

## Goal

Reduce an MV to a *partially contracted product tensor* `M` and a matching
algebra-specific point-embedding GLSL snippet, so the shader can compute the
distance by `r = M·a`, `d = distOf(r)` with no algebra branching in the shader.

This module is the **algebra SDF backend** and the single source of truth for
the canonical blade ordering shared between `M` and `embed_src`.

## Background — the product-matrix reduction

For an MV `e` with coefficients `e_b` over its blade mask and a chosen product
`∘ ∈ {ip, op}` (from `mv.algebra.opns`):

- `product_tensor(a_mask, b_mask, c_mask, product=…)` returns
  `O[c, a, b] ∈ {−1, 0, +1}` (axes: result `c`, left `a`, right `b`).
- Bake the entity in by contracting over the **entity** operand axis:
  - entity as right operand:  `M[c, a] = Σ_b O[c, a, b] · e_b`
  - entity as left operand:   `M[c, b] = Σ_a O[c, a, b] · e_a`
- `M` then encodes "the general product MV" as a matrix over result-blade ×
  point-blade space. The shader supplies `a` (the embedded point) and the
  backend supplies `e` (already consumed into `M`).

The **result blade mask** `c_mask` is the full result space (not just the scalar
blade), because the distance functions (e.g. the default `scalar_pseudo`) read
the scalar, the pseudoscalar, and the magnitude of the remaining grades. The
result ordering therefore always includes the scalar blade at slot `0` and the
pseudoscalar blade at a fixed, algebra-specific slot `I`.

## Files

- New: `py/pytanga/viz/sdf/algebra_embedding.py`
- New: `py/pytanga/viz/templates/sdf/algebra/embed_<algebra>.glsl` (generated
  snippet text; see steps)

## Key design points

- **Canonical blade ordering.** Each algebra defines a fixed blade-id order
  `blade_ids` (scalar first; use the algebra's `all_blades()` with a stable
  sort, or the basis display order). `M` is emitted row-major over
  `(result_blade_rows × point_blade_cols)` against this order.
- **Point embedding is code, not a matrix.** `embed_src` is an algebra-specific
  GLSL function `evalPoint(vec3 p, out float a[NP])`:
  - E3 / P3 / PGA3: linear in `[x, y, z, 1]` (a 4-vector expanded to the
    point-blade coefficients).
  - N3: linear terms plus the `½·ρ²·e∞` quadratic term; `NP` accordingly.
- **Normalization option.** When `normalize=True` (default), normalize the
  entity MV to unit magnitude *before* contracting into `M`, so `|r|` is a
  usable sphere-tracing step size.
- **Bound for infinite entities.** Planes/lines/similar carry an explicit
  `bound` region so the algebra SDF has a finite extent.

## Steps

- [ ] Algebra registry:
  - [ ] Map algebra type → embedding spec (blade order, point-blade func,
        `NP`, result-space `NR`, product-blade masks).
  - [ ] Cover `e3`, `p3`, `n3`, `pga3` first (3D set); structure for
        future algebras.
- [ ] `embed_entity_mv(mv, product, *, normalize, bound)`:
  - [ ] Resolve algebra type and select the product (`ip`/`op`) from
        `mv.algebra.opns`.
  - [ ] Determine the entity blade mask `e_mask` (nonzero blades of `mv`) and
        the point blade mask `a_mask`.
  - [ ] Compute the result blade mask `c_mask` via
        `product_blade_mask(...)` for the chosen product and operand order.
  - [ ] Obtain `O = product_tensor(a_mask, e_mask, c_mask, product=…)`
        (adjust left/right order).
  - [ ] Contract the entity operand: `M = einsum('cab,b->ca', O, e_coeffs)`
        (or `'cab,a->cb'` for the left-operand case).
  - [ ] Emit `M` flattened row-major with `result_ids` + `point_ids`.
- [ ] `normalize` path:
  - [ ] Normalize `mv` (unit magnitude) before contraction when `True`.
  - [ ] Keep a raw (non-normalized) path when `False`.
- [ ] `embed_src` generator:
  - [ ] Produce GLSL `evalPoint` (as a string) consistent with `point_ids`.
  - [ ] For linear algebras, express the embedding as the explicit linear
        coefficients; for N3, include the quadratic `e∞` term.
- [ ] `bound` generation for infinite entities (default extents per algebra/
      entity, overridable).
- [ ] Serialize to the `mv_sdf` wire form (see README) including:
  `algebra`, `product`, `distance`, `normalize`, `point_ids`, `result_ids`
  (with the pseudoscalar slot `I` identified), `M`, `bound`, `combine`, `style`.

## Unit tests

File: `py/tests/viz/sdf/test_algebra_embedding.py`

- [ ] `test_m_reconstruction` — for a known entity (e.g. PGA3 plane), `M`
      contracted against the embedded point reproduces the direct `ip/op`
      result MV (using `tensor.ops.contract`).
- [ ] `test_shape_and_ordering` — `M` shape is `(len(result_ids) ×
      len(point_ids))` and matches the emitted `embed_src` ordering.
- [ ] `test_p3_trivector` — P3 `point op line` yields a nonzero `|r|` even
      though the scalar blade is zero.
- [ ] `test_normalize_scales` — `normalize=True` and `False` produce
      scaled-but-proportional `M`.
- [ ] `test_embed_src_consistency` — `embed_src` generated for an algebra
      fills the same `point_ids` the `M` matrix expects.

## Verification

- [ ] Unit test: for a known entity (e.g. PGA3 plane), `M` reconstructions
      against the direct `ip/op` of the embedded point reproduce the same
      result MV coefficients (in Python, using `tensor.ops.contract`).
- [ ] `M` shape is `(len(result_ids) × len(point_ids))` and matches the
      emitted `embed_src` ordering.
- [ ] P3 `point op line` yields a nonzero `|r|` (trivector) even though its
      scalar blade is zero — confirming the full result-mask choice, and
      `scalar_pseudo` gives a signed distance there (pseudoscalar + rest).
- [ ] `normalize=True` and `False` produce scaled-but-proportional `M`.
- [ ] The `mv_sdf` wire form carries `combine` so `algebra_embedding.py`
      output participates in Phase 5/11 booleans like analytic objects.
- [ ] `uv run pytest py/tests/viz/sdf/test_algebra_embedding.py` passes.
