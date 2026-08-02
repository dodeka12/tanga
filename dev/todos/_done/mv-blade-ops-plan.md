# MV Blade Ops — Implementation Plan

Expose the blade-level operations from `cpp/Tan.GA/MV_Blade_Ops.h` in pytanga.

Functions marked "Unsafe" are excluded per the task description.  
Functions are grouped by implementation complexity and dependency order.

---

## Functions to expose (safe variants only)

| # | C++ Function | Signature | Returns |
|---|-------------|-----------|---------|
| 1 | `InverseBlade` | `(wA)` | `TMultivector` |
| 2 | `PseudoInverseBlade` | `(wA)` | `TMultivector` |
| 3 | `FactorizeBlade` | `(wA)` | `std::vector<TMultivector>` |
| 4 | `Join` | `(wA, wB)` | `TMultivector` |
| 5 | `FactorizeVersor` | `(wV)` | `std::pair<TMultivector, std::vector<TMultivector>>` |
| 6 | `Project` (single) | `(wA, wN)` | `TMultivector` |
| 7 | `Project` (vector) | `(wN, vecwA)` → `(vecwC)` | `std::vector<TMultivector>` |
| 8 | `Reject` (single) | `(wA, wN)` | `TMultivector` |
| 9 | `Reject` (vector) | `(wN, vecwA)` → `(vecwC)` | `std::vector<TMultivector>` |

**Excluded "unsafe" functions:** `ProjectUnsafe` (both overloads), `RejectUnsafe` (both overloads).

---

## Implementation phases

### Phase 1: C++ binding template and codegen

All changes are in the binding pipeline: `_template.cpp` (new placeholders) and `_codegen.py` (new code-fragment generators).

#### Step 1.1 — Add `#include` to template
- **File:** `py/pytanga/_template.cpp`
- Add `#include "Tan.GA/MV_Blade_Ops.h"` alongside the existing includes.
- This is a one-line addition; no placeholder needed.

#### Step 1.2 — Add placeholders to template
- **File:** `py/pytanga/_template.cpp`
- Add these placeholder tokens in the body (near the existing Phase D / extended-ops blocks):
  - `{BLADE_INVERSE_DEF}`
  - `{BLADE_PSEUDO_INVERSE_DEF}`
  - `{BLADE_FACTORIZE_DEF}`
  - `{BLADE_JOIN_DEF}`
  - `{BLADE_FACTORIZE_VERSOR_DEF}`
  - `{BLADE_PROJECT_DEF}`
  - `{BLADE_PROJECT_VEC_DEF}`
  - `{BLADE_REJECT_DEF}`
  - `{BLADE_REJECT_VEC_DEF}`

#### Step 1.3 — Add Python code-fragment generators
- **File:** `py/pytanga/_codegen.py`
- In the `generate()` function, add calls to replace each new placeholder.
- The new functions are independent of dtype (they use the same template types `TDynMV`, `TBlade`, `TValue`), so they appear in **one place** after the existing line 70 (`template = template.replace("{OP_CONJ_DEF}", _op_conj_def())`).
- Add the following generator functions (each returns a string):

##### `_blade_inverse_def()` → fills `{BLADE_INVERSE_DEF}`
```cpp
m.def("blade_inverse", [](const TDynMV& a) {
    TDynMV c = Tan::GA::InverseBlade(a);
    c.Prune();
    return c;
}, py::arg("a"),
   "Compute the inverse of a blade: A^{-1} = reverse(A) / IP(A, reverse(A)).");
```

##### `_blade_pseudo_inverse_def()` → fills `{BLADE_PSEUDO_INVERSE_DEF}`
```cpp
m.def("blade_pseudo_inverse", [](const TDynMV& a) {
    TDynMV c = Tan::GA::PseudoInverseBlade(a);
    c.Prune();
    return c;
}, py::arg("a"),
   "Compute the pseudo-inverse of a blade: A^{-1} = conjugate(A) / IP(A, conjugate(A)).");
```

##### `_blade_factorize_def()` → fills `{BLADE_FACTORIZE_DEF}`
```cpp
m.def("blade_factorize", [](const TDynMV& a) {
    return Tan::GA::FactorizeBlade(a);
}, py::arg("a"),
   "Factorize a blade into k normalized grade-1 vectors. Returns a list of DynMV.");
```

##### `_blade_join_def()` → fills `{BLADE_JOIN_DEF}`
```cpp
m.def("blade_join", [](const TDynMV& a, const TDynMV& b) {
    TDynMV c = Tan::GA::Join(a, b);
    c.Prune();
    return c;
}, py::arg("a"), py::arg("b"),
   "Compute the join of two blades: the smallest-grade blade that contains both A and B.");
```

##### `_blade_factorize_versor_def()` → fills `{BLADE_FACTORIZE_VERSOR_DEF}`
```cpp
m.def("blade_factorize_versor", [](const TDynMV& a) {
    auto [wScale, vecFactors] = Tan::GA::FactorizeVersor(a);
    return py::make_tuple(wScale, vecFactors);
}, py::arg("a"),
   "Factorize a versor into (scale, [factor_vectors]).");
```

