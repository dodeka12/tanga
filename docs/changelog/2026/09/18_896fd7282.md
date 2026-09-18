# Changes since version 2.7.0

## New Features
- **`BladeMask` named bases** — `BladeMask` now carries an ordered named basis
  alongside its raw blade ids: `basis_vectors` / `basis_names` read it (falling
  back to the raw blades), `with_basis(...)` attaches a reduced direction set,
  and `basis_matrix()` returns the raw→named change-of-basis matrix.  The
  algebra display basis (e.g. `einf`/`eo` for N3) is auto-attached when it covers
  the mask, composed names expand in string parsing (`"e1 + einf"`), and
  `union`/`intersection` are basis-aware (`intersection(other,
  discard_basis=…)`).
- **`get_tensor()` / `MVTensor.get_array()`** — `Expression.get_tensor()` and
  `AffineExpression.get_tensor()` return the raw `MVTensor` (one raw `BladeMask`
  per dimension), and `MVTensor.get_array()` recombines those axes into their
  named bases (`out_basis`/`axis_bases` overrides), replacing the
  per-canonical-basis-blade evaluation loop with a tensor-native combination.
- **`TwistBivector` named basis** — `mask_for(TwistBivector)` (N3) now carries
  its 6 physical DOF directions (`e12, e13, e23, e1∧e∞, e2∧e∞, e3∧e∞`) over the
  9 raw twist blades, so a twist variable's `get_tensor().get_array()` yields a
  6-column operator matrix directly.
- **Per-algebra `mask_for` named bases** — every supported geometry type in
  E2/E3/P2/P3/N2/N3/PGA2/PGA3 now exposes a named basis via `mask_for` (the
  algebra display basis auto-attached, with a per-algebra `basis_for_<type>`
  hook for reduced physical bases), pinned by `test_geometry_mask.py`.

## Bug Fixes
- **`mask_for` now returns hard-coded full type masks** — the previous
  instance-template derivation could drop a blade when the sample values landed
  on a zero coefficient (e.g. N2 `Sphere`/`Circle`/`Inversion`), producing a
  partial mask.  Each `create_*` module now declares the full blade set per type
  via `mask_for_<type>(basis)`, respecting `basis.opns`.
