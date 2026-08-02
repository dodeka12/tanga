# MV Operators — Python Mapping Plan

Map additional C++ multivector operators from `cpp/Tan.GA/MV_Operators.h`
to the Python layer (`py/pytanga/mv.py`, `py/pytanga/algebra.py`,
`py/pytanga/_codegen.py`, `py/pytanga/_template.cpp`).

---

## 1. Current State

### 1.1 C++ operators defined in `MV_Operators.h`

The header defines a generic `Product()` infrastructure and concrete
functions in `Tan::GA` namespace:

| # | C++ Symbol | Signature / Purpose |
|---|---|---|
| P1 | `GP` | `GP(C, A, B)` — geometric product |
| P2 | `GP_Congruence` | `GP(C, A, B, cong)` — GP with congruence transform |
| P3 | `GP_Reverse` | `GP_Reverse(C, A, revA, B, revB)` — GP with optional reverse on either operand |
| P4 | `GP_Conjugate` | `GP_Conjugate(C, A, conjA, B, conjB)` — GP with optional conjugate on either operand |
| P5 | `IP` | `IP(C, A, B)` — inner (left-contraction) product |
| P6 | `IP_Reverse` | `IP_Reverse(C, A, revA, B, revB)` — IP with optional reverse |
| P7 | `IP_Conjugate` | `IP_Conjugate(C, A, conjA, B, conjB)` — IP with optional conjugate |
| P8 | `OP` | `OP(C, A, B)` — outer (wedge) product |
| P9 | `OP_Reverse` | `OP_Reverse(C, A, revA, B, revB)` — OP with optional reverse |
| P10 | `OP_Conjugate` | `OP_Conjugate(C, A, conjA, B, conjB)` — OP with optional conjugate |
| P11 | `VersorProduct` | `VersorProduct(C, versor, B)` — versor·b·rev(versor) |
| P12 | `VersorProduct` (vec) | `VersorProduct(vecC, versor, vecB)` — apply to multiple MVs |
| P13 | `SP` | `SP(value, A, B)` — scalar product (scalar part of GP) |
| P14 | `GetReverse` / `Reverse` | Reverse a multivector in-place or return copy |
| P15 | `GetConjugate` / `Conjugate` | Clifford conjugate in-place or return copy |
| P16 | `GetCongruence` / `Congruence` | Apply congruence transformation to all coefficients |
| P17 | `GetInverseCongruence` / `InverseCongruence` | Apply inverse congruence transformation |
| P18 | `Dual` | `Dual(B, A)` — compute dual of A into B |
| P19 | `GetGradeProjection` / `GradeProjection` | Project to a specific grade k |
| P20 | `GreatestCommonDenominator` | GCD of all coefficients (integer algebras) |
| P21 | `MagnitudeSquared` | Sum of squared coefficients |
| P22 | `Magnitude` | sqrt(MagnitudeSquared) |
| P23 | `Scalar` | Extract the scalar coefficient |
| P24 | `IsScalar` | True if only the scalar blade is non-zero |
| P25 | `IsZero` | True if all blades are zero |
| P26 | `ProjectTo` | Project coefficients of A to blade set present in B |
| P27 | `ConvertMultivectorType` | Copy between different MV types |
| P28 | `Add` / `Sub` | `Add(C, A, B)` / `Sub(C, A, B)` — component-wise |
| P29 | `operator+` / `operator-` | C++ operator overloads (various type combos) |
| P30 | `operator*` / `operator/` | Scalar multiply / divide |
| P31 | `operator%` | Scalar modulus (coefficient-wise modulo) |

### 1.2 Already exposed in Python

