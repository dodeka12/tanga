# Phase 3 — BladeMask.from_array Classmethod

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing  
> any step in this plan.

## Goal

Add a `BladeMask.from_array(alg, mvs)` classmethod that builds a mask from
the union of the non-zero blade sets of multiple multivectors.

---

## Current State

`BladeMask` has these construction methods:

| Method | Input | Purpose |
|---|---|---|
| `__init__` | `ids`, `grades` | From int ids, strings, or grade lists |
| `from_mv` | single `MV` | Non-zero blades of one multivector |
| `from_str` | `str` | Convenience alias for `BladeMask(alg, s)` |
| `full` | — | All blades of the algebra |

No method exists for combining blade sets from multiple MVs.

---

## Step

### Step 3.1 — Add `from_array` classmethod

**File:** `py/pytanga/blade_mask.py`

Add the following classmethod to the `BladeMask` class, after the existing
`from_mv`:

```python
@classmethod
def from_array(cls, alg: "Algebra", mvs: list["MV"]) -> "BladeMask":
    """Build a mask that is the union of the non-zero blades of each MV in *mvs*.

    Parameters
    ----------
    alg : Algebra
        The algebra all MVs belong to.
    mvs : list[MV]
        List of multivectors whose blade sets are unioned.

    Returns
    -------
    BladeMask
        The union of the individual blade masks.
    """
    raw: set[int] = set()
    for mv in mvs:
        try:
            raw_ids = alg._mod.blade_mask(mv._impl, True)
        except AttributeError:
            # Fallback if C++ binding not yet compiled
            d = mv._impl.to_dict()
            raw_ids = [k for k, v in d.items() if v != 0]
        raw.update(raw_ids)
    return cls(alg, raw)
```

**Implementation notes:**
- Uses `try/except AttributeError` to fall back to Python iteration when
  the C++ `blade_mask` binding is not yet available (same pattern as
  `from_mv`).
- Only non-zero blades are collected (`only_nonzero=True`).
- The result is a single `BladeMask` with the union (sorted, deduplicated
  via the normal `__init__` path).

---

## Verification

After completing this step:

```python
import pytanga
alg = pytanga.Algebra(3, 0)

# Union of e1, e2, e3
mvs = [alg(f"e{i}") for i in range(1, 4)]
mask = pytanga.BladeMask.from_array(alg, mvs)
assert mask.ids == [1, 2, 4]       # e1, e2, e3

# Union of overlapping blade sets
a = alg("e1 + e12")
b = alg("e2 + e12")
mask2 = pytanga.BladeMask.from_array(alg, [a, b])
assert mask2.ids == [1, 2, 3]      # e1, e2, e12

# Empty list → empty mask
mask3 = pytanga.BladeMask.from_array(alg, [])
assert mask3.ids == []
```

---

## Files Touched

| File | Action |
|---|---|
| `py/pytanga/blade_mask.py` | Add `from_array` classmethod |

---

## Upstream Dependencies

- None (pure Python, independent).
- **Downstream:** Phase 4 (`solver.py`) uses this to auto-compute `a_mask`
  in `product_matrix_array`.