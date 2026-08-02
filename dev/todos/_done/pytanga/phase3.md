# Phase 3 — C++ Binding Template and Code Generator

**Overview plan:** [plan.md](plan.md)  
**Depends on:** Phase 0 (directory structure), Phase 2 (cmake file verified)  
**Required by:** Phase 4 (build driver calls `_codegen.generate()` then compiles the output)

---

## Goal

1. Write `pytanga/_template.cpp` — a pybind11 binding source file with
   placeholder tokens that is filled in per `(dim, sig, dtype)`.
2. Write `pytanga/_codegen.py` — substitutes those tokens to emit a concrete
   `.cpp` file for a given algebra.

---

## Placeholder tokens

| Token | Replaced with |
|---|---|
| `{DIM}` | integer dimension, e.g. `3` |
| `{SIG}` | unsigned integer signature, e.g. `0` |
| `{CTYPE}` | C++ value type, e.g. `double` |
| `{CONG_TYPE}` | congruence class type, e.g. `Tan::CCongruence_Float<double>` |
| `{CONG_INIT}` | congruence constructor expression, e.g. `{}` or `(modulus)` — see dtype map |
| `{MODULE_NAME}` | Python module name string, e.g. `binding_dim3_sig0_f64` |

---

## Steps

### 3.1 Write `pytanga/_template.cpp`

Key design decisions embedded in this file:

- `to_dict()` returns `std::map<uint32_t, {CTYPE}>` which pybind11 converts to
  `dict[int, <value>]` automatically via `#include <pybind11/stl.h>`.
- `from_dict()` accepts the same type.
- `gp`, `op`, `ip` all call `Prune()` on the result before returning, so
  near-zero coefficients (floating-point rounding noise) are discarded.
- `inv` for float types uses `Tan::CCongruence_Float<CTYPE>` (default-
  constructed). For integer types `{CONG_INIT}` is `(modulus)` where `modulus`
  is an extra parameter added to the `inv` lambda.
- `EResult` is checked and a `std::runtime_error` is thrown on failure;
  pybind11 converts this to a Python `RuntimeError`.

