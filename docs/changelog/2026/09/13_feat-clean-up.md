# Changes since version 2.3.0 (2.4.0-rc1)

## Bug Fixes
- **`solver_basics_01.py` always failed its own check** — the two inverse paths
  (`solve()` vs the explicit `product_matrix` + `np.linalg.solve`) agree only to
  floating-point precision, but the example compared their coefficient dicts
  with `==`; it now checks the blade sets match and compares the coefficients
  with `np.allclose`.