| C++ Function | Python Binding (`_template.cpp`) | Python MV / Algebra method |
|---|---|---|
| `GP` | `m.def("gp", …)` (float) / `m.def("gp", …)` + `m.def("gp_mod", …)` (int) | `alg.gp()`, `MV.__mul__`, `MV.gp()`, `MV.gp_mod()` |
| `GP_Congruence` | only used inside `gp_mod` (int) | `alg.gp_mod()` |
| `IP` | `m.def("ip", …)` (+ `ip_mod` for int) | `alg.ip()`, `MV.__or__`, `MV.ip()`, `MV.ip_mod()` |
| `OP` | `m.def("op", …)` (+ `op_mod` for int) | `alg.op()`, `MV.__xor__`, `MV.op()`, `MV.op_mod()` |
| `GetReverse` | `m.def("rev", …)` | `alg.rev()`, `MV.rev()` |
| `GetConjugate` | `m.def("conj", …)` | `alg.conj()`, `MV.conj()` |
| `VersorProduct` (single) | `m.def("vp", …)` | `alg.vp()`, `MV.vp()` |
| `Congruence` | `m.def("reduce", …)` (int only) | `alg.reduce()`, `MV.reduce()` |
| `Add` | `m.def("add", …)` | `alg.add()`, `MV.__add__` |
| `Sub` | `m.def("sub", …)` | `alg.sub()`, `MV.__sub__` |
| `operator-` (unary neg) | `m.def("neg", …)` | `alg.neg()`, `MV.__neg__` |
| `operator*` (scalar) | `m.def("scale", …)` | `alg.scale()`, `MV.__mul__` / `__rmul__` (scalar path) |
| Inverse | `m.def("inv", …)` | `alg.inv()`, `MV.inv()`, `MV.__invert__` |
| nvp (normalized VP) | — (pure Python via gp+inv) | `alg.nvp()`, `MV.nvp()` |

**Total already bound: 14 C++ functions**

---

## 2. Gap Analysis — Not Yet Exposed

### 2.1 High-value (direct GA operations, user-facing)

| C++ Symbol | Priority | Notes |
|---|---|---|
| `GP_Reverse` | ★★★ | `gp(a.rev(), b)`, `gp(a, b.rev())`, `gp(a.rev(), b.rev())` — frequently needed. Can be achieved by calling `rev()` then `gp()` in Python, but a single C++ call avoids an intermediate copy. |
| `GP_Conjugate` | ★★☆ | Same pattern as `GP_Reverse` but with conjugation. Lower demand than reverse. |
| `IP_Reverse` | ★★☆ | IP with reversion on operands. |
| `IP_Conjugate` | ★☆☆ | IP with conjugation on operands. |
| `OP_Reverse` | ★★☆ | OP with reversion on operands. |
| `OP_Conjugate` | ★☆☆ | OP with conjugation on operands. |
| `SP` (scalar product) | ★★★ | Scalar product $A * B$ (only the scalar part of the GP). Common in GA computations — relates to angle/distance. |
| `Dual` | ★★★ | Compute the dual $\star A = A \cdot I^{-1}$. Fundamental GA operation. |
| `GetGradeProjection` / `GradeProjection` | ★★★ | Extract grade-k part $\langle A \rangle_k$. Used in almost every GA application. |
| `MagnitudeSquared` | ★★☆ | Sum of squared coefficients — frequent in numerical work. |
| `Magnitude` | ★★☆ | sqrt of magnitude squared. |
| `Scalar` | ★★★ | Extract scalar coefficient — extremely common. |
| `IsScalar` | ★☆☆ | Boolean check. Trivial to do in Python but nice for completeness. |
| `IsZero` | ★★★ | Boolean check — very common. |
| `ProjectTo` | ★★☆ | Project coefficients onto blade set of another multivector. |

### 2.2 Niche / internal (lower priority, or easy Python-side workaround)

| C++ Symbol | Priority | Notes |
|---|---|---|
| `VersorProduct` (vector overload) | ★☆☆ | Batch versor product. Can be done with a Python list comprehension. |
| `GetCongruence` / `GetInverseCongruence` | ★☆☆ | Already have `reduce()` for the HMod case. Only needed if custom congruences are to be supported. |
| `GreatestCommonDenominator` | ★☆☆ | Integer-only. Can be computed in Python with `math.gcd` over coefficients. |
| `ConvertMultivectorType` | ★☆☆ | Internal — needed when mixing `_CMultivector` and `CDynamicMultivector`. Not needed from Python since we always use `DynMV`. |
| `operator%` (modulus) | ★☆☆ | Coefficient-wise modulo. Python can call `reduce()`. |

---

## 3. Implementation Plan

### 3.1 Binding layer — new `m.def()` entries in `_template.cpp`

For each new C++ function, add a `m.def()` block in the template and a
corresponding fragment generator in `_codegen.py`.

#### Phase A: Grade projection & scalar extraction

| # | Binding name | C++ call | Python-side method |
|---|---|---|---|
| A1 | `grade_proj` | `Tan::GA::GetGradeProjection(a, grade)` | `MV.grade(grade)` |
| A2 | `scalar` | `Tan::GA::Scalar(a)` | `MV.scalar()` (property) |

