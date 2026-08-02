# Phase 9 — Predefined Basis Classes

**Overview plan:** [plan.md](plan.md)  
**Depends on:** Phase 6 (full Algebra facade), Phase 7 (tests pass)  
**Required by:** nothing – optional extension  

---

## Goal

Expose comfortable, typed basis helper objects on the Python side for the three
standard geometries. Each basis class inherits from `Algebra`, pre-populates
named blade attributes (`e1`, `einf`, `I`, …) as `MV` instances, and provides
geometric factory methods (`point`, `vector`, …). It enables the null-vector
embedding from `docs/py/pga_null_embedding.md` without the user having to
remember the underlying algebra signature.

> **Decision (revised from original plan):** The C++ basis classes
> (`CBasisE3`, `CBasisP3`, `CBasisN3`) are **not** wrapped via pybind11.  
> All blade IDs are compile-time bitmasks (`e_k` = `1 << (k-1)`) that are
> trivially expressed as Python integer literals. The null-vector coefficients
> for PGA3 (`einf`, `eo`) are hardcoded constants from `_CBasisN3::_Init()`.
> Binding the C++ types would add a compilation step per dtype for information
> that is dtype-independent — pure overhead with no benefit.  
> Steps 9.1–9.4 from the original plan (C++ template, codegen extension, build
> extension, cache extension) are therefore dropped.

---

## Why basis classes?

- The user should be able to work with `pytanga.basis.PGA3()` instead of having
  to remember the signature `(5, 0b10000)`.
- Named blade attributes (`e1`, `e2`, `einf`, `eo`, `I`, …) replace raw blade-ID
  dicts in user code.
- Factory methods (`point`, `vector`, …) encapsulate the embedding rules.
- Inheriting from `Algebra` keeps full backward compatibility: existing code that
  calls `alg.gp()`, `alg.op()`, etc. on a `BasisPGA3` instance continues to work.

---

## Planned basis classes

| C++ basis      | Python class  | dim | sig       | Description                                    |
|----------------|---------------|-----|-----------|------------------------------------------------|
| `CBasisE3`     | `BasisE3`     | 3   | `0`       | Euclidean 3D geometry                          |
| `CBasisP3`     | `BasisP3`     | 4   | `0`       | Projective 3D geometry (homogeneous coords)    |
| `CBasisN3`     | `BasisN3`     | 5   | `0b10000` | Null 3D algebra — raw named blades             |
| `CBasisN3`     | `BasisPGA3`   | 5   | `0b10000` | PGA‑3D — same algebra, adds geometric factory methods (subclass of `BasisN3`) |

### Blade ID bitmask reference

Each basis vector `e_k` has blade ID `1 << (k-1)`:

| Blade  | ID (decimal) | ID (binary) | Notes                          |
|--------|--------------|-------------|--------------------------------|
| `e1`   | 1            | `00001`     | all three bases                |
| `e2`   | 2            | `00010`     | all three bases                |
| `e3`   | 4            | `00100`     | all three bases                |
| `e4`   | 8            | `01000`     | P3 only (homogeneous direction)|
| `ep`   | 8            | `01000`     | N3/PGA3 — `ep² = +1`          |
| `em`   | 16           | `10000`     | N3/PGA3 — `em² = -1`          |
| `einf` | —            | —           | N3/PGA3 composed: `{8:1, 16:1}` (= ep + em) |
| `eo`   | —            | —           | N3/PGA3 composed: `{8:-0.5, 16:0.5}` (= 0.5·em - 0.5·ep) |

Pseudoscalar IDs: E3 = 7, P3 = 15, PGA3 = 31.

> **Null vector note:** From `_CBasisN3::_Init()`:  
> `einf` = `em + ep`, so coefficients `{em:1, ep:1}` → `{16:1.0, 8:1.0}`.  
> `eo`   = `0.5·em - 0.5·ep`   → `{16:0.5, 8:-0.5}`.  
> These hardcoded values match the embedding in `docs/py/pga_null_embedding.md`.

