# Phase 2 — Implement Q3 `create_rotor` (arbitrary axis)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Extend `quadric/_create.py::create_rotor` to the 3D quadric space (`basis.dim ==
10`): a rotation about an arbitrary axis, matching `Rotor(angle, axis)`.

## Files

- Edit: `py/pytanga/quadric/_create.py`
- Edit: `py/tests/geometry/test_conic_create.py`

## Steps

- [x] **2.1 — Implement the Q3 branch in `create_rotor`**
  - Keep the Q2 branch unchanged (`basis.dim == 6`); remove the
    `NotImplementedError` for Q3.
  - For `basis.dim == 10`: normalize `axis = (aₓ, a_y, a_z)`; build an orthonormal
    frame `(p, q, r=â)` (stable cross-product: `ref = ẑ` unless `|a_z| > 0.9`).
  - Build the three commuting factors in the `b`-basis (from the derivation):
    - `R_lin  = cos(θ/2) − sin(θ/2) (P ∧ Q)` with `P = pₓ b₁ + p_y b₂ + p_z b₃`,
      `Q = qₓ b₁ + q_y b₂ + q_z b₃`.
    - `R_mixed = cos(θ/2) − sin(θ/2) (X_{pr} ∧ X_{qr})`.
    - `R_quad  = cos θ − sin θ ((D_p − D_q) ∧ X_{pq})`.
  - Monomial blades (`b`-basis):
    `D_u = (√2/2)(uₓ² b₅ + u_y² b₆ + u_z² b₇) + uₓu_y b₈ + uₓu_z b₉ + u_yu_z b₁₀`;
    `X_uv = √2(uₓvₓ b₅ + u_yv_y b₆ + u_zv_z b₇) + (uₓv_y+u_yvₓ) b₈
    + (uₓv_z+u_zvₓ) b₉ + (u_yv_z+u_zv_y) b₁₀`.
  - Return `R_lin * R_mixed * R_quad` (factors commute; grades `{0,2,4,6}`,
    norm² = 1).
- [x] **2.2 — Update the `create_rotor` docstring**
  - Drop "Q3 has no rotation rotor yet"; cite `dev/notes/quadric-rotor-derivation.md`.
  - Document that `axis` is ignored in Q2 and required (normalized) in Q3.
- [x] **2.3 — Tests**
  - Replace `test_rotor_not_supported_in_q3` with positive tests:
    - grades `{0,2,4,6}` and `norm2() ≈ 1` for a Q3 rotor (both OPNS and IPNS).
    - point identity: `R · embed_point(x) · R̃ == embed_point(R_mat·x)` for a
      non-axis-aligned axis and angle.
    - quadric identity: `from_coeffs` of `R · A · R̃` equals `R_mat Q R_matᵀ`
      (Rodrigues) for a general symmetric 4×4 `Q`.
    - Q2 branch still returns grades `{0,2,4}` and the existing
      `test_rotor_rotates_conic` stays green.
  - Reuse the existing `create(BasisQ3(), Rotor(θ, Direction(ax,ay,az)))` path.

## Validation

`uv run pytest py/tests/geometry/test_conic_create.py -q`

## Notes

- Import only from `.`/`._embedding`/`._mapping` and `math`/`numpy` — no module-level
  `geometry` import (layering).
- The formulas are pre-verified; do not re-derive the √2/2 factors.
