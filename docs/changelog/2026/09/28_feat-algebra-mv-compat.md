# Changes since version 2.12.1

## New Features

- **Cross-instance MV compatibility** — any two `Algebra` instances with the
  same `(dim, sig, dtype, modulus)` parameters are now interchangeable end to
  end: multivectors, `BladeMask`, `Expression`, `tensor`, `solver`, and
  `matrix` combine across equal-parameter instances instead of only the
  identical instance.
- **`Algebra.compare` / `__eq__` / `__hash__`** — a new equality API compares
  the algebra parameters `(dim, sig, dtype, modulus)`.  `opns`, `precision`,
  and display settings are intentionally excluded, so `==`, `in`, and dict/set
  keys now work on algebras.