---

## Architecture (simplified)

1. **Python basis package** → `pytanga/basis/`  
   - `__init__.py` — public exports (`BasisE3`, `BasisP3`, `BasisN3`, `BasisPGA3`)  
   - `_e3.py`, `_p3.py`, `_n3.py`, `_pga3.py` — one module per basis.  
   - `BasisN3` inherits from `Algebra` and provides all raw named blades.  
   - `BasisPGA3` inherits from `BasisN3` and adds geometric factory methods.

2. **Integration with named algebras** → `pytanga/_algebra.py`  
   `Algebra.from_name("PGA3")` returns a `BasisPGA3` instance instead of a
   plain `Algebra`. Fully backward-compatible because `BasisXxx` inherits
   from `Algebra`.

No C++ compilation, no codegen, no cache changes are required.

---

## Detailed steps

### 9.1 – Python basis package (`pytanga/basis/`)

Create `pytanga/basis/__init__.py` exporting the three classes.

### 9.2 – `BasisE3` (`pytanga/basis/_e3.py`)

```python
class BasisE3(Algebra):
    def __init__(self, dtype: str = "float64", **kw) -> None:
        super().__init__(3, 0, dtype, **kw)
        mv = self.multivector
        self.e1  = mv({1: 1})
        self.e2  = mv({2: 1})
        self.e3  = mv({4: 1})
        self.e12 = self.op(self.e1, self.e2)
        self.e31 = self.op(self.e3, self.e1)
        self.e23 = self.op(self.e2, self.e3)
        self.I   = mv({self.pseudoscalar_id: 1})

    def vector(self, x: float, y: float, z: float) -> MV:
        """x·e1 + y·e2 + z·e3"""
        return self.multivector({1: x, 2: y, 4: z})
```

### 9.3 – `BasisP3` (`pytanga/basis/_p3.py`)

```python
class BasisP3(Algebra):
    def __init__(self, dtype: str = "float64", **kw) -> None:
        super().__init__(4, 0, dtype, **kw)
        mv = self.multivector
        self.e1 = mv({1: 1})
        self.e2 = mv({2: 1})
        self.e3 = mv({4: 1})
        self.e4 = mv({8: 1})   # homogeneous direction
        self.I  = mv({self.pseudoscalar_id: 1})

    def point(self, x: float, y: float, z: float) -> MV:
        """Homogeneous point: x·e1 + y·e2 + z·e3 + e4"""
        return self.multivector({1: x, 2: y, 4: z, 8: 1})
```

### 9.4 – `BasisN3` (`pytanga/basis/_n3.py`)

Mirrors `CBasisN3` directly — same algebra, same named blades, no geometric
interpretation yet. `BasisPGA3` will subclass this.

```python
_EP = 8   # ep  (e4, ep²=+1)
_EM = 16  # em  (e5, em²=-1)

class BasisN3(Algebra):
    def __init__(self, dtype: str = "float64", **kw) -> None:
        super().__init__(5, 0b10000, dtype, **kw)
        mv = self.multivector
        self.e1   = mv({1: 1})
        self.e2   = mv({2: 1})
        self.e3   = mv({4: 1})
        self.ep   = mv({_EP: 1})
        self.em   = mv({_EM: 1})
        self.einf = mv({_EP: 1.0,  _EM: 1.0})   # ep + em
        self.eo   = mv({_EP: -0.5, _EM: 0.5})   # 0.5·em - 0.5·ep
        self.e0   = self.einf                    # alias
        self.I    = mv({self.pseudoscalar_id: 1})
```

### 9.5 – `BasisPGA3` (`pytanga/basis/_pga3.py`)

Blade IDs follow `CBasisN3`: `ep = 8` (e4, `ep²=+1`), `em = 16` (e5, `em²=−1`).  
Null vectors from `_CBasisN3::_Init()`:

| Name   | Coefficients              |
|--------|---------------------------|
| `einf` | `{8: 1.0,  16: 1.0}`     |
| `eo`   | `{8: -0.5, 16: 0.5}`     |

```python
from pytanga.basis._n3 import BasisN3

class BasisPGA3(BasisN3):
    """BasisN3 extended with PGA geometric factory methods."""
    # No __init__ override needed — inherits all named blades from BasisN3.

    def point(self, x: float, y: float, z: float) -> MV:
        """Finite PGA3 point: x·e1 + y·e2 + z·e3 + eo"""
        return self.multivector({1: x, 2: y, 4: z, _EP: -0.5, _EM: 0.5})

    def vector(self, x: float, y: float, z: float) -> MV:
        """Ideal point (direction): x·e1 + y·e2 + z·e3"""
        return self.multivector({1: x, 2: y, 4: z})
```

**Null condition check:** For a finite point `p = point(x,y,z)`, the inner
product `p | einf` must be non-zero (it equals `−1`). For an ideal point
(direction) it is zero.

### 9.6 – Integration with `Algebra.from_name` (`pytanga/_algebra.py`)

`from_name` checks a map of named bases and returns the appropriate basis
class instance, falling back to a plain `Algebra` for all other names:

```python
_BASIS_NAMES = {"E3": "BasisE3", "P3": "BasisP3", "N3": "BasisN3", "PGA3": "BasisPGA3"}

@classmethod
def from_name(cls, name, dtype="float64", **kwargs):
    if name in _BASIS_NAMES:
        from pytanga.basis import _CLASS_MAP
        return _CLASS_MAP[name](dtype=dtype, **kwargs)
    # existing logic for G2, CGA3, STA, …
```

### 9.7 – Tests (`pytanga/tests/test_basis.py`)

- Import `BasisE3`, `BasisP3`, `BasisPGA3` from `pytanga.basis`.
- `Algebra.from_name("PGA3")` returns a `BasisPGA3` instance.
- `isinstance(BasisPGA3(), Algebra)` is `True`.
- `e1 * e1` in E3 returns scalar `1` (Euclidean metric).
- `einf * einf` = 0 (null vector squares to zero) in PGA3.
- `eo * eo` = 0 (origin null vector also squares to zero) in PGA3.
- `BasisPGA3().point(1, 2, 3)` inner-producted with `einf` gives `−1`.

---

## Files to create / modify

| Action | File |
|--------|------|
| Delete | `pytanga/_template_basis.cpp` (created by mistake, not needed) |
| Create | `pytanga/basis/__init__.py` |
| Create | `pytanga/basis/_e3.py` |
| Create | `pytanga/basis/_p3.py` |
| Create | `pytanga/basis/_n3.py` |
| Create | `pytanga/basis/_pga3.py` |
| Modify | `pytanga/_algebra.py` — update `from_name` |
| Create | `pytanga/tests/test_basis.py` |

---

## Completion check

- [ ] `pytanga/_template_basis.cpp` is deleted.
- [ ] `pytanga/basis/` package exists with `BasisE3`, `BasisP3`, `BasisN3`, `BasisPGA3`.
- [ ] Each basis class passes `isinstance(b, Algebra)`.
- [ ] `BasisPGA3().einf * BasisPGA3().einf` = 0 (null vector).
- [ ] `BasisPGA3().eo * BasisPGA3().eo` = 0 (null vector).
- [ ] `BasisPGA3().point(1,2,3)` inner-producted with `einf` gives `−1`.
- [ ] `Algebra.from_name("PGA3")` returns a `BasisPGA3` instance.
- [ ] `isinstance(BasisPGA3(), BasisN3)` is `True`.
- [ ] `Algebra.from_name("N3")` returns a `BasisN3` instance.
- [ ] `Algebra.from_name("G2")` still returns a plain `Algebra` instance.
- [ ] Tests in `pytanga/tests/test_basis.py` pass.

