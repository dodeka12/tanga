# Changes since version 0.9.2

## New Features
- **`meet` operator** — `Algebra.meet(a, b)` / `MV.meet(other)` computes the
  meet (intersection) of two blades: `dual(join(dual(A), dual(B)))`, i.e. the
  largest-grade blade contained in both.
- **Windows MSVC auto-detection for the JIT compile path** — `_build.py` now
  locates MSVC itself (via `vswhere`) and sources `vcvars64.bat` automatically,
  so JIT-compiling an algebra binding no longer requires the Developer Command
  Prompt for VS.

## Breaking Changes
- **`blade_join` renamed to `join`** — the join operator is now
  `Algebra.join(a, b)` / `MV.join(other)` (the `blade_` prefix is dropped), and
  the new meet is exposed as `meet` rather than `blade_meet`.

## Bug Fixes
- **`join` hangs on non-unit blades** — `ProjectUnsafe` computed the projection
  as `IP(IP(A, conjugate(N)), N)` without normalizing by the blade's
  (pseudo-)norm, so the rejection of a vector already lying inside a non-unit
  blade never vanished and `GA::Join`'s loop spun forever (e.g.
  `Join(e1+e2, e3)`). The projection now uses the conjugate-based pseudo-inverse
  `conjugate(N) / IP(N, conjugate(N))`, which fixes the infinite loop and also
  makes null blades (e.g. `e_inf`) invertible in degenerate metrics.
- **`meet` with the pseudoscalar raises a runtime error** — `meet(A, I)` (and
  `meet(I, I)`) crashed because the signed dual of the pseudoscalar is a scalar
  (grade 0), which `Join` cannot factorize into vectors. `Join` now
  short-circuits when either blade is a scalar, returning the other blade.
- **`join` of conformal (N3) sphere vectors returned a trivector** — for a
  non-degenerate blade in a mixed-signature metric the conjugate-based
  pseudo-inverse `conjugate(N) / IP(N, conjugate(N))` is an inverse only w.r.t.
  the inner product, not the geometric product, so `ProjectUnsafe`'s projection
  landed in the wrong direction and `GA::Join` grew an extra grade (two IPNS
  spheres produced a trivector instead of a bivector). `ProjectUnsafe` now uses
  the true inverse `reverse(N) / IP(N, reverse(N))` for non-degenerate blades
  and only falls back to the pseudo-inverse for null blades (which have no
  geometric inverse). The pseudo-inverse / `project` / `reject` docs now state
  this inner-product-only distinction explicitly.
- **`join` throws for null conformal vectors (points)** — `Join` rejected each
  factor from `J` using projection and rejection, which is undefined for a null
  blade (a conformal point squares to zero), so `join(p1, p2)` for two points
  threw `PseudoInverseBlade: Blade is not pseudo-invertible`. `Join` now uses
  the metric-free wedge test `J ^ n_j == 0` to decide containment, which works
  for null blades too.
- **`blade_factorize` returned mixed-grade factors for null blades** — the
  projection-based factorization used the pseudo-inverse for null blades,
  returning a mixed-grade (grade 1 + 3) first factor and failing to reconstruct
  the blade (e.g. `t ^ e_inf`). `FactorizeBlade` now extracts factors
  metric-free: it probes coordinate blades `E << B` for a factor (Option A),
  with a Gaussian-elimination null-space fallback (Option B), and peels each
  factor off with a partner vector, `B = (b << B) / (a . b)`. `FactorizeVersor`
  now also selects non-null factors (by geometric norm) so its geometric-product
  peel does not vanish, and falls back to a unit scale when a versor has no
  non-null factor (e.g. a single null vector). This fixes `meet` of null blades
  (e.g. two points).
