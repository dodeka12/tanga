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
`∘ ∈ {ip, op}` (selected from `mv.opns`, a bool on the MV/`Algebra`:
`opns=True` → outer product `EProduct.OP` (OPNS), `opns=False` → inner
product `EProduct.IP` (IPNS)):

- `pytanga.tensor.product.product_tensor(a_mask, b_mask, c_mask=None, *,
  product=EProduct, left=True, …)` returns an `MVTensor` with
  `masks=(c_mask, a_mask, b_mask)` and data shape `(|c|, |a|, |b|)` — axes
  (result `c`, left `a`, right `b`), entries in `{−1, 0, +1}`.
- Bake the entity in by contracting over the **entity** operand axis (via
  `pytanga.tensor.ops.contract`, the mask-preserving einsum wrapper):
  - entity as right operand (`left=True`):   `M[c, a] = Σ_b O[c, a, b] · e_b`
  - entity as left operand (`left=False`):   `M[c, b] = Σ_a O[c, a, b] · e_a`
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
- New: `py/pytanga/viz/templates/sdf/algebra/embeds.js` (the algebra-specific
  `evalPoint` GLSL snippet registry — a `.js` module mirroring
  `algebra/distances.js`, not a per-algebra `.glsl` file; populated here,
  consumed by Phase 8)

## Key design points

- **Canonical blade ordering.** Each algebra defines a fixed blade-id order
  (scalar first; use the algebra's `all_blades()` with a stable sort, or the
  basis display order — note `MV` has no `blade_ids()` method). `M` is emitted
  row-major over `(result_blade_rows × point_blade_cols)` against this order.
- **Point embedding is code, not a matrix.** `embed_src` is an algebra-specific
  GLSL function `evalPoint(vec3 p, out float a[NP])`:
  - E3 / P3 / PGA3: linear in `[x, y, z, 1]` (a 4-vector expanded to the
    point-blade coefficients).
  - N3: linear terms plus the `½·ρ²·e∞` quadratic term; `NP` accordingly.
- **Normalization option.** When `normalize=True` (default), normalize the
  entity MV to unit magnitude *before* contracting into `M` (via
  `mv.normalized()`), so `|r|` is a usable sphere-tracing step size.
- **Bound for infinite entities.** Planes/lines/similar carry an explicit
  `bound` region so the algebra SDF has a finite extent.

## Steps

- [ ] Algebra registry:
  - [ ] Map algebra type → embedding spec (blade order, point-blade func,
        `NP`, result-space `NR`, product-blade masks, pseudoscalar slot `I`).
  - [ ] Cover `e3`, `p3`, `n3`, `pga3` first (3D set); structure for
        future algebras.
- [ ] `embed_entity_mv(mv, *, normalize=True, bound=None)`:
  - [ ] Resolve the algebra type and select the product from `mv.opns`:
        `True` → `EProduct.OP`, `False` → `EProduct.IP`.
  - [ ] Determine the entity blade mask `e_mask` (the nonzero blades of `mv`)
        by iterating `mv.algebra.all_blades()` and keeping `bid` where
        `mv[bid] != 0` (note: `MV` has **no** `blade_ids()` method — use
        `all_blades()` + `mv[bid]`, or `mv.to_dict()`); build a
        `pytanga.blade_mask.BladeMask`. The point mask `a_mask` comes from the
        algebra spec.
  - [ ] Compute the result blade mask `c_mask` via
        `pytanga.blade_mask.predict.product_blade_mask(...)` for the chosen
        product and operand order.
  - [ ] Obtain `O = product_tensor(a_mask, e_mask, c_mask, product=…,
        left=…)` (use the `left=` flag for operand order — no manual reorder).
  - [ ] Contract the entity operand with `pytanga.tensor.ops.contract`:
        `M = contract('cab,b->ca', O, e)` (entity as right operand) or
        `contract('cab,a->cb', O, e)` (entity as left operand).
  - [ ] Emit `M` flattened row-major with `result_ids` + `point_ids`.
- [ ] `normalize` path:
  - [ ] Normalize `mv` via `mv.normalized()` (unit magnitude) before
        contraction when `True`; keep the raw MV when `False`.
- [ ] `embed_src` registry entry:
  - [ ] Add the algebra's `evalPoint` snippet to `algebra/embeds.js`,
        consistent with `point_ids`.
  - [ ] For linear algebras, express the embedding as the explicit linear
        coefficients; for N3, include the quadratic `e∞` term.
- [ ] `bound` generation for infinite entities (default extents per algebra/
      entity, overridable).
- [ ] Serialize to the `mv_sdf` wire form (see README) including:
  `algebra`, `product`, `distance`, `normalize`, `point_ids`, `result_ids`
  (with the pseudoscalar slot `I` identified), `M`, `bound`, `combine`, `style`.
- [ ] Give `SdfVisualizer` a path that serializes a **raw MV** to an `mv_sdf`
      object without routing it through `geometry.analyze()` (which re-dispatches
      to the analytic path).

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
