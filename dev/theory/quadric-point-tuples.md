<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2021 Christian Perwass (author) -->

# Point tuples in the quadric spaces — the dual/net correspondence

This note is the theory reference for the point-tuple analysis in
`pytanga.quadric` (`_analysis.py` grade dispatch, `_pointset.py` point
recovery, `_intersection.py` two- and three-quadric intersection).  It explains
why a `k`-point *join* (outer product of `k` point embeddings) in the 2D conic
space Q2 or the 3D quadric space Q3 is recovered as a set of points by
dualizing to the space of quadrics through those points and intersecting a
generic triple of them — the same "thesis pencil method" Perwass uses for two
conics, lifted one dimension and to three quadrics.

## 1. The Veronese embedding: points are rank-1 matrices

The quadric spaces embed a point as the symmetric rank-1 matrix `x xᵀ`, rescaled
so the Euclidean inner product with a quadric coefficient vector is `½ xᵀ Q x`:

* **Q2** (2D conics, dim 6): `p = (x, y)` ↦
  `(x, y, √2/2, √2/2·x², √2/2·y², xy)`.
* **Q3** (3D quadrics, dim 10): `p = (x, y, z)` ↦
  `(x, y, z, √2/2, √2/2·x², √2/2·y², √2/2·z², xy, xz, yz)`.

These are exactly the **Veronese** (moment) embeddings: the image of P² (resp.
P³) under the complete linear system of quadrics.  A point is a *rank-1*
symmetric matrix; recovering the points of a blade is recovering the rank-1
matrices in the blade's subspace.

## 2. The dual correspondence (join ↔ net)

The join of `k` points is the `k`-dimensional subspace spanned by their
embeddings.  Its orthogonal complement (Frobenius inner product
`⟨A, B⟩ = tr(AᵀB)`) is the `(N−k)`-dimensional space of quadrics *through* the
`k` points, where `N = 6` (Q2) or `N = 10` (Q3):

```
span{ x₁x₁ᵀ, …, x_kx_kᵀ }^⊥  =  { Q : xᵢᵀ Q xᵢ = 0 for all i }
```

So the dual of a `k`-point join is the (IPNS) space of quadrics vanishing on
those points.  Conversely, the points are the common base points of any
generating set of that space.  In the code this is the *orthogonal complement*
via SVD (`_points_from_join_via_conics` for Q2, `_points_from_join_via_quadrics`
for Q3): factor the blade, stack the embeddings, and take the right singular
vectors of the gram matrix.

## 3. Recovering points: dual → intersect → filter

Because **three** quadrics in P³ meet in **eight** base points (and two conics
in P² meet in four), the recovery is:

1. **Dual** the blade to its complement `span{Q₁, …, Q_{N−k}}` of quadrics
   through the points.
2. **Intersect** three generic combinations `g₁, g₂, g₃` of those quadrics —
   this yields up to eight base points (of which the `k` join points are a
   subset).
3. **Filter** the candidate points to those lying on *all* complement quadrics;
   for `k < 7` this selects exactly the `k` join points.

For Q2 (`k = 3, 4`) step 2 is `two_conic_intersection` (the thesis pencil
method).  For Q3 it is `intersect_three_quadrics`.

## 4. Intersecting three quadrics

`intersect_three_quadrics(Q₁, Q₂, Q₃)` reduces to the two-quadric machinery and
locates `Q₃ = 0` along the quartic `Q₁ ∩ Q₂`:

* **Plane-pair member.** If the pencil `span{Q₁, Q₂}` has a rank-2 (plane-pair)
  degenerate member, the quartic factors into two plane-conics; restricting
  `Q₃` to each plane and intersecting the two conics (Perwass's pencil method)
  is *exact*.
* **Cone member.** Generically the pencil has a rank-3 *cone* member; the
  quartic is sampled through the cone's rulings and every sample is
  Newton-refined to the common `Q₁ = Q₂ = Q₃ = 0` zero (a residual check
  discards non-convergent seeds).  Trying several pairings and several random
  triplets (in the point-recovery layer) makes a bad quartic sampling in one
  instance unable to hide a point.

### The net method (and why the code uses the pencil)

The classical *net* method intersects three quadrics through the **rank-2
(plane-pair) members of the 3-dimensional net** `span{Q₁, Q₂, Q₃}` — the
singular points of the discriminant quartic
`det(λ₁Q₁ + λ₂Q₂ + λ₃Q₃) = 0`.  Factoring one plane-pair member into its two
planes and intersecting the plane-conics recovers all eight points exactly, with
no sampling.

However, the plane-pair members are real only in special configurations: for a
generic net (e.g. the complement of seven generic points) the singular points of
the discriminant are **complex**, so no real plane-pair exists to factor.  The
cone members of a *pencil*, by contrast, are generically real.  This is why the
working implementation uses the pencil (cone) reduction; the net method is
documented here as the exact refinement for the real case.

## 5. The `k = 7 → 8` Cayley–Bacharach phenomenon

For `k = 7`, the complement is a **3-dimensional net** of quadrics through the
seven points, and a generic triple in it has **eight** base points: the seven
originals plus one further point.  This is the Cayley–Bacharach theorem in
P³: a seven-point set in general position lies on a net, and that net determines
an eighth point (the seven points do *not* impose independent conditions on
quadrics — they span a P⁶ that meets the Veronese 3-fold in eight rank-1
points).  Consequently `pointset_from_blade` returns **eight** points for a
grade-7 join, not seven; the IPNS dualize step handles this identically (the
grade-3 IPNS net dualizes to the grade-7 OPNS join).

## 6. Relation to Perwass's conic method

Perwass's `ConicIntersect.tex` intersects two conics `A, B` through the
eigen-decomposition of `M = B⁻¹A`: each real eigenvalue `λ` yields the
degenerate conic `C = A − λB`, which factors into (real) lines, and intersecting
those lines with `A` recovers the intersection points.  The quadric work here is
exactly this lifted one dimension:

* degenerate conic (line pair) → degenerate quadric (plane pair / cone);
* two-conic pencil → two-quadric pencil (and its degenerate members);
* and, for point tuples, the *complement* net is intersected in triples, which
  is the same "factor a degenerate member, then intersect with one of the
  originals" idea applied to three quadrics.