These are the most-requested missing operations. They are pure functions
that take a single MV and return either a new MV or a scalar value.

**`_codegen.py` fragment** (float, shared by int):
```python
def _grade_proj_def() -> str:
    return """
    m.def("grade_proj", [](const TDynMV& a, unsigned grade) {
        TDynMV c = Tan::GA::GetGradeProjection(a, grade);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("grade"),
       "Extract grade-k part <A>_k.");
"""

def _scalar_def() -> str:
    return """
    m.def("scalar", [](const TDynMV& a) -> CTYPE {
        return Tan::GA::Scalar(a);
    }, py::arg("a"),
       "Return the scalar coefficient of a.");
"""
```

> **Note:** `_scalar_def` returns a scalar value (not an MV). The C++
> `Scalar()` function returns `TValue`. The binding returns a Python
> `float` or `int`.

**`_codegen.py` integration:** Add `{GRADE_PROJ_DEF}` and `{SCALAR_DEF}`
placeholders to `generate()`, and always inject them (same for float and int).

#### Phase B: Dual, magnitude, zero-check

| # | Binding name | C++ call | Python-side method |
|---|---|---|---|
| B1 | `dual` | `Tan::GA::Dual(c, a)` | `MV.dual()` |
| B2 | `magnitude_sq` | `Tan::GA::MagnitudeSquared(a)` | `MV.mag2()` (property) |
| B3 | `magnitude` | `Tan::GA::Magnitude(a)` | `MV.mag()` (property) |
| B4 | `is_zero` | `Tan::GA::IsZero(a)` | `MV.is_zero()` (property) |

**`_codegen.py` fragments:**
```python
def _dual_def() -> str:
    return """
    m.def("dual", [](const TDynMV& a) {
        TDynMV c;
        Tan::GA::Dual(c, a);
        c.Prune();
        return c;
    }, py::arg("a"),
       "Compute the dual ★A = A · I⁻¹.");
"""

def _magnitude_sq_def() -> str:
    return """
    m.def("magnitude_sq", [](const TDynMV& a) -> CTYPE {
        return Tan::GA::MagnitudeSquared(a);
    }, py::arg("a"),
       "Return sum of squared coefficients.");
"""

def _magnitude_def() -> str:
    return """
    m.def("magnitude", [](const TDynMV& a) -> double {
        return Tan::GA::Magnitude(a);
    }, py::arg("a"),
       "Return sqrt(sum of squared coefficients).");
"""

def _is_zero_def() -> str:
    return """
    m.def("is_zero", [](const TDynMV& a) -> bool {
        return Tan::GA::IsZero(a);
    }, py::arg("a"),
       "Return True if all blades are zero.");
"""
```

#### Phase C: Scalar product, project-to, is-scalar

| # | Binding name | C++ call | Python-side method |
|---|---|---|---|
| C1 | `sp` | `Tan::GA::SP(value, a, b)` | `MV.sp(other)` |
| C2 | `project_to` | (no direct C++ free function; calls `MV::ProjectTo` or manual) | `MV.project_to(other)` |
| C3 | `is_scalar` | `Tan::GA::IsScalar(a)` | `MV.is_scalar()` (property) |

**SP note:** The C++ `SP()` writes to a reference `TValue&`. The binding
returns the scalar directly:
```python
def _sp_def() -> str:
    return """
    m.def("sp", [](const TDynMV& a, const TDynMV& b) -> CTYPE {
        CTYPE val{};
        Tan::GA::SP(val, a, b);
        return val;
    }, py::arg("a"), py::arg("b"),
       "Scalar product (scalar part of geometric product).");
"""
```

**ProjectTo note:** The C++ `ProjectTo()` is `void ProjectTo(wA, wB)` and
it zeros A first then copies matching blades from B. This is effectively
"restrict A to the blade set of B". The binding would look like:
```python
def _project_to_def() -> str:
    return """
    m.def("project_to", [](const TDynMV& a, const TDynMV& b) {
        TDynMV c;
        c.SetValuePrecision(a.GetValuePrecision());
        Tan::GA::ProjectTo(c, a);  // init c with structure of a
        b.ForEachBlade([&](const CTYPE& val, const TBlade& bl) {
            CTYPE existing{};
            if (c.GetValueBlade(existing, bl)) {
                c.SetValueBlade(val, bl);
            }
        });
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("b"),
       "Return a projected onto the blade set of b (retain only blades present in b).");
"""
```

