# Changes since version 2.9.0 (2.10.0-rc1)

## New Features

- **GA-only quadric API** — the `pytanga.quadric` public surface is now
  GA-centric: `BasisQ2`/`BasisQ3`, the `Conic`/`Quadric3D` entities, and the
  `analyze_*` entry points.  Conic/quadric fitting, the cone lift, and
  conic/quadric intersection are expressed with `geo(...)` + the GA operations
  (`op`/`join`/`meet`/`gp`, `dual`, `sp`) + `analyze`/`refine`; the raw
  coefficient/matrix/fit/intersection helpers (`to_coeffs`/`from_coeffs`,
  `embed_point`, `conic_from_points*`, `quadric_from_points*`, `line_from_points`,
  `cone_from_conic`, `fit_singular_values`/`fit_nullity`, `intersect_quadrics`,
  `two_conic_intersection`, …) are now private (`_`-prefixed) or removed.
- **GA sequence products** — `pytanga.algebra.op` / `join` / `meet` / `gp` fold a
  sequence of multivectors (e.g. `join([geo(Point(*p)) for p in pts])`).
- **Matrix-accepting `Conic` / `Quadric3D`** — both entities now accept a
  symmetric 3×3 / 4×4 matrix (`np.ndarray` or `pytanga.geometry.Matrix`) in
  addition to the coefficient vector, and expose `to_matrix()` (satisfying
  `MatrixProvider`).
- **Cone lift from a base conic** — `BasisQ3(c)` relabels a Q2 conic onto the
  cone quadric slots (`CONE_BLADE_MAP`), and `geo(Translator(apex))` moves the
  apex — a rank-3 cone.
- **Tolerance-aware conic/quadric analysis** — `Geometry(algebra, tol=…)` /
  settable `Geometry.tol` and `Geometry.refine(..., tol=…)` (plus
  `Conic.refine` / `Quadric3D.refine`) classify within a tolerance, so a noisy
  near-cone quadric is recognized as a `Cone`.
- **Operator translation as a linear-map expression** — `geo(Translator(t))`
  returns a linear-map `Expression` for `BasisQ2`/`BasisQ3` (where translation has
  no versor), applied by contraction (`trans(conic)` / `trans.evaluate(conic)` /
  `trans @ conic`), plus a public `linear_map(matrix, out_mask, var_name,
  var_mask)` factory and a single-variable positional apply on `Expression`.
- **`Hyperboloid` / `Paraboloid` entities** — new axis-aligned quadric entities
  (`Hyperboloid(center, semi_axes, sheets=1|2)` and
  `Paraboloid(vertex, semi_axes, is_hyperbolic=…)`), created with `geo(...)` and
  positioned with `geo(Translator(...))`.
- **`@` operator applies a single-variable expression** — `expr @ value` is
  shorthand for `expr.evaluate(value)` for a single-variable expression, so a
  translation linear map applies naturally as `T @ q`.

## Bug Fixes

- **Expression-solver null space** — `Expression.lstsq` / `Expression.svd` (and
  the `AffineExpression` twins) now use `full_matrices=True`, so a homogeneous
  solve of an *underdetermined* (wide) linear system returns the true null-space
  vector instead of silently returning an arbitrary smallest-singular-vector
  solution.
