# Phase 6 — Python Facade

**Overview plan:** [plan.md](plan.md)  
**Depends on:** Phase 1 (`_blade_names`), Phase 5 (`_cache.get_or_build`)  
**Required by:** Phase 7 (tests use the public API)

---

## Goal

Implement the user-facing classes in `pytanga/__init__.py`:

- `MV` — a thin Python wrapper around the C++ `DynMV` object that adds
  blade-name indexing, operator overloads, and a human-readable `__repr__`.
- `Algebra` — loads (or builds) the compiled module for a given `(dim, sig,
  dtype)` and exposes GA operations as clean Python methods.

---

## Steps

### 6.1 Define `MV`

`MV` is intentionally minimal: it delegates arithmetic to the `Algebra`
instance that created it, so the C++ module reference stays in one place.

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytanga import Algebra


class MV:
    """
    A multivector belonging to a specific Algebra instance.

    Coefficients are stored in the wrapped C++ DynMV object.
    Arithmetic operators delegate to the parent Algebra.
    """

    __slots__ = ("_impl", "_alg")

    def __init__(self, impl, alg: "Algebra") -> None:
        self._impl = impl   # C++ DynMV
        self._alg  = alg    # parent Algebra — keeps algebra metadata close

    # -----------------------------------------------------------------------
    # Coefficient access — accept both blade names and integer blade ids
    # -----------------------------------------------------------------------
    def __getitem__(self, key: str | int) -> float | int:
        blade_id = self._alg._resolve_key(key)
        return self._impl.get(blade_id)

    def __setitem__(self, key: str | int, value: float | int) -> None:
        blade_id = self._alg._resolve_key(key)
        self._impl.set(blade_id, value)

    # -----------------------------------------------------------------------
    # Arithmetic operators
    # -----------------------------------------------------------------------
    def __mul__(self, other: "MV") -> "MV":
        return self._alg.gp(self, other)

    def __xor__(self, other: "MV") -> "MV":
        return self._alg.op(self, other)

    def __or__(self, other: "MV") -> "MV":
        return self._alg.ip(self, other)

    def __invert__(self) -> "MV":
        return self._alg.inv(self)

    # -----------------------------------------------------------------------
    # Representation
    # -----------------------------------------------------------------------
    def __repr__(self) -> str:
        from pytanga._blade_names import blade_name
        dim    = self._alg.dim
        coeffs = self._impl.to_dict()
        if not coeffs:
            return "0"
        terms = []
        # Sort by grade then blade id for a stable readable order
        for blade_id in sorted(coeffs, key=lambda b: (bin(b).count('1'), b)):
            val  = coeffs[blade_id]
            name = blade_name(blade_id, dim)
            terms.append(f"{val}*{name}" if name != "s" else str(val))
        return " + ".join(terms)

    # -----------------------------------------------------------------------
    # Utility
    # -----------------------------------------------------------------------
    def to_dict(self) -> dict[str | int, float | int]:
        """Return {blade_name: coeff} for all non-zero blades."""
        from pytanga._blade_names import blade_name
        dim = self._alg.dim
        return {blade_name(k, dim): v for k, v in self._impl.to_dict().items()}

    def prune(self) -> "MV":
        """Remove near-zero coefficients in-place and return self."""
        self._impl.prune()
        return self