> **Alternative:** The C++ `ProjectTo(wA, wB)` zeros `wA` first, then
> copies matching blades from `wB`. But if we want the non-destructive
> version (return a new MV), we can either call `ConvertMultivectorType`
> first or write the loop manually as shown above. We should verify the
> exact semantics desired: "restrict A's coefficients to blades that exist
> in B" vs "copy B's coefficients into A's blade structure".

#### Phase D: GP/IP/OP with reverse/conjugate flags

| # | C++ call | Binding name | Python MV method |
|---|---|---|---|
| D1 | `GP_Reverse` | `gp_rev` | `gp_rev(other, rev_self=False, rev_other=False)` |
| D2 | `GP_Conjugate` | `gp_conj` | `gp_conj(other, conj_self=False, conj_other=False)` |
| D3 | `IP_Reverse` | `ip_rev` | `ip_rev(other, rev_self=False, rev_other=False)` |
| D4 | `IP_Conjugate` | `ip_conj` | `ip_conj(other, conj_self=False, conj_other=False)` |
| D5 | `OP_Reverse` | `op_rev` | `op_rev(other, rev_self=False, rev_other=False)` |
| D6 | `OP_Conjugate` | `op_conj` | `op_conj(other, conj_self=False, conj_other=False)` |

These follow the same pattern. For each product type P ∈ {GP, IP, OP} and
involution type I ∈ {Reverse, Conjugate}, bind with two boolean flags.

```python
def _gp_rev_def() -> str:
    return """
    m.def("gp_rev", [](const TDynMV& a, bool revA, const TDynMV& b, bool revB) {
        TDynMV c;
        Tan::GA::GP_Reverse(c, a, revA, b, revB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("rev_a"), py::arg("b"), py::arg("rev_b"),
       "Geometric product with optional reverse on operands.");
"""
```

**`_codegen.py` fragments for all six variants:**
```python
def _gp_rev_def() -> str:
    return """
    m.def("gp_rev", [](const TDynMV& a, bool revA, const TDynMV& b, bool revB) {
        TDynMV c;
        Tan::GA::GP_Reverse(c, a, revA, b, revB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("rev_a"), py::arg("b"), py::arg("rev_b"),
       "Geometric product with optional reverse on operands.");
"""

def _gp_conj_def() -> str:
    return """
    m.def("gp_conj", [](const TDynMV& a, bool conjA, const TDynMV& b, bool conjB) {
        TDynMV c;
        Tan::GA::GP_Conjugate(c, a, conjA, b, conjB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("conj_a"), py::arg("b"), py::arg("conj_b"),
       "Geometric product with optional conjugate on operands.");
"""

def _ip_rev_def() -> str:
    return """
    m.def("ip_rev", [](const TDynMV& a, bool revA, const TDynMV& b, bool revB) {
        TDynMV c;
        Tan::GA::IP_Reverse(c, a, revA, b, revB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("rev_a"), py::arg("b"), py::arg("rev_b"),
       "Inner product with optional reverse on operands.");
"""

def _ip_conj_def() -> str:
    return """
    m.def("ip_conj", [](const TDynMV& a, bool conjA, const TDynMV& b, bool conjB) {
        TDynMV c;
        Tan::GA::IP_Conjugate(c, a, conjA, b, conjB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("conj_a"), py::arg("b"), py::arg("conj_b"),
       "Inner product with optional conjugate on operands.");
"""

def _op_rev_def() -> str:
    return """
    m.def("op_rev", [](const TDynMV& a, bool revA, const TDynMV& b, bool revB) {
        TDynMV c;
        Tan::GA::OP_Reverse(c, a, revA, b, revB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("rev_a"), py::arg("b"), py::arg("rev_b"),
       "Outer product with optional reverse on operands.");
"""

def _op_conj_def() -> str:
    return """
    m.def("op_conj", [](const TDynMV& a, bool conjA, const TDynMV& b, bool conjB) {
        TDynMV c;
        Tan::GA::OP_Conjugate(c, a, conjA, b, conjB);
        c.Prune();
        return c;
    }, py::arg("a"), py::arg("conj_a"), py::arg("b"), py::arg("conj_b"),
       "Outer product with optional conjugate on operands.");
"""
```

### 3.2 Python `MV` class — new methods/properties

Each new binding must be wrapped in `Algebra` and optionally exposed on `MV`.

