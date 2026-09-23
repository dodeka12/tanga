# Conic & quadric space — analysis and visualization

This page describes the mathematics behind `pytanga.quadric`: how a 2D conic or a
3D quadric is represented in a projective geometric algebra, how an MV is analyzed
into a concrete entity, and how that entity is turned into geometry the viewer can
draw.

## The projective quadric space

A conic is the zero set of a symmetric quadratic form in the affine plane, and a
quadric the zero set of a symmetric quadratic form in affine 3-space:

$$A(x) = x^{\mathsf T} A\,x = 0, \qquad A = \begin{bmatrix} Q & b \\ b^{\mathsf T} & c \end{bmatrix}.$$

Perwass's *conic space* linearises this: the symmetric matrix becomes a vector,
so conics (and quadrics) live in a linear space that a geometric algebra can act
on. `pytanga.quadric` uses

- `BasisQ2` — conic space `CA{6}`, a 6-dimensional algebra (`Algebra(6, 0)`),
- `BasisQ3` — quadric space `CA{10}`, a 10-dimensional algebra (`Algebra(10, 0)`),

(the 6 and 10 are exactly the number of independent symmetric-matrix entries).
Perwass's original bases are non-Euclidean; here they are **rescaled to a
Euclidean metric** so the plain `Algebra(6,0)` / `Algebra(10,0)` product can be
used unchanged. The `√2/2` factors that the rescaling introduces appear *only* in
`_embedding.py` (point embedding) and `_mapping.py` (matrix ↔ coefficients); every
other module works with the Euclidean basis `b₁…b₆` / `b₁…b₁₀`.

## Representation: symmetric matrix ↔ coefficients

`_to_coeffs` / `_from_coeffs` are exact inverses and fix the coefficient order:

- conic (3×3): `(a₁₃, a₂₃, (√2/2)a₃₃, (√2/2)a₁₁, (√2/2)a₂₂, a₁₂)`
- quadric (4×4): `(q₁₄, q₂₄, q₃₄, (√2/2)q₄₄, (√2/2)q₁₁, (√2/2)q₂₂, (√2/2)q₃₃, q₁₂, q₁₃, q₂₃)`

`Conic` / `Quadric3D` are thin dataclasses over that vector: `matrix` rebuilds the
symmetric matrix, and the classification properties read the affine block form
`[[Q, b], [bᵀ, c]]`.

## Point embedding

A point is embedded as the rank-1 outer product $x\,x^{\mathsf T}$, expressed in
the coefficient basis:

- 2D: `x b₁ + y b₂ + (√2/2) b₃ + (√2/2)x² b₄ + (√2/2)y² b₅ + xy b₆`
- 3D: `x b₁ + y b₂ + z b₃ + (√2/2) b₄ + (√2/2)x² b₅ + (√2/2)y² b₆ + (√2/2)z² b₇ + xy b₈ + xz b₉ + yz b₁₀`

The rescaling makes the basis pairing exact:

$$\bigl\langle \operatorname{coeff}(A),\; \operatorname{embed}(x) \bigr\rangle = \tfrac{1}{2}\, x^{\mathsf T} A\, x,$$

so "the point lies on the conic" is the **inner product being zero**. This is the
identity that makes the whole analysis work: a conic's coefficients and a point's
embedding are dual, and the incidence relation is a scalar product.

## OPNS, IPNS and grade dispatch

The same conic/quadric can be represented in two dual ways:

- **OPNS** — the *outer product null space*: blades that pass through a point
  (the point embedding `embed(x)` is a grade-1 OPNS blade), and a point set is the
  join (wedge) of its points.
- **IPNS** — the *inner product null space*: the conic/quadric itself is a grade-1
  blade (its coefficient vector), and a point is incident when the inner product
  with it vanishes.

The two are related by duality. `analyze_entity` normalises IPNS input to OPNS by
dualising first, then dispatches on the blade grade:

| space | OPNS grade | entity |
| --- | --- | --- |
| Q2 (conic) | 1 | `Point` |
| Q2 | 2, 3, 4 | `PointSet` |
| Q2 | 5 | `Conic` |
| Q3 (quadric) | 1 | `Point` |
| Q3 | 2…7 | `PointSet` |
| Q3 | 8 | degenerate quadric intersection → `PlaneConicPair` / `Curve` |
| Q3 | 9 | `Quadric3D` |

For Q3 **IPNS** the dispatch dualises to OPNS first (so grade $k$ IPNS maps to
grade $10-k$ OPNS and every grade routes through the same OPNS table above);
e.g. IPNS grade 1 → `Quadric3D`, grade 2 → the quadric intersection, grade 9 →
`Point`. Coefficients below the algebra precision are pruned first, so numerical
residue from a versor product (e.g. a rotated quadric carrying `~1e-12` in lower
grades) does not misclassify as a mixed-grade MV.

A `PointSet` is recovered through the **dual/net correspondence**: the join of
`k` points is dual to the $(N-k)$-dim space of conics/quadrics through them, and
three generic members of that space meet in eight (Q3) / four (Q2) base points,
of which the `k` join points are the subset lying on *all* members. For `k = 7`
in Q3 this yields eight points — the seven originals plus the Cayley–Bacharach
partner of the 3-dim net (see `dev/theory/quadric-point-tuples.md`).


## Classification and refinement

Given the matrix $A = \begin{bmatrix} Q & b \\ b^{\mathsf T} & c\end{bmatrix}$,
the entity is classified by **rank and inertia**, not by solving anything:

- $\operatorname{rank} A$ gives the coarse family; $\operatorname{rank} Q$ splits
  it further (e.g. a rank-3 conic is a *parabola* when $\operatorname{rank} Q = 1$
  and an *ellipse*/*hyperbola* when $\operatorname{rank} Q = 2$);
- the inertia `(n⁺, n⁻, n⁰)` of $A$ distinguishes real from imaginary and splits
  the hyperboloid families;
- `center` solves $Q\,c = -b$; `eigenvalues` / `principal_directions` are the
  eigen-decomposition of $Q$; the semi-axis along an eigenvector $v_i$ is
  $\sqrt{-f'/\lambda_i}$ with $f' = c + b^{\mathsf T}c$ (Perwass's conic analysis).

`refine()` maps a classified matrix to a specific entity — `Circle`, `Ellipse`,
`Hyperbola`, `Parabola`, `LinePair`, `Ellipsoid`, `Cone`, `PlanePair`, … The
**degenerate** cases are factored rather than fitted: a rank-2 matrix is a plane
pair whose two homogeneous plane vectors are
$\sqrt{\lambda_+}\,v_+ \pm \sqrt{-\lambda_-}\,v_-$ from the eigen-decomposition
(the 2D analogue gives a `LinePair`), and a rank-1 quadratic part gives a
*parallel* plane/line pair.

## Two-quadric intersection

Two quadrics span a **pencil** $\{Q_1 - \lambda Q_2\}$ of quadrics through their
common curve. Every member is a quadric of the same projective type, and the curve
is easiest to read off the **degenerate** members — those of rank ≤ 3:

- a **rank-2** member factors into two planes; intersecting each plane with the
  *other* quadric gives two conics (a `PlaneConicPair`);
- a **rank-3 cone** member is a *ruled surface*: writing a generator as
  $x(\tau) = v + \tau\,d$ (through the apex $v$), the companion quadric becomes a
  quadratic $a\tau^2 + b\tau + c = 0$ whose roots are the curve points. Sweeping
  the generator over the cone's base conic traces the **quartic** intersection
  curve, split into arcs where the discriminant changes sign.

That quartic is generally **unbounded**: it tends to infinity where the generator
is asymptotic to the companion quadric. Those directions are solved analytically —
substituting the base-conic parametrisation into $d^{\mathsf T}q_Q d = 0$ gives a
quadratic in $(\cos\theta, \sin\theta)$, i.e. a **quartic in $\tan(\theta/2)$** —
and each real direction is then sampled out to a `±extent` clip box with a
geometric ladder of small $\theta$-offsets, while the bounded body is sampled at a
low resolution. The result is an on-curve, finite polyline (a `Curve`) that still
reaches the view box.

Where the two generators of the pencil are *both* singular and through the origin
(a rotated exact cube, for instance), the generalised-eigenvalue path degenerates;
a homogeneous cubic $\det(A - \lambda B) = 0$ on the 3×3 quadratic parts recovers
the rank-2 plane-pair members instead. If the pencil has **no real degenerate
member**, the intersection is an elliptic hard case and is not resolved.

## Rotation rotor

Rotations act on the quadric space as versors $A \mapsto R A \tilde R$.
`create_rotor` builds $R$ from an angle and axis, and `analyze_rotor` inverts it
back to `Rotor(angle, axis)`:

- **Q2**: $R = R_2 R_1$ with $R_1 = \cos\theta - \tfrac{\sqrt2}{2}\sin\theta\,(b_4\wedge b_6 - b_5\wedge b_6)$
  and $R_2 = \cos(\theta/2) - \sin(\theta/2)\,b_1\wedge b_2$ (the axis is implicit —
  rotation in the $b_1b_2$ plane);
- **Q3**: three commuting factors $R_{\text{lin}} \cdot R_{\text{mixed}} \cdot R_{\text{quad}}$
  acting on the linear, mixed-quadratic and traceless-quadratic monomials at rates
  $\theta, \theta, 2\theta$.

The rotor is an even versor (grades 0, 2, 4 in Q2; 0, 2, 4, 6 in Q3) and is
independent of the OPNS/IPNS flag. Analysis sandwiches the **linear** basis blades
only (the other factors commute with them), so the rotation matrix — and hence the
angle and axis — is read off directly. The full derivations live in
`dev/notes/quadric-rotor-derivation.md` and `dev/notes/quadric-plane-pair-derivation.md`.

## Translation (linear map)

Rotations act as versors (`A ↦ R A R̃`), but the quadric space has **no translator
versor** — translation of a conic/quadric is an *affine* map on the coefficient
vector, not an isometry.  `geo(Translator(t))` therefore returns a **linear-map
`Expression`** for `BasisQ2`/`BasisQ3` (built with
`pytanga.expression.linear_map`) instead of an MV, applied by contraction:

```python
geo = Geometry(BasisQ3())
trans = geo(Translator(Direction(1, -2, 3)))   # a linear-map Expression
cone = trans.evaluate(cone_at_origin)           # translate the cone
```

The translation matrix is `coeffs(Hᵀ Q H) = M_t · coeffs(Q)` with `H = [[I, −t],[0,1]]`,
computed by applying `Q ↦ Hᵀ Q H` to each coefficient basis vector.  This is the
"algebraic way to specify the apex" of a cone: `q3(base)` gives the cone with apex
at the origin, and `geo(Translator(apex))` moves it.

## Visualization

Conics and quadrics reach the viewer as concrete entities:

- A **`Quadric3D`** renders through the analytic **ray** path (`RayStyle`): the
  frontend intersects the view ray with the quadric in the fragment shader, with a
  bounding-box proxy that writes `gl_FragDepth`.
- **Conic/curve entities** (`Ellipse`, `Hyperbola`, `Parabola`, `LinePair`,
  `PlaneConic`, `PlaneConicPair`, `Curve`, …) are **sampled** on the Python side
  into ordered polylines (one polyline per connected component, so the frontend
  never draws a spurious chord between branches) and streamed to per-kind
  renderers: `curve.js`, `plane_pair.js`, and the 2D conic renderers. Unbounded
  2D conics (hyperbolas, parabolas, lines) are clipped to a spatial `extent`
  rather than an unbounded parameter range.

Because the sampled geometry is just polylines, adding a new quadric entity only
requires a `refine`/`create` branch, a style, a serializer, and a renderer — see
[Viz architecture](../architecture/viz-architecture.md) for the frontend extension recipe.