##### `_blade_project_def()` → fills `{BLADE_PROJECT_DEF}`
```cpp
m.def("blade_project", [](const TDynMV& a, const TDynMV& n) {
    TDynMV c = Tan::GA::Project(a, n);
    c.Prune();
    return c;
}, py::arg("a"), py::arg("n"),
   "Project a multivector onto a blade N_l: proj_N(A) = IP(IP(A, conj(N)), N).");
```

##### `_blade_project_vec_def()` → fills `{BLADE_PROJECT_VEC_DEF}`
```cpp
m.def("blade_project_vec", [](const std::vector<TDynMV>& vecA, const TDynMV& n) {
    std::vector<TDynMV> vecC;
    Tan::GA::Project(vecC, n, vecA);
    return vecC;
}, py::arg("vec_a"), py::arg("n"),
   "Project each multivector in vec_a onto blade n.");
```

##### `_blade_reject_def()` → fills `{BLADE_REJECT_DEF}`
```cpp
m.def("blade_reject", [](const TDynMV& a, const TDynMV& n) {
    TDynMV c = Tan::GA::Reject(a, n);
    c.Prune();
    return c;
}, py::arg("a"), py::arg("n"),
   "Compute the rejection from a blade N_l: rej_N(A) = A - proj_N(A).");
```

##### `_blade_reject_vec_def()` → fills `{BLADE_REJECT_VEC_DEF}`
```cpp
m.def("blade_reject_vec", [](const std::vector<TDynMV>& vecA, const TDynMV& n) {
    std::vector<TDynMV> vecC;
    Tan::GA::Reject(vecC, n, vecA);
    return vecC;
}, py::arg("vec_a"), py::arg("n"),
   "Compute the rejection of each multivector in vec_a from blade n.");
```

**Note on `py::make_tuple` with structured bindings:**  
pybind11 supports `py::make_tuple` with structured bindings from C++17. The line
`auto [wScale, vecFactors] = Tan::GA::FactorizeVersor(a);` works because
`FactorizeVersor` returns `std::pair<TMultivector, std::vector<TMultivector>>`.
The return `py::make_tuple(wScale, vecFactors)` produces a Python `tuple`.

---

### Phase 2: Python facade (`Algebra` + `MV`)

#### Step 2.1 — Add methods to `Algebra` class
- **File:** `py/pytanga/algebra.py`
- Add these methods on `Algebra`:

```python
def blade_inverse(self, blade: MV) -> MV:
    """Compute the proper inverse of a blade (caller must ensure input is a blade)."""
    return MV(self._mod.blade_inverse(blade._impl), self)

def blade_pseudo_inverse(self, blade: MV) -> MV:
    """Compute the pseudo-inverse of a blade (uses conjugate instead of reverse)."""
    return MV(self._mod.blade_pseudo_inverse(blade._impl), self)

def blade_factorize(self, blade: MV) -> list[MV]:
    """Factorize a blade into k normalized grade-1 vectors."""
    impls = self._mod.blade_factorize(blade._impl)
    return [MV(impl, self) for impl in impls]

def blade_join(self, a: MV, b: MV) -> MV:
    """Compute the join of two blades."""
    return MV(self._mod.blade_join(a._impl, b._impl), self)

def blade_factorize_versor(self, versor: MV) -> tuple[MV, list[MV]]:
    """Factorize a versor into (scale, factor_vectors)."""
    wScale_impl, vecFactors_impl = self._mod.blade_factorize_versor(versor._impl)
    return (MV(wScale_impl, self), [MV(impl, self) for impl in vecFactors_impl])

def blade_project(self, a: MV, blade: MV) -> MV:
    """Project a multivector onto a blade."""
    return MV(self._mod.blade_project(a._impl, blade._impl), self)

def blade_project_vec(self, mvs: list[MV], blade: MV) -> list[MV]:
    """Project each multivector in a list onto the same blade."""
    impls_in = [mv._impl for mv in mvs]
    impls_out = self._mod.blade_project_vec(impls_in, blade._impl)
    return [MV(impl, self) for impl in impls_out]

def blade_reject(self, a: MV, blade: MV) -> MV:
    """Compute the rejection of a multivector from a blade."""
    return MV(self._mod.blade_reject(a._impl, blade._impl), self)

def blade_reject_vec(self, mvs: list[MV], blade: MV) -> list[MV]:
    """Compute the rejection of each multivector in a list from the same blade."""
    impls_in = [mv._impl for mv in mvs]
    impls_out = self._mod.blade_reject_vec(impls_in, blade._impl)
    return [MV(impl, self) for impl in impls_out]
```

#### Step 2.2 — Add convenience methods on `MV` class
- **File:** `py/pytanga/mv.py`
- Add methods that delegate to Algebra:

```python
def blade_inverse(self) -> "MV":
    """Compute the proper inverse of this blade (caller must ensure self is a blade)."""
    return self._alg.blade_inverse(self)

def blade_pseudo_inverse(self) -> "MV":
    """Compute the pseudo-inverse of this blade."""
    return self._alg.blade_pseudo_inverse(self)

def blade_factorize(self) -> list["MV"]:
    """Factorize this blade into k normalized grade-1 vectors."""
    return self._alg.blade_factorize(self)

def blade_join(self, other: "MV") -> "MV":
    """Compute the join of self and other (both must be blades)."""
    return self._alg.blade_join(self, other)

def blade_factorize_versor(self) -> "tuple[MV, list[MV]]":
    """Factorize this versor into (scale, factor_vectors)."""
    return self._alg.blade_factorize_versor(self)

def project(self, blade: "MV") -> "MV":
    """Project this multivector onto a blade."""
    return self._alg.blade_project(self, blade)

def reject(self, blade: "MV") -> "MV":
    """Compute the rejection of this multivector from a blade."""
    return self._alg.blade_reject(self, blade)
```

---

### Phase 3: Tests

#### Step 3.1 — Create test file
- **File:** `py/tests/test_blade_ops.py`
- Port the tests from `cpp/Tan.App.Test/Test_MV_Blade_Ops.cpp`:
  - `Test_InverseBlade` → test `blade_inverse()` on e1 (E3)
  - `Test_InverseBlade_Bivector` → test `blade_inverse()` on e1^e2
  - `Test_PseudoInverseBlade` → test `blade_pseudo_inverse()` on e1
  - `Test_Project_Vector_onto_Bivector` → test `project()` of e1+e2 onto e1^e2
  - `Test_Reject_Vector_From_Bivector` → test `reject()` of e1+e2+e3 from e1^e2
  - `Test_Project_Reject_Reconstruction` → test project+reject == original
  - `Test_FactorizeBlade` → test `blade_factorize()` on e1^e2
  - `Test_Join` → test `blade_join()` on e1, e2
  - `Test_Join_Disjoint` → test `blade_join()` on e1, e3
  - `Test_FactorizeVersor` → test `blade_factorize_versor()` on e1*e2
  - `Test_FactorizeVersor_G5` → test `blade_factorize_versor()` on G(5) random versor

---

### Phase 4: Documentation

#### Step 4.1 — Update `docs/py/mv.md`
- Add entries for new blade ops in the Named Methods table:
  - `a.blade_inverse()` — Proper blade inverse
  - `a.blade_pseudo_inverse()` — Pseudo-inverse of a blade
  - `a.blade_factorize()` — Factorize blade into factor vectors
  - `a.blade_join(b)` — Join of two blades
  - `a.blade_factorize_versor()` — Factorize versor into (scale, factors)
  - `a.project(blade)` — Project onto blade
  - `a.reject(blade)` — Reject from blade

---

## Dependency ordering

```
Phase 1 (C++ binding template + codegen)
    │
    ▼
Phase 2 (Python facade)
    │
    ├──► Phase 3 (tests)
    └──► Phase 4 (docs)
```

Phase 1 must complete first, as it makes the C++ functions available to Python.
Phases 3 and 4 can be done in parallel after Phase 2.

---

## Verification

After all phases:
1. Run `uv run python -m pytest py/tests/test_blade_ops.py -v` — all tests pass.
2. Run existing test suite to ensure no regressions:
   - `uv run python -m pytest py/tests/ -v`
3. Manually verify with a quick smoke test:
   ```python
   import pytanga
   alg = pytanga.Algebra(3, 0)
   e1 = alg("e1")
   e2 = alg("e2")
   print(e1.blade_inverse())         # should be ~= e1
   print(e1.blade_join(e2))          # should be ~= e1^e2
   print(e1.blade_factorize())       # should be [e1]
   print(e1.project(alg("e1^e2")))   # should be ~= e1
   print(e1.reject(alg("e1^e2")))    # should be ~= 0
   ```

---

## Estimated effort

| Phase | Description | Effort |
|-------|-------------|--------|
| 1 | C++ binding template + codegen | ~1 h |
| 2 | Python facade (Algebra + MV) | ~30 min |
| 3 | Tests | ~1 h |
| 4 | Documentation | ~30 min |
| **Total** | | **~3 h** |

## Key integration points

- **Template placeholder pattern** follows the existing `{GP_REV_DEF}`, `{OP_CONJ_DEF}` style.
- **New placeholders** are injected in `_codegen.py:generate()` after line 70 (existing Phase D replacements).
- **No new `#include`** beyond `MV_Blade_Ops.h`; all needed types (`TDynMV`, `TBlade`, `TValue`) are already typedef'd in the template.
- **Vector return types** (`std::vector<TDynMV>`, `std::pair<...>`) are handled by pybind11's built-in STL converters (`pybind11/stl.h` is already included).