```cpp
// @@AUTO-GENERATED — do not edit; see pytanga/_codegen.py@@
// Algebra: G({DIM}, {SIG})  dtype: {CTYPE}
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <map>
#include <stdexcept>
#include <cstdint>

#include "Tan.GA/DynamicMultivector.h"
#include "Tan.GA/MV_Operators.h"
#include "Tan.GA/Algo.h"
#include "Tan.Math/Congruence.h"

namespace py = pybind11;

using TBlade = Tan::GA::CBlade<{DIM}, {SIG}>;
using TDynMV = Tan::GA::CDynamicMultivector<{CTYPE}, TBlade>;
using TCong  = {CONG_TYPE};

PYBIND11_MODULE({MODULE_NAME}, m)
{
    // -----------------------------------------------------------------------
    // Module-level constants
    // -----------------------------------------------------------------------
    m.attr("VECTOR_SPACE_DIM") = static_cast<unsigned>(TBlade::VectorSpaceDimension);
    m.attr("ALGEBRA_DIM")      = static_cast<unsigned>(TBlade::AlgebraDimension);
    m.attr("SIGNATURE")        = static_cast<unsigned>(TBlade::VectorSpaceSignature);
    m.attr("PSEUDOSCALAR_ID")  = static_cast<unsigned>(TBlade::PseudoScalarId);

    // -----------------------------------------------------------------------
    // DynMV class
    // -----------------------------------------------------------------------
    py::class_<TDynMV>(m, "DynMV")
        .def(py::init<>())

        // set / get a single blade coefficient by its uint32 blade-id
        .def("set", [](TDynMV& mv, uint32_t id, {CTYPE} val) {
            mv.SetValueBlade(val, TBlade(id));
        }, py::arg("blade_id"), py::arg("value"))

        .def("get", [](const TDynMV& mv, uint32_t id) -> {CTYPE} {
            {CTYPE} val{};
            mv.GetValueBlade(val, TBlade(id));
            return val;
        }, py::arg("blade_id"))

        // export all non-zero entries as dict[int, <value>]
        .def("to_dict", [](const TDynMV& mv) {
            std::map<uint32_t, {CTYPE}> d;
            mv.ForEachBlade([&](const {CTYPE}& v, const TBlade& bl) {
                d[bl.GetId()] = v;
            });
            return d;
        })

        // overwrite from dict[int, <value>]; clears existing entries first
        .def("from_dict", [](TDynMV& mv, const std::map<uint32_t, {CTYPE}>& d) {
            mv.Reset();
            for (const auto& kv : d) {
                mv.SetValueBlade(kv.second, TBlade(kv.first));
            }
        }, py::arg("coeffs"))

        .def("blade_count", [](const TDynMV& mv) {
            return mv.GetBladeCount();
        })

        .def("reset", [](TDynMV& mv) { mv.Reset(); })
        .def("prune", [](TDynMV& mv) { mv.Prune(); });

    // -----------------------------------------------------------------------
    // Free functions
    // -----------------------------------------------------------------------
    m.def("gp", [](const TDynMV& a, const TDynMV& b) {
        TDynMV c;
        Tan::GA::GP(c, a, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"),
       "Geometric product: a * b");

    m.def("op", [](const TDynMV& a, const TDynMV& b) {
        TDynMV c;
        Tan::GA::OP(c, a, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"),
       "Outer (wedge) product: a ^ b");

    m.def("ip", [](const TDynMV& a, const TDynMV& b) {
        TDynMV c;
        Tan::GA::IP(c, a, b);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"),
       "Inner product: a | b");

{INV_DEF}
}
```

The `{INV_DEF}` placeholder is replaced by `_codegen.py` with one of two
variants depending on dtype (see step 3.2).

**`inv` for float dtypes** (`float32`, `float64`):

```cpp
    m.def("inv", [](const TDynMV& a) -> TDynMV {
        TDynMV result;
        TCong cong;
        auto r = Tan::GA::Inverse(result, a, cong);
        if (r != Tan::GA::EResult::Success) {
            throw std::runtime_error("Multivector is not invertible");
        }
        result.Prune();
        return result;
    }, py::arg("a"), "Multiplicative inverse");
```

**`inv` for integer dtypes** (`int32`, `int64`):

```cpp
    m.def("inv", [](const TDynMV& a, {CTYPE} modulus) -> TDynMV {
        TDynMV result;
        TCong cong(modulus);
        auto r = Tan::GA::Inverse(result, a, cong);
        if (r != Tan::GA::EResult::Success) {
            throw std::runtime_error("Multivector is not invertible (modulus=" +
                                     std::to_string(modulus) + ")");
        }
        result.Prune();
        return result;
    }, py::arg("a"), py::arg("modulus"), "Modular multiplicative inverse");
```

### 3.2 Write `pytanga/_codegen.py`

