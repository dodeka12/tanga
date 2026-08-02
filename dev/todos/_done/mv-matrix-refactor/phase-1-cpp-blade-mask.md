# Phase 1 — C++ Mask-Based Blade-Mask Functions + Bindings

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing  
> any step in this plan.

## Goal

Add C++ overloads of `_EvalProductBladeMask` and the public `EvalProductBladeMask_*`
wrappers that accept a `CBladeMask` (`xMaskA`) instead of a multivector (`wA`).
Bind these new functions in the pybind11 template so the Python `MVSolver` can
call them with blade masks directly.

---

## Current State

The blade-mask prediction functions in `Matrix_MapToBladeMask.h` take `wA` (a
multivector) and iterate over its blades:

| C++ Function | Signature |
|---|---|
| `_EvalProductBladeMask` (internal) | `(xMaskC, wA, xMaskB, left, complete, op)` |
| `EvalProductBladeMask_GP` | `(xMaskC, wA, xMaskB, left, complete)` |
| `EvalProductBladeMask_IP` | `(xMaskC, wA, xMaskB, left, complete)` |
| `EvalProductBladeMask_OP` | `(xMaskC, wA, xMaskB, left, complete)` |

No mask-based variant exists — the caller must always provide a multivector.

---

## Steps

### Step 1.1 — Add mask-based `_EvalProductBladeMask` overload

**File:** `cpp/Tan.GA/Matrix_MapToBladeMask.h`

Add a new overload of `_EvalProductBladeMask` that takes `xMaskA` (a
`CBladeMask`) instead of `wA` (a multivector).  This mirrors the existing
3-mask `_EvalProductMatrix` overload pattern.

The signature is:

```cpp
template<typename TBlade, typename FuncOp>
void _EvalProductBladeMask(GA::CBladeMask<TBlade>& xMaskC,
        const GA::CBladeMask<TBlade>& xMaskA,
        const GA::CBladeMask<TBlade>& xMaskB,
        bool bLeftToRight,
        bool bComplete,
        FuncOp xFuncOp)
```

Implementation:
- Reset `xMaskC`.
- If not `bComplete`: iterate `xMaskA` via `ForEachBlade`, calling
  `_EvalProductBladeMask_InnerLoop` for each blade.
- If `bComplete`: iterate to a fixed point — same do/while pattern as
  the existing MV-based overload, but using `xMaskA.ForEachBlade` instead
  of `wA.ForEachBlade`.

Place this overload immediately after the existing MV-based
`_EvalProductBladeMask` template (which takes `wA` as second parameter).

### Step 1.2 — Add public mask-based `EvalProductBladeMask_*` wrappers

**File:** `cpp/Tan.GA/Matrix_MapToBladeMask.h`

Add three new overloads — one per product — each taking `xMaskA` instead
of `wA`.  Place each after its corresponding 2-parameter (MV-based) variant.

#### `EvalProductBladeMask_GP` (mask-based overload)

```cpp
template<typename TBlade>
void EvalProductBladeMask_GP(GA::CBladeMask<TBlade>& xMaskC,
        const GA::CBladeMask<TBlade>& xMaskA,
        const GA::CBladeMask<TBlade>& xMaskB,
        bool bLeftToRight = true,
        bool bComplete = false)
{
    _EvalProductBladeMask(xMaskC, xMaskA, xMaskB, bLeftToRight, bComplete,
            [](unsigned& uSign, TBlade& blC, const TBlade& blA, const TBlade& blB) -> bool
            { return GA::GPSign(uSign, blC, blA, blB); });
}
```

#### `EvalProductBladeMask_IP` (mask-based overload)

Same pattern, using `GA::IPSign` as the lambda.

#### `EvalProductBladeMask_OP` (mask-based overload)

Same pattern, using `GA::OPSign` as the lambda.

> **Note:** These are overloads — the existing MV-based signatures remain
> unchanged for backward compatibility.  Python bindings will call the new
> mask-based forms directly.

### Step 1.3 — Bind new C++ functions in the template

**File:** `py/pytanga/_template.cpp`

Add three new placeholder slots after the existing blade-mask bindings
(before `{REDUCE_DEF}`):

```
{PRODUCT_BLADE_MASK_GP_A_DEF}
{PRODUCT_BLADE_MASK_IP_A_DEF}
{PRODUCT_BLADE_MASK_OP_A_DEF}
```

### Step 1.4 — Add Python codegen fragments

**File:** `py/pytanga/_codegen.py`

Add three generator functions, one per product.  Each accepts `a_ids`
(the blade ids of A's mask) and `col_ids` (the B mask), and returns
the predicted output blade ids (the C mask).

#### `_product_blade_mask_gp_a_def()`

```python
def _product_blade_mask_gp_a_def() -> str:
    return """
    m.def("product_blade_mask_gp_a", [](const std::vector<uint32_t>& a_ids,
            const std::vector<uint32_t>& col_ids,
            bool left_to_right, bool complete) {
        Tan::GA::CBladeMask<TBlade> xMaskA, xMaskB, xMaskC;
        for (auto id : a_ids)   xMaskA.Insert(TBlade(id));
        for (auto id : col_ids) xMaskB.Insert(TBlade(id));
        Tan::GA::EvalProductBladeMask_GP(xMaskC, xMaskA, xMaskB, left_to_right, complete);
        std::vector<uint32_t> ids;
        xMaskC.ForEachBlade([&](unsigned, const TBlade& bl) {
            ids.push_back(static_cast<uint32_t>(bl.GetId()));
        });
        return ids;
    }, py::arg("a_ids"), py::arg("col_ids"),
        py::arg("left_to_right") = true, py::arg("complete") = false,
       "Predict output blade ids of GP from A-mask and B-mask.");
"""
```

Repeat for `_product_blade_mask_ip_a_def` and `_product_blade_mask_op_a_def`,
calling `EvalProductBladeMask_IP` and `EvalProductBladeMask_OP` respectively.

#### Wire replacements in `generate()`

Add these lines to the `generate()` function, in the same area as the other
dtype-independent replacements (after the blade-ops block, before the return):

```python
template = template.replace("{PRODUCT_BLADE_MASK_GP_A_DEF}", _product_blade_mask_gp_a_def())
template = template.replace("{PRODUCT_BLADE_MASK_IP_A_DEF}", _product_blade_mask_ip_a_def())
template = template.replace("{PRODUCT_BLADE_MASK_OP_A_DEF}", _product_blade_mask_op_a_def())
```

---

## Status

✅ **Complete** — all steps implemented.

---

## Verification

After completing all steps:

1. Build a binding and confirm the three new Python functions exist:
   ```python
   alg = pytanga.Algebra(3, 0)
   mod = alg._mod
   mod.product_blade_mask_gp_a  # should exist
   mod.product_blade_mask_ip_a  # should exist
   mod.product_blade_mask_op_a  # should exist
   ```

2. Test mask-based prediction returns correct output blades:
   ```python
   a_ids = [1, 2]      # e1, e2
   b_ids = [1, 2, 4]   # e1, e2, e3
   c_ids = mod.product_blade_mask_gp_a(a_ids, b_ids, True, False)
   # Should contain blade 0 (scalar) from e1*e1 and e2*e2
   assert 0 in c_ids
   ```

---

## Files Touched

| File | Action |
|---|---|
| `cpp/Tan.GA/Matrix_MapToBladeMask.h` | Add `_EvalProductBladeMask` mask overload + 3 public wrappers |
| `py/pytanga/_template.cpp` | Add 3 placeholder slots |
| `py/pytanga/_codegen.py` | Add 3 fragment generators + wire replacements |