```

### 6.2 Define `Algebra`

```python
class Algebra:
    """
    A geometric algebra G(dim, sig) over values of type *dtype*.

    Parameters
    ----------
    dim   : vector-space dimension (1–32)
    sig   : signature bitmask — bit k=1 means basis vector e_{k+1} squares to -1
    dtype : 'float32' | 'float64' | 'int32' | 'int64'

    On first construction for a new (dim, sig, dtype), the C++ binding is
    compiled (~5–20 s). Subsequent constructions load the cached binary (~ms).
    """

    def __init__(
        self,
        dim: int,
        sig: int = 0,
        dtype: str = "float64",
        *,
        verbose: bool = False,
    ) -> None:
        from pytanga._cache import get_or_build

        self._dim   = dim
        self._sig   = sig
        self._dtype = dtype
        self._mod   = get_or_build(dim, sig, dtype, verbose=verbose)

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------
    @property
    def dim(self) -> int:
        return self._dim

    @property
    def sig(self) -> int:
        return self._sig

    @property
    def dtype(self) -> str:
        return self._dtype

    @property
    def algebra_dim(self) -> int:
        """2 ** dim — total number of basis blades."""
        return self._mod.ALGEBRA_DIM

    @property
    def pseudoscalar_id(self) -> int:
        return self._mod.PSEUDOSCALAR_ID

    # -----------------------------------------------------------------------
    # Factory
    # -----------------------------------------------------------------------
    def multivector(
        self,
        coeffs: dict[str, float] | dict[int, float] | None = None,
    ) -> MV:
        """
        Create a multivector.

        *coeffs* may be:
        - a dict with string keys:  {"e1": 1.0, "e12": -0.5}
        - a dict with integer keys: {1: 1.0, 3: -0.5}  (raw blade bitmasks)
        - None for a zero multivector
        """
        impl = self._mod.DynMV()
        if coeffs:
            for key, val in coeffs.items():
                blade_id = self._resolve_key(key)
                impl.set(blade_id, val)
        return MV(impl, self)

    # -----------------------------------------------------------------------
    # GA operations
    # -----------------------------------------------------------------------
    def gp(self, a: MV, b: MV) -> MV:
        """Geometric product a * b."""
        return MV(self._mod.gp(a._impl, b._impl), self)

    def op(self, a: MV, b: MV) -> MV:
        """Outer (wedge) product a ^ b."""
        return MV(self._mod.op(a._impl, b._impl), self)

    def ip(self, a: MV, b: MV) -> MV:
        """Inner product a | b."""
        return MV(self._mod.ip(a._impl, b._impl), self)

    def inv(self, a: MV, modulus: int | None = None) -> MV:
        """
        Multiplicative inverse.

        *modulus* is required for integer dtypes ('int32', 'int64') and
        ignored for floating-point dtypes.
        """
        if self._dtype in ("int32", "int64"):
            if modulus is None:
                raise ValueError("modulus is required for integer dtypes")
            return MV(self._mod.inv(a._impl, modulus), self)
        return MV(self._mod.inv(a._impl), self)

    # -----------------------------------------------------------------------
    # Blade name helpers
    # -----------------------------------------------------------------------
    def blade_id(self, name: str) -> int:
        from pytanga._blade_names import blade_id
        return blade_id(name, self._dim)

    def blade_name(self, blade_id: int) -> str:
        from pytanga._blade_names import blade_name
        return blade_name(blade_id, self._dim)

    def all_blades(self) -> list[int]:
        from pytanga._blade_names import all_blades
        return all_blades(self._dim)

    # -----------------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------------
    def _resolve_key(self, key: str | int) -> int:
        if isinstance(key, int):
            return key
        from pytanga._blade_names import blade_id
        return blade_id(key, self._dim)

    def __repr__(self) -> str:
        return f"Algebra(dim={self._dim}, sig={self._sig:#010b}, dtype={self._dtype!r})"
```

### 6.3 Public exports

```python
__all__ = ["Algebra", "MV"]
```

### 6.4 Verify the end-to-end API

```python
import pytanga

alg = pytanga.Algebra(dim=3, sig=0)    # G(3,0) — compiles or loads from cache

e1  = alg.multivector({"e1": 1.0})
e2  = alg.multivector({"e2": 1.0})
e12 = alg.multivector({"e12": 1.0})

# e1 * e1 == scalar 1
assert (e1 * e1).to_dict() == {"s": 1.0}

# e1 ^ e2 == e12
result = e1 ^ e2
assert result["e12"] == 1.0

# __repr__ is human-readable
print(repr(e1))      # "1.0*e1"
print(repr(e1 * e2)) # "1.0*e12"

# inv(e12): in G(3,0), e12 * e12 = -e0 = -scalar, so inv(e12) = -e12
inv_e12 = ~e12
assert abs(inv_e12["e12"] + 1.0) < 1e-9
```

---

## Completion check

- [x] `pytanga/__init__.py` is fully implemented
- [x] `from pytanga import Algebra, MV` works without error
- [x] `Algebra(3, 0)` constructs successfully (hit or miss cache)
- [x] `e1 * e1` returns a scalar 1 multivector
- [x] `e1 ^ e2` returns an `e12` blade
- [x] `~e12` (invert) returns `-e12`
- [x] Blade-name indexing `mv["e12"]` and integer-id indexing `mv[3]` both work
- [x] `repr(alg)` and `repr(mv)` both produce readable strings
