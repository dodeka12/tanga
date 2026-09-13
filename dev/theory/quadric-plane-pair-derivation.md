<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2021 Christian Perwass (author) -->

# Degenerate quadric analysis (plane pairs) — derivation

This note derives the analysis of degenerate 3D quadrics — plane pairs,
parallel plane pairs, and single/double planes — by extending Perwass's
degenerate-conic (line-pair) analysis to one dimension up.  It is the reference
the `pytanga.quadric` docstrings cite (the code mirrors it in
`refine.py::_plane_pair_from_quadric`, `_parallel_plane_pair_from_quadric`,
`_plane_from_homogeneous` and `_create.py::create_plane_pair` /
`create_parallel_plane_pair`).

The 2D source is Perwass, *ConicIntersect.tex*, §"Analysis of Conics": a
degenerate conic is a **line pair** (two lines through a common point), a
**parallel line pair**, or a **double line**.  The 3D analogue treated here is a
**plane pair** (two planes through a common line), a **parallel plane pair**, or
a **double plane**.

## 1. Homogeneous quadric and the affine block form

A quadric in affine 3D is `xᵀ A x = ρ` with symmetric `A ∈ ℝ³ˣ³`, `x ∈ ℝ³`,
`ρ ∈ ℝ`.  Homogenising `x_H = [x, 1]ᵀ` turns it into

```
Q_H = [[A, 0], [0, −ρ]]            (x_Hᵀ Q_H x_H = 0)
```

An arbitrary symmetric `4×4` matrix has the affine block form

```
Q_H = [[A, b], [bᵀ, f]],           A ∈ ℝ³ˣ³ symmetric, b ∈ ℝ³, f ∈ ℝ
```

Let `r = rank(Q_H)` and `rq = rank(A)`.  Diagonalising `A = U Λ Uᵀ` (eigenvalues
`λ₁, λ₂, λ₃`, `U` orthogonal) reduces `Q_H` — after a rotation and a translation
by `t = −A⁻¹b` (when `A` is invertible) — to Perwass's canonical form

```
Λ_H = diag(λ₁, λ₂, λ₃, −ρ)
```

where `ρ` is the (signed) constant the centred quadric has to equal.  Every
classification below follows from the signs of `λ₁, λ₂, λ₃, ρ` (up to a global
sign, since `Q_H` and `−Q_H` define the same quadric).

## 2. Perwass's degenerate conic (2D) in one paragraph

In 2D the conic matrix is `3×3`.  A **line pair** has `ρ = 0` and quadratic-part
eigenvalues `λ₁ > 0 > λ₂`, so the full matrix has eigenvalues `{λ₋, 0, λ₊}` and
rank 2.  Perwass factors it via the eigen-decomposition: with unit eigenvectors
`v₊` (of `λ₊`) and `v₋` (of `λ₋`),

```
l₁ = √λ₊ v₊ + √(−λ₋) v₋          Q ∝ l₁ l₂ᵀ + l₂ l₁ᵀ
l₂ = √λ₊ v₊ − √(−λ₋) v₋
```

The `lᵢ` are homogeneous line vectors (`a x + b y + c = 0`).  This is exactly
`refine.py::_line_pair_from_conic`.  A **parallel line pair** (`λ₂ = 0`, `ρ > 0`)
and a **double line** (`λ₂ = 0`, `ρ = 0`) are handled separately.

## 3. Plane pair from a rank-2 quadric (the direct extension)

The 3D analogue of the line pair is the **plane pair**: a rank-2 quadric.  Its
`4×4` matrix has eigenvalues `{λ₋, 0, 0, λ₊}` (`λ₋ < 0 < λ₊`, i.e. `r = 2`,
`rq = 2`, quadratic part indefinite).  The same eigen-decomposition applies:

```
p₁ = √λ₊ v₊ + √(−λ₋) v₋          Q ∝ p₁ p₂ᵀ + p₂ p₁ᵀ
p₂ = √λ₊ v₊ − √(−λ₋) v₋
```

where `pᵢ = [nᵢ, dᵢ]` are homogeneous plane vectors (`nᵢᵀ x + dᵢ = 0`).

*Why this works.*  `Q` is real symmetric, so `Q = V Λ Vᵀ = λ₊ v₊v₊ᵀ + λ₋ v₋v₋ᵀ`
(the two zero eigenvalues contribute nothing).  With `a = √λ₊ v₊` and
`b = √(−λ₋) v₋`,

```
a aᵀ − b bᵀ = Q = ½[(a+b)(a−b)ᵀ + (a−b)(a+b)ᵀ]
```