```python
"""Generate a concrete pybind11 binding .cpp for a given (dim, sig, dtype)."""

from __future__ import annotations
import re
from pathlib import Path

# Map dtype string → (C++ type, congruence type, inv_variant)
# inv_variant is 'float' or 'int'
_DTYPE_MAP: dict[str, tuple[str, str, str]] = {
    "float32": ("float",    "Tan::CCongruence_Float<float>",    "float"),
    "float64": ("double",   "Tan::CCongruence_Float<double>",   "float"),
    "int32":   ("int32_t",  "Tan::CCongruence_HMod<int32_t>",   "int"),
    "int64":   ("int64_t",  "Tan::CCongruence_HMod<int64_t>",   "int"),
}

_TEMPLATE_PATH = Path(__file__).parent / "_template.cpp"

_INV_FLOAT = '''    m.def("inv", [](const TDynMV& a) -> TDynMV {
        TDynMV result;
        TCong cong;
        auto r = Tan::GA::Inverse(result, a, cong);
        if (r != Tan::GA::EResult::Success) {
            throw std::runtime_error("Multivector is not invertible");
        }
        result.Prune();
        return result;
    }, py::arg("a"), "Multiplicative inverse");'''

_INV_INT = '''    m.def("inv", [](const TDynMV& a, {CTYPE} modulus) -> TDynMV {
        TDynMV result;
        TCong cong(modulus);
        auto r = Tan::GA::Inverse(result, a, cong);
        if (r != Tan::GA::EResult::Success) {
            throw std::runtime_error("Multivector is not invertible (modulus=" +
                                     std::to_string(modulus) + ")");
        }
        result.Prune();
        return result;
    }, py::arg("a"), py::arg("modulus"), "Modular multiplicative inverse");'''


def module_name(dim: int, sig: int, dtype: str) -> str:
    """Return the Python module name for this (dim, sig, dtype) triplet."""
    short = {"float32": "f32", "float64": "f64", "int32": "i32", "int64": "i64"}
    return f"binding_dim{dim}_sig{sig}_{short[dtype]}"


def generate(dim: int, sig: int, dtype: str, out_path: Path) -> None:
    """Write a concrete binding .cpp to *out_path*."""
    if dtype not in _DTYPE_MAP:
        raise ValueError(f"Unknown dtype {dtype!r}. Choose from {list(_DTYPE_MAP)}")
    if dim < 1 or dim > 32:
        raise ValueError(f"dim must be in [1, 32]")
    if sig >= (1 << dim):
        raise ValueError(f"sig={sig} has bits set outside the {dim}-bit range")

    ctype, cong_type, inv_variant = _DTYPE_MAP[dtype]
    mod_name = module_name(dim, sig, dtype)

    template = _TEMPLATE_PATH.read_text(encoding="utf-8")

    inv_def = (_INV_FLOAT if inv_variant == "float" else _INV_INT).replace(
        "{CTYPE}", ctype
    )

    result = (
        template
        .replace("{DIM}",         str(dim))
        .replace("{SIG}",         str(sig))
        .replace("{CTYPE}",       ctype)
        .replace("{CONG_TYPE}",   cong_type)
        .replace("{MODULE_NAME}", mod_name)
        .replace("{INV_DEF}",     inv_def)
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result, encoding="utf-8")
```

### 3.3 Verify generated output by inspection

Generate a `.cpp` for `G(3,0)` with `float64` and inspect it:

```python
from pathlib import Path
from pytanga._codegen import generate
generate(3, 0, "float64", Path("/tmp/check_dim3_sig0_f64.cpp"))
```

Open the file and confirm:
- The `CBlade<3, 0>` type alias is present.
- `PYBIND11_MODULE(binding_dim3_sig0_f64, m)` is the module declaration.
- The `inv` variant has no `modulus` parameter (float path).
- All `{...}` tokens have been replaced — run a regex check:
  ```python
  import re
  src = Path("/tmp/check_dim3_sig0_f64.cpp").read_text()
  assert not re.search(r'\{[A-Z_]+\}', src), "Unreplaced tokens found"
  ```

Generate one for `G(3,0)` with `int64` and confirm the `inv` signature
includes `modulus`.

---

## Completion check

- [x] `pytanga/_template.cpp` exists and contains all six `{TOKENS}`
- [x] `pytanga/_codegen.py` is fully implemented
- [x] `_codegen.generate(3, 0, "float64", ...)` produces a `.cpp` with no
  unreplaced tokens
- [x] `_codegen.generate(3, 0, "int64", ...)` produces a `.cpp` with the
  `modulus` parameter in `inv`
- [x] `_codegen.module_name(3, 0, "float64")` == `"binding_dim3_sig0_f64"`
