# Changes since version 0.9.2

## Bug Fixes
- **macOS (Apple Clang/libc++) precompiled-wheel build fails with an ambiguous
  `operator-`** — the generic `operator-`/`operator+` templates in
  `MV_Operators.h` were unconstrained and therefore matched arbitrary types via
  argument-dependent lookup. When `std::vector<TMultivector>::erase` (used by
  the new `Join`) computed `__position - cbegin()` under libc++, both the
  standard iterator `operator-` and `Tan::GA::operator-` were viable, producing
  a compile error on `macos-14-arm64`. The operators are now SFINAE-constrained
  to true multivector types (those exposing the `TValue` and `TBlade` nested
  types), so the standard iterator `operator-` is selected unambiguously and the
  macOS wheel build compiles again.
