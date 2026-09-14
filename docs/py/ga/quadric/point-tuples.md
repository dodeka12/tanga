# Point tuples — the 7→8 point effect

A set of `k` points can be represented as their **join** — the outer product of
their embeddings — and recovered from that blade by dualising to the space of
quadrics through the points.  In the 3D quadric space this has a subtle
consequence: a join of **seven** points returns **eight**.

## The Veronese embedding

Points are rank-1 symmetric matrices (see [Conic space](conic-space.md)): a
point `x` is `x xᵀ`, so the image of P² (resp. P³) under the complete linear
system of quadrics is the Veronese variety.

## The dual correspondence (join ↔ net)

The join of `k` points is the `k`-dimensional subspace spanned by their
embeddings.  Its orthogonal complement (Frobenius inner product
`<A,B> = tr(AᵀB)`) is the `(N−k)`-dimensional space of quadrics **through** the
`k` points, where `N = 6` (Q2) or `N = 10` (Q3):

```text
span{ x1x1ᵀ, …, xk xkᵀ }^⊥ = { Q : xiᵀ Q xi = 0 for all i }
```

So the dual of a `k`-point join is the IPNS space of quadrics vanishing on those
points, and the points are the common base points of any generating set of that
space.  Analysing the blade (`analyze_entity`, or `Geometry.analyze`) returns a
`PointSet` of those points.

## Recovering points: dual → intersect → filter

Because three quadrics in P³ meet in **eight** base points (two conics in P²
meet in four), recovery is a three-step process:

1. **Dual** the blade to its complement `span{Q1, …, Q_{N−k}}` of quadrics
   through the points.
2. **Intersect** three generic combinations `g1, g2, g3` of those quadrics —
   up to eight base points (the `k` join points are a subset).
3. **Filter** the candidates to those on *all* complement quadrics; for `k < 7`
   this selects exactly the `k` join points.

For Q2 (`k = 3, 4`) step 2 is `two_conic_intersection`; for Q3 it is
`intersect_three_quadrics`.

## The `k = 7 → 8` Cayley–Bacharach phenomenon

For `k = 7`, the complement is a **3-dimensional net** of quadrics through the
seven points, and a generic triple in it has **eight** base points — the seven
originals plus one further point.  This is the Cayley–Bacharach theorem in P³:
seven points in general position do *not* impose independent conditions on
quadrics; the net they span determines an **eighth** point.  Consequently the
analysis of a grade-7 join returns **eight** points, not seven.

The IPNS dualise step handles this identically: the grade-3 IPNS net dualises to
the grade-7 OPNS join, so both representations carry the same eighth point.

## Relation to Perwass's conic method

Perwass's `ConicIntersect.tex` intersects two conics through the eigen-
decomposition of `M = B⁻¹A` — each real eigenvalue yields a degenerate conic
that factors into lines.  The quadric work here is the same idea lifted one
dimension: a degenerate conic (line pair) becomes a degenerate quadric (plane
pair / cone), and the point-tuple complement net is intersected in triples.

## See Also

- [Conic space & visualization](conic-space.md) — embedding, reconstruction, rendering
- `dev/theory/quadric-point-tuples.md` — the full derivation
- `py/examples/ga/quadric/point_tuples_demo.py` — a runnable demonstration
