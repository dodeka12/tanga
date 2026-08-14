# Phase 1 — Mutable `opns` on `Algebra` and `MV`

**Prerequisites:** None (purely additive; nothing existing is removed).

**Goal:** Add a mutable `opns` flag to `Algebra`, expose it on every `MV`, and
forward it through all eight `Basis*` subclasses. After this phase the flag is
available everywhere but not yet consumed by create/analyze.

---

## 1. `Algebra.opns`

File: `py/pytanga/algebra/_algebra.py`

### 1.1 Constructor

Add `opns: bool = True` as a keyword-only argument (after `seed`), and store
`self._opns = bool(opns)`.

```python
def __init__(
    self,
    dim: int,
    sig: int | tuple[int, ...] = 0,
    dtype: str = "float64",
    *,
    verbose: bool = False,
    modulus: int | None = None,
    print_fmt: str = ".4g",
    precision: float = 1e-10,
    seed: int | None = None,
    opns: bool = True,
) -> None:
    ...
    self._opns = bool(opns)
```

### 1.2 Property (mutable)

```python
@property
def opns(self) -> bool:
    """OPNS/IPNS interpretation flag.

    ``True`` (default) -> multilinevectors are interpreted in the Outer
    Product Null Space; ``False`` -> Inner Product Null Space.  This is the
    single source of truth for geometry interpretation: every multivector
    created by this algebra reads the flag through :attr:`~pytanga.MV.opns`.

    The flag is mutable.  Changing it reinterprets subsequently created or
    analyzed multivectors of this algebra (existing MVs will be interpreted
    with the new setting when analyzed).
    """
    return self._opns

@opns.setter
def opns(self, value: bool) -> None:
    self._opns = bool(value)
```

---

## 2. `MV.opns`

File: `py/pytanga/algebra/_mv.py`

Add a read-mostly property (no setter; mutation happens on the algebra):

```python
@property
def opns(self) -> bool:
    """The OPNS/IPNS interpretation flag inherited from this multivector's algebra."""
    return self._alg.opns
```

---

## 3. Basis subclasses forward `opns`

Each basis `__init__` currently calls `super().__init__(...)`. Add `opns` to their
signature and pass it through. The eight files are:

| File | Current `super().__init__` |
|------|----------------------------|
| `py/pytanga/basis/e2.py` | `super().__init__(2, 0, dtype, **kw)` |
| `py/pytanga/basis/e3.py` | `super().__init__(3, 0, dtype, **kw)` |
| `py/pytanga/basis/p2.py` | `super().__init__(3, 0, dtype, seed=seed, **kw)` |
| `py/pytanga/basis/p3.py` | `super().__init__(4, 0, dtype, seed=seed, **kw)` |
| `py/pytanga/basis/n2.py` | `super().__init__(4, 0b1000, dtype, **kw)` |
| `py/pytanga/basis/n3.py` | `super().__init__(5, 0b10000, dtype, **kw)` |
| `py/pytanga/basis/pga2.py` | `super().__init__(4, 0b1000, dtype, **kw)` |
| `py/pytanga/basis/pga3.py` | `super().__init__(5, 0b10000, dtype, **kw)` |

These already accept `**kw`, so `opns` is forwarded automatically. Only add an
explicit `opns` parameter where the subclass signature also needs it (the ones
with `seed`) — but since `**kw` is present everywhere, the minimal change is to
**not** add a named parameter and rely on `**kw`. However, for discoverability,
add `opns: bool = True` explicitly and pass `opns=opns` in the ones that also
name `seed` (`p2`, `p3`); the `**kw`-only ones are left unchanged because `**kw`
already forwards it.

> Decision: keep the change uniform and explicit — add `opns: bool = True` to
> every basis `__init__` and pass it explicitly to `super().__init__(...)`.
> This avoids relying on undocumented `**kw` forwarding.

---

## 4. Tests (Phase 1)

New file `py/tests/geometry/test_opns_algebra_flag.py`:

- `Algebra(2, 0).opns is True`
- `Algebra(2, 0, opns=False).opns is False`
- `BasisE3().opns is True`; `BasisE3(opns=False).opns is False`
- `BasisP3(opns=False).opns is False`, `BasisPGA3(opns=False).opns is False` (2D+3D)
- mutation: `alg = BasisE3(); alg.opns = False; assert alg.opns is False`
- `mv = alg.multivector({1: 1}); assert mv.opns is False` (delegates to algebra)
- flag is per-algebra, not global: two algebras with different `opns` are independent

No existing tests change in Phase 1.

---

## 5. Implementation Checklist

- [ ] `Algebra.__init__` gains `opns: bool = True`; stores `_opns`
- [ ] `Algebra.opns` property (getter + setter)
- [ ] `MV.opns` property
- [ ] Forward `opns` in all 8 `Basis*.__init__`
- [ ] Add `py/tests/geometry/test_opns_algebra_flag.py`
- [ ] Run: `pytest py/tests/geometry/test_opns_algebra_flag.py py/tests/basis -q`

---

## 6. Verification

- [ ] `Algebra(2, 0).opns is True`
- [ ] `Algebra(2, 0, opns=False).opns is False`
- [ ] `alg.opns = False` mutates and is observed by an existing `MV` via `mv.opns`
- [ ] All 8 basis classes construct with `opns=False` and report `False`