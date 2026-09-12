# Phase 1 — Derivation document

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Write `dev/notes/quadric-rotor-derivation.md` — the authoritative derivation of
the Q2/Q3 rotation rotors and their analysis, with a copyright + author notice.

## Files

- New: `dev/notes/quadric-rotor-derivation.md`

## Steps

- [x] **1.1 — Header (copyright + author notice)**
  - Match the code header convention, adapted to Markdown:
    ```
    <!-- SPDX-License-Identifier: Apache-2.0 -->
    <!-- Copyright 2021 Christian Perwass (author) -->
    ```
  - Title: `# Quadric-space rotation rotor (Q2 conic / Q3 quadric) — derivation`.
- [x] **1.2 — Notation + the two bases**
  - State Perwass's non-Euclidean `e`-basis for `CA{6}` (norms² `(1,1,2,2,2,1)`)
    and `CA{10}` (norms² `(1,1,1,2,2,2,2,1,1,1)`), and the Euclidean-rescaled
    `b`-basis used by the code (`b₃₄₅ = e₃₄₅/√2` for Q2; `b₄₅₆₇ = e₄₅₆₇/√2` for Q3).
  - Give the monomial↔blade table (x, y, z, 1, x², y², z², xy, xz, yz).
- [x] **1.3 — Q2 rotor (Perwass, eq. `GAGeo:C2:RotorDef1`)**
  - `R = R₂ R₁`, `R₁ = cos θ − ½ sin θ (e₄ − e₅) ∧ e₆`, `R₂ = cos(θ/2) − sin(θ/2) e₁ ∧ e₂`.
  - Show the `b`-basis form (`½ → √2/2`) and its correspondence to
    `quadric/_create.py::create_rotor` (`b46`, `b56`, `b12`).
- [x] **1.4 — Q3 z-axis rotor (the direct analog)**
  - `R = R_lin · R_mixed · R_quad` with (in the `b`-basis)
    `R_lin = cos(θ/2) − sin(θ/2) b₁∧b₂`,
    `R_mixed = cos(θ/2) − sin(θ/2) b₉∧b₁₀`,
    `R_quad = cos θ − (√2/2) sin θ (b₅ − b₆) ∧ b₈`.
  - Explain the three commuting factors and the rates θ / θ / 2θ via the
    monomial (quadrupole) decomposition.
- [x] **1.5 — Q3 general-axis rotor (arbitrary axis â)**
  - Frame construction: unit `r = â`, orthonormal `(p, q) ⟂ r`.
  - Monomial blades (e-basis): `D_u = M(u uᵀ) = ½(uₓ² e₅ + u_y² e₆ + u_z² e₇)
    + uₓu_y e₈ + uₓu_z e₉ + u_yu_z e₁₀` and
    `X_uv = M(u vᵀ + v uᵀ) = uₓvₓ e₅ + u_yv_y e₆ + u_zv_z e₇ + (uₓv_y+u_yvₓ) e₈
    + (uₓv_z+u_zvₓ) e₉ + (u_yv_z+u_zv_y) e₁₀`.
  - Rotor: `R_lin = cos(θ/2) − sin(θ/2)(P∧Q)` (with `P∧Q = aₓ e₂₃ + a_y e₃₁ + a_z e₁₂`),
    `R_mixed = cos(θ/2) − sin(θ/2)(X_{pr} ∧ X_{qr})`,
    `R_quad = cos θ − sin θ ((D_p − D_q) ∧ X_{pq})`.
  - Give the `b`-basis form (multiply the `e₅₆₇` coefficients by `√2`), and note
    the three factors commute.  Reference the verified identity
    `R A R̃ = R_mat A R_matᵀ` (Rodrigues) and the point identity `R X(x) R̃ = X(Rx)`.
- [x] **1.6 — Analysis (MV → `Rotor(angle, axis)`)**
  - Extract the linear rotation by sandwiching the linear basis blades
    (`b₁,b₂` for Q2; `b₁,b₂,b₃` for Q3) and reading the coefficients into a
    rotation matrix.
  - Q2: `angle = atan2(m₁₀, m₀₀)`, `axis = Dir(0,0,1)`.
  - Q3: `angle = acos((tr−1)/2)`, `axis = normalized dual of the skew part`
    (sign is a convention, up to ±).
  - Note why `analyze` reaches the operator path (mixed grades → entity analysis
    raises → falls through).
- [x] **1.7 — Degrees-of-freedom note**
  - 9 points → unique quadric; 3 draggable points → 9 dof → open dense set of
    quadrics (degenerate ones excluded).

## Validation

`uv run mkdocs build --strict` (the doc must not break the build; it is a
`dev/notes` Markdown file, so this is a sanity check only — no nav change).

## Notes

- The Q3 general-axis formula and the analysis were pre-verified numerically
  (point identity and `R A R̃ = R_mat A R_matᵀ` hold to ~1e-15 for arbitrary
  axes); the doc records those exact formulas so phase 2/3 implement them
  without re-deriving.
- Keep the doc self-contained: it is the reference the code docstrings cite.