#### `algebra.py` additions

```python
def grade_proj(self, a: MV, grade: int) -> MV:
    """Extract grade-k part ⟨A⟩_k."""
    return MV(self._mod.grade_proj(a._impl, grade), self)

def scalar(self, a: MV) -> float | int:
    """Return the scalar coefficient of a."""
    return self._mod.scalar(a._impl)

def dual(self, a: MV) -> MV:
    """Compute the dual ★A."""
    return MV(self._mod.dual(a._impl), self)

def sp(self, a: MV, b: MV) -> float | int:
    """Scalar product (scalar part of a * b)."""
    return self._mod.sp(a._impl, b._impl)

def magnitude_sq(self, a: MV) -> float | int:
    """Sum of squared coefficients."""
    return self._mod.magnitude_sq(a._impl)

def magnitude(self, a: MV) -> float:
    """sqrt(sum of squared coefficients)."""
    return self._mod.magnitude(a._impl)

def is_zero(self, a: MV) -> bool:
    """True if all coefficients are zero."""
    return self._mod.is_zero(a._impl)

def is_scalar(self, a: MV) -> bool:
    """True if only the scalar blade is non-zero."""
    return self._mod.is_scalar(a._impl)

def project_to(self, a: MV, b: MV) -> MV:
    """Project a onto the blade set of b."""
    return MV(self._mod.project_to(a._impl, b._impl), self)

# Phase D: GP/IP/OP with reverse/conjugate flags
def gp_rev(self, a: MV, b: MV, rev_a: bool = False, rev_b: bool = False) -> MV:
    """Geometric product with optional reverse on operands."""
    return MV(self._mod.gp_rev(a._impl, rev_a, b._impl, rev_b), self)

def gp_conj(self, a: MV, b: MV, conj_a: bool = False, conj_b: bool = False) -> MV:
    """Geometric product with optional conjugate on operands."""
    return MV(self._mod.gp_conj(a._impl, conj_a, b._impl, conj_b), self)

def ip_rev(self, a: MV, b: MV, rev_a: bool = False, rev_b: bool = False) -> MV:
    """Inner product with optional reverse on operands."""
    return MV(self._mod.ip_rev(a._impl, rev_a, b._impl, rev_b), self)

def ip_conj(self, a: MV, b: MV, conj_a: bool = False, conj_b: bool = False) -> MV:
    """Inner product with optional conjugate on operands."""
    return MV(self._mod.ip_conj(a._impl, conj_a, b._impl, conj_b), self)

def op_rev(self, a: MV, b: MV, rev_a: bool = False, rev_b: bool = False) -> MV:
    """Outer product with optional reverse on operands."""
    return MV(self._mod.op_rev(a._impl, rev_a, b._impl, rev_b), self)

def op_conj(self, a: MV, b: MV, conj_a: bool = False, conj_b: bool = False) -> MV:
    """Outer product with optional conjugate on operands."""
    return MV(self._mod.op_conj(a._impl, conj_a, b._impl, conj_b), self)
```

#### `mv.py` additions

```python
def grade(self, k: int) -> "MV":
    """Extract grade-k part ⟨self⟩_k."""
    return self._alg.grade_proj(self, k)

def dual(self) -> "MV":
    """Compute the dual ★self."""
    return self._alg.dual(self)

def sp(self, other: "MV") -> float | int:
    """Scalar product (scalar part of self * other)."""
    return self._alg.sp(self, other)

# Phase D: GP/IP/OP with reverse/conjugate flags
def gp_rev(self, other: "MV", rev_self: bool = False, rev_other: bool = False) -> "MV":
    """Geometric product with optional reverse on operands."""
    return self._alg.gp_rev(self, other, rev_self, rev_other)

def gp_conj(self, other: "MV", conj_self: bool = False, conj_other: bool = False) -> "MV":
    """Geometric product with optional conjugate on operands."""
    return self._alg.gp_conj(self, other, conj_self, conj_other)

def ip_rev(self, other: "MV", rev_self: bool = False, rev_other: bool = False) -> "MV":
    """Inner product with optional reverse on operands."""
    return self._alg.ip_rev(self, other, rev_self, rev_other)

def ip_conj(self, other: "MV", conj_self: bool = False, conj_other: bool = False) -> "MV":
    """Inner product with optional conjugate on operands."""
    return self._alg.ip_conj(self, other, conj_self, conj_other)

def op_rev(self, other: "MV", rev_self: bool = False, rev_other: bool = False) -> "MV":
    """Outer product with optional reverse on operands."""
    return self._alg.op_rev(self, other, rev_self, rev_other)

def op_conj(self, other: "MV", conj_self: bool = False, conj_other: bool = False) -> "MV":
    """Outer product with optional conjugate on operands."""
    return self._alg.op_conj(self, other, conj_self, conj_other)

# Properties
@property
def scalar(self) -> float | int:
    """The scalar coefficient."""
    return self._alg.scalar(self)

@property
def mag2(self) -> float | int:
    """Sum of squared coefficients."""
    return self._alg.magnitude_sq(self)

@property
def mag(self) -> float:
    """sqrt(sum of squared coefficients)."""
    return self._alg.magnitude(self)

@property
def is_zero(self) -> bool:
    """True if all coefficients are zero."""
    return self._alg.is_zero(self)

@property
def is_scalar(self) -> bool:
    """True if only the scalar blade is non-zero."""
    return self._alg.is_scalar(self)

def project_to(self, other: "MV") -> "MV":
    """Project self onto the blade set of other (retain only shared blades)."""
    return self._alg.project_to(self, other)
```

