# Changes since version 2.3.0 (2.4.0-rc1)

## Bug Fixes
- **`solver_basics_01.py` always failed its own check** — the two inverse paths
  (`solve()` vs the explicit `product_matrix` + `np.linalg.solve`) agree only to
  floating-point precision, but the example compared their coefficient dicts
  with `==`; it now checks the blade sets match and compares the coefficients
  with `np.allclose`.

## Refactor
- **Ratchet the `py/tests` ANN gate** — the existing unannotated test code now
  carries per-line `# noqa: ANN…` directives (added with
  `ruff check --add-noqa`, ~2 600 directives across 124 files), and `ANN` was
  removed from the `py/tests/**` per-file-ignores.  The current baseline passes,
  while **new** test functions must be annotated to pass `ruff check` (the
  star-import `F403`/`F405` debt stays blanket-ignored).
