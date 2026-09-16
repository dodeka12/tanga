# Changes since version 2.4.1

## New Features
- **Detached scene-subtree insertion** — `VizGroup`/`VizSceneObject` trees can
  now be composed before a `Visualizer`/`Scene` exists and inserted in one step
  via `viz.add(group)`/`viz.new(group)`; `Scene.add_subtree` registers every
  descendant, auto-generates omitted ids, and backfills partial per-kind styles,
  so each part stays individually addressable afterwards.
- **`analyze_operator(expect=…)` hint** — `analyze_operator`, `analyze`, and the
  `Geometry` facade accept an optional expected operator type, coercing a
  half-turn reflection to the requested rotation (a 3D `ReflectionLine` or a 2D
  `ReflectionPoint` → `GeneralRotor`/`Rotor`) instead of failing downstream.
- **Named GA product functions on the expression system** — `gp`, `ip`, `op`,
  `vp`, `nvp`, `sp`, `cp`, `acp`, and `rc` are now available as methods on
  `Variable`/`Expression`/`AffineExpression` and as module-level functions in
  `pytanga.expression`, accepting a constant multivector, a variable, or an
  expression as either operand (including a constant multivector as the
  caller).  `sp` returns a `float`/`int` when fully bound (matching the
  multivector dtype), and `nvp` requires a constant versor.
- **Variable renaming and unifying** — `Expression.bind(X=X)` (a `Variable`
  value), `rename_var(old, new_name)`, and `unify([e1, e2], X=X, Y=X)` re-key
  independently-created variables onto one canonical variable so their
  expressions merge under `+`; the target mask must match the source mask.