so `Q ∝ p₁ p₂ᵀ + p₂ p₁ᵀ` with `p₁ = a + b`, `p₂ = a − b` (the `½` and `√2` are
absorbed by the homogeneous scale).  Substituting into the quadratic form,

```
x_Hᵀ Q x_H ∝ 2 (p₁ᵀ x_H)(p₂ᵀ x_H) = 0   ⟺   x_H on plane 1 or plane 2.
```

The two planes meet in a line (the two-plane intersection); the `PlanePair`
entity stores only the two planes, not the intersection line.  This is
`refine.py::_plane_pair_from_quadric`, a verbatim 4D restatement of the 2D line
pair.

## 4. Parallel plane pair (rank 2, `rq = 1`)

Two parallel planes share a normal `n` and differ only in their offsets, so the
quadratic part is rank 1: `A = λ n nᵀ` (`λ = ±1` after normalisation).  The
matrix has the form

```
Q = [[λ n nᵀ, β n], [β nᵀ, f]]          nᵀ x = dᵢ
```

which represents `λ (nᵀx)² + 2β (nᵀx) + f = 0`.  Completing the square,

```
(nᵀx + β/λ)² = β²/λ² − f/λ    ⟹    nᵀx = −β/λ ± √(β²/λ² − f/λ)
```

so the two plane offsets are `d₁ = −β/λ + √(β²/λ² − f/λ)` and
`d₂ = −β/λ − √(β²/λ² − f/λ)`.  In the code (`_parallel_plane_pair_from_quadric`)
`β = b·v` is read off with the unit eigenvector `v` of the single non-zero
eigenvalue `λ`.

*Sign subtlety.*  Because `Q` and `−Q` are the same quadric, the quadratic part
can come back as `−n nᵀ` (negative definite), placing the non-zero eigenvalue at
index 0 of the ascending `eigh` order rather than index 2.  The code therefore
locates it by **magnitude** (`argmax(|λᵢ|)`) instead of position.

## 5. Single plane and double plane (`r = 1` / `rq = 0`)

A single plane `nᵀx + d = 0` has two inequivalent quadric realisations:

- **`r = 2`, `rq = 0`** — the *linear* form

  ```
  Q = [[0, n/2], [nᵀ/2, d]]        x_Hᵀ Q x_H = nᵀx + d = 0
  ```

  This is what `create_plane` writes and `_plane_from_quadric` reads back
  (`a = 2 Q₀₃`, …).

- **`r = 1`** — the *double plane* `Q = [n, d][n, d]ᵀ` (`(nᵀx + d)² = 0`), the
  squared homogeneous plane vector.

Both classify as `EQuadricKind.plane`; a rank-2 `plane_pair` with `rq = 2` and a
**definite** quadratic part (both eigenvalues same sign) is the imaginary
"degenerate line/point" case, not a real plane pair.

## 6. Classification summary

| rank `r` | `rq` | quadratic-part signs | entity |
|---|---|---|---|
| 4 | 3 | definite / indefinite | ellipsoid / hyperboloid |
| 4 | 2 | — | paraboloid |
| 3 | 3 | indefinite | cone |
| 3 | 2 | — | cylinder |
| 3 | 1 | — | parabolic cylinder |
| 2 | 2 | opposite signs | **plane pair** (intersecting) |
| 2 | 2 | same signs | imaginary (degenerate line/point) |
| 2 | 1 | — | **parallel plane pair** |
| 2 | 0 | — | single plane (linear form) |
| 1 | 0 | — | double plane |

The degenerate cases (last five rows) are a measure-zero, rank-≤2 subset of the
9-dimensional quadric space — they are never reconstructed from nine generic
points, but they arise directly from a constructed plane-pair matrix, from the
pencil `Q₁ − λ Q₂` of two quadrics, or from an explicit `PlanePair` entity.

## 7. Code references

- `py/pytanga/quadric/conic.py::_classify_quadric` — rank/`rq` split above.
- `py/pytanga/quadric/refine.py::_plane_pair_from_quadric` — §3.
- `py/pytanga/quadric/refine.py::_parallel_plane_pair_from_quadric` — §4.
- `py/pytanga/quadric/refine.py::_plane_from_homogeneous` — plane vector → `Plane`.
- `py/pytanga/quadric/_create.py::create_plane_pair` / `create_parallel_plane_pair` —
  the inverse round-trip (`p₁ p₂ᵀ + p₂ p₁ᵀ` and §4's matrix).

