<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2021 Christian Perwass (author) -->

# Q2 conic → Q3 cone lift — derivation

This note derives the `CONE_BLADE_MAP` blade relabel that lifts a 2D conic into a
3D cone quadric (apex at the origin, base conic in the plane `z = 1`).  It is the
reference the `pytanga.quadric` docstrings cite (the code mirrors it in
`_basis.py::CONE_BLADE_MAP`, `_basis.py::BasisQ3.__call__` and
`_create.py::cone_from_conic`).

## 1. The cone over a base conic

A 2D conic is a symmetric 3×3 matrix `C` with

```
[u v 1] C [u v 1]ᵀ = a₁₁ u² + 2a₁₂ uv + a₂₂ v² + 2a₁₃ u + 2a₂₃ v + a₃₃ = 0
```

The cone with apex at the origin whose cross-section in the plane `z = 1` is `C`
is the set of `(x, y, z)` whose homogeneous projection `(u, v) = (x/z, y/z)` lies
on `C`.  Substituting and multiplying by `z²`:

```
a₁₁ x² + 2a₁₂ xy + a₂₂ y² + 2a₁₃ xz + 2a₂₃ yz + a₃₃ z² = 0
```

i.e. the symmetric 4×4 quadric

```
Q₀ = [[a₁₁, a₁₂, a₁₃, 0],
      [a₁₂, a₂₂, a₂₃, 0],
      [a₁₃, a₂₃, a₃₃, 0],
      [  0,   0,   0, 0]]
```

with the homogeneous last row/column zero (the apex at the origin).

## 2. The coefficient relabel (`CONE_BLADE_MAP`)

The Q2 conic coefficient vector (`_mapping.py`) is

```
(a₁₃, a₂₃, (√2/2)a₃₃, (√2/2)a₁₁, (√2/2)a₂₂, a₁₂)      on blades b₁…b₆
```

and the Q3 quadric coefficient vector is

```
(q₁₄, q₂₄, q₃₄, (√2/2)q₄₄, (√2/2)q₁₁, (√2/2)q₂₂, (√2/2)q₃₃, q₁₂, q₁₃, q₂₃)
```

Comparing `Q₀` to this ordering, the conic's coefficients land on the quadric's
slots as

| Q2 blade (id) | conic coeff  | →  | Q3 blade (id) | quadric coeff |
|---------------|--------------|----|---------------|---------------|
| `b₁` (1)      | `a₁₃`        | →  | `b₉` (256)    | `q₁₃`         |
| `b₂` (2)      | `a₂₃`        | →  | `b₁₀` (512)   | `q₂₃`         |
| `b₃` (4)      | `(√2/2)a₃₃`  | →  | `b₇` (64)     | `(√2/2)q₃₃`   |
| `b₄` (8)      | `(√2/2)a₁₁`  | →  | `b₅` (16)     | `(√2/2)q₁₁`   |
| `b₅` (16)     | `(√2/2)a₂₂`  | →  | `b₆` (32)     | `(√2/2)q₂₂`   |
| `b₆` (32)     | `a₁₂`        | →  | `b₈` (128)    | `q₁₂`         |

with `q₁₄ = q₂₄ = q₃₄ = q₄₄ = 0`.  This is `CONE_BLADE_MAP`
`{1:256, 2:512, 4:64, 8:16, 16:32, 32:128}` — the general `Algebra.embed` /
`MV.to_algebra` blade-map primitive applied to the canonical Q2→Q3 injection
(also exposed as `BasisQ3(c)`).

## 3. Translating to a general apex

For a general apex `v`, translate the origin cone `Q₀` by `v`; in the affine block
form `Q = [[q, -q v], [(-q v)ᵀ, vᵀ q v]]` where `q = Q₀[:3,:3]` is the quadratic
part.  This is exactly `_create.py::_centered_matrix(q, v, 0)`, which
`cone_from_conic` applies after the relabel.  The right-circular `create_cone` is
the special case of a circle base conic `diag(1, 1, -1)`; `refine_quadric`'s
`_cone_from_quadric` is the inverse (it recovers the apex and, for a right
circular cone, the axis and half-angle).

## 4. Code references

- `py/pytanga/quadric/_basis.py::CONE_BLADE_MAP` / `BasisQ3.__call__` — §2.
- `py/pytanga/quadric/_create.py::cone_from_conic` — §2 + §3.
- `py/pytanga/algebra/_algebra.py::Algebra.embed` / `_mv.py::MV.to_algebra` — the
  general blade-map primitive.
