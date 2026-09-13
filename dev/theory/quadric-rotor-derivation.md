<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2021 Christian Perwass (author) -->

# Quadric-space rotation rotor (Q2 conic / Q3 quadric) — derivation

This note derives the rotation operator (versor) for the 2D conic space `CA{6}`
(Perwass) and its 3D quadric-space generalisation `CA{10}`, plus the inverse
analysis (MV → rotation angle/axis).  It is the reference the
`pytanga.quadric` code docstrings cite.

## 1. The two bases

Perwass's conic space `CA{6}` uses a **non-Euclidean** basis `e₁…e₆` with
squared norms

```
Q2:  e₁…e₆   ↔  (1, 1, 2, 2, 2, 1)
Q3:  e₁…e₁₀  ↔  (1, 1, 1, 2, 2, 2, 2, 1, 1, 1)
```

The code instead uses the **Euclidean-rescaled** basis `bᵢ` (`bᵢ·bᵢ = 1`),
related by `b = e/√2` on the norm-2 blades:

```
Q2:  b₃₄₅ = e₃₄₅ / √2,    b₁ = e₁, b₂ = e₂, b₆ = e₆
Q3:  b₄₅₆₇ = e₄₅₆₇ / √2,  b₁₂₃ = e₁₂₃, b₈₉₁₀ = e₈₉₁₀
```

The monomial ↔ blade correspondence is

| blade | Q2 | Q3 |
|---|---|---|
| b₁, b₂ | x, y | x, y |
| b₃ | 1 (const) | z |
| b₄ | x² | 1 (const) |
| b₅ | y² | x² |
| b₆ | xy | y² |
| b₇ | — | z² |
| b₈ | — | xy |
| b₉ | — | xz |
| b₁₀ | — | yz |

The point embedding is (e-basis)

```
Q2:  X(x, y)      = x e₁ + y e₂ + ½ e₃ + ½ x² e₄ + ½ y² e₅ + x y e₆
Q3:  X(x, y, z)   = x e₁ + y e₂ + z e₃ + ½ e₄ + ½ x² e₅ + ½ y² e₆ + ½ z² e₇
                    + x y e₈ + x z e₉ + y z e₁₀
```

i.e. `X(x) = M(x xᵀ)`, where `M` maps a symmetric matrix to a blade by
`q₁₃ ↦ e₁, …, ½ q₃₃ ↦ e₃, ½ q₁₁ ↦ e₄, …, q₁₂ ↦ e₆` (Q2) and the obvious
3D extension.  The `½` on the diagonal (norm-2) blades is why `M` is an
isometry with `A·B = 2 M(A)·M(B)`.

## 2. Q2 conic rotor (Perwass, eq. `GAGeo:C2:RotorDef1`)

A rotation by θ about the origin, applied as `R A R̃`, with

```
R = R₂ R₁
R₁ = cos θ − ½ sin θ (e₄ − e₅) ∧ e₆
R₂ = cos(θ/2) − sin(θ/2) e₁ ∧ e₂
```

In the `b`-basis (`½ → √2/2` on the rescaled blades):

```
R₁ = cos θ − (√2/2) sin θ (b₄ − b₅) ∧ b₆
R₂ = cos(θ/2) − sin(θ/2) b₁ ∧ b₂
```

which is exactly `quadric/_create.py::create_rotor`
(`r1 = {0: cos θ, b₄₆: −k, b₅₆: +k}`, `k = √2/2 sin θ`;
`r2 = {0: cos(θ/2), b₁₂: −sin(θ/2)}`).  `R₂` rotates the **linear** monomials
(x, y); `R₁` rotates the **traceless quadratic** monomials (x²−y², 2xy).

## 3. Q3 z-axis rotor (the direct analog)

Rotation about z by θ is the product of **three commuting factors** (each a
simple bivector rotor in a disjoint plane):

```
R = R_lin · R_mixed · R_quad
R_lin    = cos(θ/2) − sin(θ/2) b₁∧b₂
R_mixed  = cos(θ/2) − sin(θ/2) b₉∧b₁₀
R_quad   = cos θ − (√2/2) sin θ (b₅ − b₆) ∧ b₈
```

