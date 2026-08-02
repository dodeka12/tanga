# PyTanga — Implementation Plan (Overview)

Python bindings for TanGA using on-demand pybind11 compilation.  
Each `(dim, sig, dtype)` triplet is compiled once, cached in `~/.cache/pytanga/`,
and loaded instantly on subsequent uses.

See [architecture notes](#architecture-notes) below for key constraints that
shape every phase.

---

## Phases

| # | Phase | Detail | Done |
|---|---|---|---|
| 0 | Repository scaffolding | [phase0.md](phase0.md) | [ ] |
| 1 | Pure-Python blade name utilities | [phase1.md](phase1.md) | [ ] |
| 2 | Binding CMake infrastructure | [phase2.md](phase2.md) | [ ] |
| 3 | C++ binding template and code generator | [phase3.md](phase3.md) | [ ] |
| 4 | Build driver | [phase4.md](phase4.md) | [ ] |
| 5 | Cache layer | [phase5.md](phase5.md) | [ ] |
| 6 | Python facade | [phase6.md](phase6.md) | [ ] |
| 7 | Tests | [phase7.md](phase7.md) | [ ] |
| 8 | Polish / optional extensions | [phase8.md](phase8.md) | [ ] |

Phases are strictly ordered: each phase depends only on work completed in
earlier phases. Phase 1 (pure Python, no C++) can be developed and tested
independently of phases 2–6.

---

## Architecture notes

**Compile-time algebra shape.**  
`CBlade<Dim, Sig>` fixes the algebra via template parameters. Changing either
value produces an incompatible C++ type, so each `(dim, sig, dtype)` triplet
requires a separate compiled module.

**Header-only GA engine.**  
`Tan.GA` is 100% template headers. A generated binding `.cpp` needs only
`#include` those headers; no pre-built GA library is required.

**Small set of required `.cpp` files.**  
Only three tanga `.cpp` files contain non-template definitions that the binding
needs at link time:
- `Tan.Math/ValuePrecision.cpp` — `template<>` specialisations of
  `CValuePrecision<T>::DefaultPrecision()` for float, double, int, int64_t, etc.
- `Tan.Core/ValueFormatString.cpp` — `template<>` specialisations of
  `ValueFormatString<T>()`, pulled in transitively through `Matrix.Operators.h`.
- `Tan.Math/Matrix.Enum.cpp` — non-template `Tan::ToString(EMatrixResult)`.

These three files are compiled **directly into each generated binding** via the
binding CMakeLists.txt (phase 2). No separate shared library is needed.

**Sparse runtime representation.**  
`CDynamicMultivector` stores coefficients in `std::map<TBlade, TValue>`. Only
non-zero blades consume memory, so high-dimensional algebras stay practical.

**Congruence types.**  
`Tan::CCongruence_Float<T>` is used for floating-point inversion (identity map,
reciprocal for inverse). `Tan::CCongruence_HMod<T>` is used for integer
modular arithmetic (requires a modulus value). The dtype governs which is wired
into the binding template.

---

## Toolchain

| Tool | Role |
|---|---|
| **uv** | Package manager and virtual-environment runner |
| **hatchling + hatch-vcs** | Build backend with VCS-derived versioning |
| **GCC / g++** | C++ compiler for all binding compilation |
| **CMake ≥ 3.18** | Build system for binding modules |

## Dependency summary

| Dependency | Why | Install |
|---|---|---|
| `hatchling` | Build backend | declared in `[build-system]` — uv resolves automatically |
| `hatch-vcs` | Dynamic version from git tags | declared in `[build-system]` — uv resolves automatically |
| `pybind11` | C++/Python bridge | `uv add --optional build "pybind11>=2.11"` |
| `cmake ≥ 3.18` | Build system | `uv add --optional build "cmake>=3.18"` or system |
| `ninja` (optional) | Faster builds | `uv add --optional build ninja` or system |
| `pytest` | Test runner | `uv add --dev pytest` |

Install everything at once: `uv sync --all-extras`

No other Python runtime dependencies are required.
