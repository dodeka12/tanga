# Changes since version 0.11.0

## New Features
- **Variable/expression system** — a symbolic layer for composing GA equations
  where only a few elements change.  `Variable` (a named slot with a fixed
  `BladeMask`) combines with constants and other variables via `*`/`|`/`^` to
  build an `Expression`, a reduced product tensor with one axis per variable.
  Expressions evaluate against bound `MV`s (or lists of `MV`s for batched
  results), support addition/subtraction over a shared variable set, and expose
  reverse/Clifford-conjugate involutions.
- **Vectorized batch MV↔tensor conversion** — `to_tensor`/`from_tensor` now use
  new C++ `to_matrix_batch`/`from_matrix_batch` bindings, collapsing per-MV
  Python+C++ calls into a single C++ call.  Batched expression evaluation is
  now ~1.8× faster than a Python loop of fresh products.
- **Expression inverse** — `Expression.inv(name)` returns the inverse linear map
  of a single-variable, square, invertible expression as a new expression, for
  solving `y = E(x)` back to `x`.
- **Partial evaluation & named counting axes** — `Expression(...)` now accepts a
  subset of variables, returning a new `Expression` over the remaining variables
  (enabling Jacobians), and a batch may be bound with an explicit counting-axis
  label via `E(V1=("n", [x0, x1]))`.
- **Repeated variables (polynomial forms)** — a variable may appear up to
  `MAX_DEGREE` (4) times per product term (`v * v`, `v * v * v`).  Each
  `Variable` owns a contiguous block of labels, so identically-shaped terms
  merge under `+`/`-` (`v*v + v*v == 2·(v*v)`, `v*v - v*v == 0`).
- **`AffineExpression`** — adding/subtracting expressions that cannot be
  broadcast-merged (differing variable sets, occurrence degrees, or constants)
  now returns an `AffineExpression` instead of raising; products distribute
  over its terms and evaluation sums them per term.
- **Interruptible custom animation loops** — `Visualizer.interrupted()` reports
  whether Ctrl+C / SIGTERM has been received, and `Visualizer.sleep_ms(ms)` now
  returns `False` early when interrupted (instead of blindly sleeping), so
  user-defined nested animation loops can break out cleanly.  (`sleep_ms` is no
  longer a `@staticmethod`; it now returns a `bool`.)
- **Geometry-derived variable blade masks** — `Geometry.mask_for(typ)` returns
  the `BladeMask` a geometric entity/operator type occupies in the bound
  algebra (derived from the creation pipeline, so it respects OPNS/IPNS and the
  per-algebra support matrix), and `Geometry.create_var(name, typ)` wraps it in
  an expression-system `Variable`.  `Geometry.__call__` also accepts a
  `(name, type)` pair (`geo("R1", Rotor)`).
- **Expression least-squares solve** — `Expression.lstsq(rhs=None)` solves a
  single-variable expression as a linear system, returning the
  smallest-singular-vector solution for homogeneous fittings (e.g. line
  incidence ``P ^ L = 0``) or a `numpy.linalg.lstsq` solution given an explicit
  right-hand side.
- **Expression SVD** — `Expression.svd()` returns the descending singular
  values of a single-variable expression's linear map together with the
  corresponding right-singular vectors as `MV`s over the variable's blade
  mask.

## Bug Fixes
- **Snapshot export default camera matches the live view** — the exported HTML
  auto-fit (no `camera=` config) 3D camera now keeps its orbit target at the
  world origin and recomputes `near`/`far` from scene scale, so snapshots frame
  scenes identically to the live viewer instead of centering on the bounding box.