### 3.3 `_codegen.py` — template placeholder wiring

The `generate()` function needs to wire the new fragment placeholders into
the template. Currently the function handles `{GP_MOD_DEF}`, `{OP_MOD_DEF}`,
`{IP_MOD_DEF}`, `{INV_DEF}`, `{REDUCE_DEF}`, `{MATRIX_DEF}`.

Add new entries for the common (dtype-independent) bindings:

```python
# In generate(), after the existing replacements:
template = template.replace("{GRADE_PROJ_DEF}", _grade_proj_def())
template = template.replace("{SCALAR_DEF}", _scalar_def())
template = template.replace("{DUAL_DEF}", _dual_def())
template = template.replace("{MAGNITUDE_SQ_DEF}", _magnitude_sq_def())
template = template.replace("{MAGNITUDE_DEF}", _magnitude_def())
template = template.replace("{IS_ZERO_DEF}", _is_zero_def())
template = template.replace("{IS_SCALAR_DEF}", _is_scalar_def())
template = template.replace("{SP_DEF}", _sp_def())
template = template.replace("{PROJECT_TO_DEF}", _project_to_def())

# Phase D: GP/IP/OP with reverse/conjugate flags
template = template.replace("{GP_REV_DEF}", _gp_rev_def())
template = template.replace("{GP_CONJ_DEF}", _gp_conj_def())
template = template.replace("{IP_REV_DEF}", _ip_rev_def())
template = template.replace("{IP_CONJ_DEF}", _ip_conj_def())
template = template.replace("{OP_REV_DEF}", _op_rev_def())
template = template.replace("{OP_CONJ_DEF}", _op_conj_def())
```

### 3.4 `_template.cpp` — new placeholder slots

Insert new placeholder slots in the template. A logical place is after
the existing `// Reverse and versor product` section and before
`{REDUCE_DEF}`:

```cpp
    // -----------------------------------------------------------------------
    // Grade projection, scalar extraction, dual
    // -----------------------------------------------------------------------
{GRADE_PROJ_DEF}
{SCALAR_DEF}
{DUAL_DEF}

    // -----------------------------------------------------------------------
    // Magnitude
    // -----------------------------------------------------------------------
{MAGNITUDE_SQ_DEF}
{MAGNITUDE_DEF}

    // -----------------------------------------------------------------------
    // Boolean queries
    // -----------------------------------------------------------------------
{IS_ZERO_DEF}
{IS_SCALAR_DEF}

    // -----------------------------------------------------------------------
    // Scalar product & projection
    // -----------------------------------------------------------------------
{SP_DEF}
{PROJECT_TO_DEF}

    // -----------------------------------------------------------------------
    // GP/IP/OP with reverse/conjugate flags (Phase D)
    // -----------------------------------------------------------------------
{GP_REV_DEF}
{GP_CONJ_DEF}
{IP_REV_DEF}
{IP_CONJ_DEF}
{OP_REV_DEF}
{OP_CONJ_DEF}
```

### 3.5 Docs — update `docs/py/mv.md`

Add the new methods/properties to the tables in `docs/py/mv.md`:

**Named Methods table — new rows:**