In the `e`-basis this reads `cos θ − ½ sin θ (e₅ − e₆) ∧ e₈` — the same
`½`-coefficient structure as Perwass's Q2 `R₁`, relabelled.

## 4. Q3 general-axis rotor (arbitrary unit axis â)

Let `r = â` and `(p, q, r)` be an orthonormal frame (`p, q ⟂ r`).  Define the
monomial blades (e-basis, `M`-normalised)

```
D_u  = M(u uᵀ)      = ½(uₓ² e₅ + u_y² e₆ + u_z² e₇) + uₓu_y e₈ + uₓu_z e₉ + u_yu_z e₁₀
X_uv = M(u vᵀ + v uᵀ)
     = uₓvₓ e₅ + u_yv_y e₆ + u_zv_z e₇
       + (uₓv_y + u_yvₓ) e₈ + (uₓv_z + u_zvₓ) e₉ + (u_yv_z + u_zv_y) e₁₀
```

(`D_u` is the `u²` form, `X_uv` the `uv` cross form; note `X_uu = 2 D_u`.)
Then

```
R = R_lin · R_mixed · R_quad
R_lin    = cos(θ/2) − sin(θ/2) (P ∧ Q)              P∧Q = aₓ e₂₃ + a_y e₃₁ + a_z e₁₂
R_mixed  = cos(θ/2) − sin(θ/2) (X_{pr} ∧ X_{qr})
R_quad   = cos θ − sin θ ((D_p − D_q) ∧ X_{pq})
```

where `P, Q` are the linear blades of `p, q`.  The three factors commute and
act at rates θ (linear), θ (mixed quadratic), and **2θ** (traceless quadratic);
the invariants are the trace `x²+y²+z²`, the `r²` monomial, and the constant.
In the `b`-basis, multiply the `e₅₆₇` coefficients by `√2`:

```
D_u  = (√2/2)(uₓ² b₅ + u_y² b₆ + u_z² b₇) + uₓu_y b₈ + uₓu_z b₉ + u_yu_z b₁₀
X_uv = √2(uₓvₓ b₅ + u_yv_y b₆ + u_zv_z b₇)
       + (uₓv_y + u_yvₓ) b₈ + (uₓv_z + u_zvₓ) b₉ + (u_yv_z + u_zv_y) b₁₀
```

**Verification.**  The rotor reproduces the rotation of any symmetric matrix
`Q` (`R A R̃ = R_mat A R_matᵀ` with `R_mat` the 3×3 Rodrigues rotation) and of
any point (`R X(x) R̃ = X(R_mat x)`), both to ~1e-15 for arbitrary axes; the
z-axis case reduces exactly to §3.

## 5. Analysis — MV → `Rotor(angle, axis)`

The rotor is an even versor (grades `{0,2,4}` in Q2, `{0,2,4,6}` in Q3).  The
rotation it encodes is recovered by sandwiching the **linear basis blades** and
reading the coefficients into a rotation matrix `m`:

```
Q2:  R b₁ R̃, R b₂ R̃          → 2×2 matrix;  angle = atan2(m₁₀, m₀₀), axis = (0,0,1)
Q3:  R b₁ R̃, R b₂ R̃, R b₃ R̃   → 3×3 matrix;  angle = acos(clip((tr − 1)/2)),
                                         axis  = normalised dual of the skew part (±)
```

The other factors (`R_mixed`, `R_quad`) commute with the linear blades, so only
`R_lin` contributes to `m` — the extraction is exact and sign-stable.  The
axis sign is a convention (the `±` of the skew-dual), matching the existing
E3/N3 rotor-analysis behaviour.

## 6. Degrees of freedom (9 points / 3 action points)

A 3D quadric has 9 degrees of freedom (10 homogeneous coefficients up to
scale).  Nine points in general position give 9 independent linear constraints
on the coefficients, so they determine a unique quadric.  Dragging 3 of the 9
points (3×3 = 9 dof) traces a full-dimensional open set of the 9-dimensional
quadric space: every non-degenerate quadric, but not the measure-zero
degenerate cases (planes, plane pairs, imaginary quadrics).
