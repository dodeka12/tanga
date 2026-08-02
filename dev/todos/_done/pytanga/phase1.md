# Phase 1 — Pure-Python Blade Name Utilities

**Overview plan:** [plan.md](plan.md)  
**Depends on:** Phase 0 (directory structure only)  
**Required by:** Phase 6 (facade `__repr__`, `__getitem__`, `multivector()`)

---

## Goal

Implement `pytanga/_blade_names.py` — all bit-arithmetic, no C++.  
This module is independently testable before any C++ work starts.

---

## Blade encoding recap

TanGA encodes a blade as a `uint32_t` bitmask.  
Basis vector `e_k` corresponds to bit `k-1` (0-indexed), so:

| Name | Bitmask | Decimal |
|---|---|---|
| scalar (`s`) | `0b000...0` | 0 |
| `e1` | `0b000...01` | 1 |
| `e2` | `0b000...10` | 2 |
| `e12` | `0b000...11` | 3 |
| `e3` | `0b000...100` | 4 |
| `e123` / pseudoscalar | `0b000...111` | 7 |

Grade = number of set bits (`popcount`).

---

## Steps

### 1.1 `grade(blade_id: int) -> int`

```python
def grade(blade_id: int) -> int:
    return bin(blade_id).count('1')
```

Simplest possible; relies on Python's arbitrary-precision integers.

### 1.2 `all_blades(dim: int) -> list[int]`

Returns every blade id for a `dim`-dimensional algebra, sorted by grade then
by id within each grade (matching the canonical ordering used in TanGA's
`CBlade` comparison operator):

```python
def all_blades(dim: int) -> list[int]:
    if dim < 1 or dim > 32:
        raise ValueError(f"dim must be in [1, 32], got {dim}")
    return sorted(range(1 << dim), key=lambda b: (grade(b), b))
```

### 1.3 `blade_name(blade_id: int, dim: int) -> str`

Converts a bitmask to the canonical TanGA-style name:

- `0` → `"s"` (scalar)
- `(1 << dim) - 1` → `"I"` (pseudoscalar)
- everything else → `"e"` followed by the 1-based indices of set bits in
  ascending order, e.g. bitmask `0b0101` with `dim=3` → `"e13"`

```python
def blade_name(blade_id: int, dim: int) -> str:
    if blade_id < 0 or blade_id >= (1 << dim):
        raise ValueError(f"blade_id {blade_id} out of range for dim={dim}")
    if blade_id == 0:
        return "s"
    if blade_id == (1 << dim) - 1:
        return "I"
    indices = [str(k + 1) for k in range(dim) if blade_id & (1 << k)]
    return "e" + "".join(indices)
```

### 1.4 `blade_id(name: str, dim: int) -> int`

Parses a name back to a bitmask. Accept the following forms:
- `"s"` or `"0"` → scalar (id = 0)
- `"I"` → pseudoscalar (id = `(1 << dim) - 1`)
- `"e"` followed by one or more distinct decimal digits in `[1, dim]` in
  **any** order (canonical form sorts them; input is flexible).
  Repeated indices are an error.

```python
def blade_id(name: str, dim: int) -> int:
    if name in ("s", "0"):
        return 0
    if name == "I":
        return (1 << dim) - 1
    if not name.startswith("e"):
        raise ValueError(f"Cannot parse blade name: {name!r}")
    tail = name[1:]
    if not tail.isdigit():
        raise ValueError(f"Non-digit characters after 'e' in: {name!r}")
    indices = [int(c) for c in tail]
    if len(indices) != len(set(indices)):
        raise ValueError(f"Repeated basis-vector index in: {name!r}")
    if any(i < 1 or i > dim for i in indices):
        raise ValueError(f"Index out of range [1, {dim}] in: {name!r}")
    result = 0
    for i in indices:
        result |= (1 << (i - 1))
    return result
```

> **Note on multi-digit indices:** the format `"e12"` is ambiguous for
> `dim > 9` (does it mean e1∧e2 or e12?). For `dim ≤ 9` each character is one
> index. For `dim > 9` require comma-separated format `"e1,2,10"`. Implement
> this in the same function by checking whether the tail contains a comma.

### 1.5 Add the comma-separated fallback for `dim > 9`

Extend `blade_id` to handle `"e1,2,10"` style:

```python
    # inside blade_id, after the "e" branch check:
    if "," in tail:
        indices = [int(s) for s in tail.split(",")]
    else:
        # single-character indices only — safe for dim <= 9
        if dim > 9:
            raise ValueError(
                f"Use comma-separated format (e.g. 'e1,2,10') for dim > 9; got {name!r}")
        indices = [int(c) for c in tail]
```

### 1.6 Module-level `__all__`

```python
__all__ = ["grade", "all_blades", "blade_name", "blade_id"]
```

---

## Completion check

- [ ] `pytanga/_blade_names.py` is fully implemented (no stubs)
- [ ] All four functions are importable: `from pytanga._blade_names import ...`
- [ ] Manual spot-checks pass:
  - `blade_id("e1", 3)` == 1
  - `blade_id("e12", 3)` == 3
  - `blade_id("I", 3)` == 7
  - `blade_name(3, 3)` == `"e12"`
  - `blade_name(7, 3)` == `"I"`
  - `grade(3)` == 2
  - `len(all_blades(3))` == 8
- [ ] Phase 7 writes the definitive `test_blade_names.py`; optionally write
  it now for early feedback — it requires no C++ and gives immediate results