| Method | Operator | Description |
|---|---|---|
| `a.grade(k)` | — | Grade projection: extract ⟨a⟩ₖ |
| `a.dual()` | — | Dual: ★a = a · I⁻¹ |
| `a.sp(b)` | — | Scalar product: scalar part of a * b |
| `a.project_to(b)` | — | Restrict a to the blade set of b |
| `a.gp_rev(b, rev_self, rev_other)` | — | GP with optional reverse on operands |
| `a.gp_conj(b, conj_self, conj_other)` | — | GP with optional conjugate on operands |
| `a.ip_rev(b, rev_self, rev_other)` | — | IP with optional reverse on operands |
| `a.ip_conj(b, conj_self, conj_other)` | — | IP with optional conjugate on operands |
| `a.op_rev(b, rev_self, rev_other)` | — | OP with optional reverse on operands |
| `a.op_conj(b, conj_self, conj_other)` | — | OP with optional conjugate on operands |

**Properties — new subsection:**

| Property | Return type | Description |
|---|---|---|
| `a.scalar` | `float \| int` | Scalar coefficient |
| `a.mag2` | `float \| int` | Sum of squared coefficients |
| `a.mag` | `float` | sqrt of mag2 |
| `a.is_zero` | `bool` | True if all blades are zero |
| `a.is_scalar` | `bool` | True if only scalar blade is non-zero |

---

## 4. Order of Work

### Step 1 — Core binding fragments (Phases A, B, C, D) ✅
Files changed:
- `py/pytanga/_codegen.py`: Added all `_*_def()` fragment functions (16 total).
- `py/pytanga/_codegen.py`: Wired all 16 placeholders into `generate()`.
- `py/pytanga/_template.cpp`: Added placeholder slots for all 16 new fragments.

### Step 2 — Python Algebra wrapper ✅
File changed:
- `py/pytanga/algebra.py`: Added `grade_proj`, `scalar`, `dual`, `sp`,
  `magnitude_sq`, `magnitude`, `is_zero`, `is_scalar`, `project_to`,
  `gp_rev`, `gp_conj`, `ip_rev`, `ip_conj`, `op_rev`, `op_conj` methods (16 total).

### Step 3 — Python MV methods ✅
File changed:
- `py/pytanga/mv.py`: Added `grade()`, `dual()`, `sp()`, `project_to()`,
  `gp_rev()`, `gp_conj()`, `ip_rev()`, `ip_conj()`, `op_rev()`, `op_conj()`
  methods (10 total) and `scalar`, `mag2`, `mag`, `is_zero`, `is_scalar` properties (5 total).

### Step 4 — Documentation ✅
File changed:
- `docs/py/mv.md`: Added entries for all 10 new methods and 5 new properties
  (see §3.5 for the complete table).

### Step 5 (later) — Batch versor product, GCD, modulus operator
Low-priority niche operations. GCD can be done in pure Python.
Batch versor product can be done with a list comprehension.

---

## 5. Design Decisions

1. **`grade_proj` vs `grade`**: The C++ function is `GetGradeProjection`.
   The Python method on MV is named `grade(k)` for brevity, matching
   common GA notation $\langle A \rangle_k$.

2. **`dual()` vs operator**: The dual is a named method, not an operator
   overload. There is no obvious Python operator for the dual.

3. **`scalar` as a property**: Since it takes no arguments and returns a
   single value, a `@property` fits naturally.

4. **`sp()` returning a scalar, not an MV**: The scalar product returns
   a single number (`float` or `int`), not an `MV` instance. This matches
   the C++ semantics.

5. **Integer algebras**: All new functions work with both float and integer
   dtypes. For integer algebras, no automatic modular reduction is applied
   (unlike `gp`/`op`/`ip` which auto-reduce when `self._modulus` is set).
   Callers should explicitly call `reduce()` if needed. Rationale: operations
   like `grade()`, `dual()`, `scalar()` are structural, not arithmetic
   products, and modular reduction may not be meaningful.

6. **Congruence variants**: The `_Congruence` product variants
   (`GP_Congruence`, etc.) are already wired internally through `gp_mod`.
   No new Python surface is needed.

7. **`project_to` semantics**: The C++ `ProjectTo(wA, wB)` zeros `wA`
   then copies matching blades from `wB`. We expose this as
   `a.project_to(b)` — returns a new MV containing only the blades of
   `a` that also exist in `b`, with coefficients taken from `a` (not `b`).
   Verify this matches user expectations during implementation.