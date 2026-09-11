# Variable / Expression System for GA Equations

**Created:** 2026-08-20 | **Status:** Done

## Goal

Add a lightweight symbolic layer for composing GA equations where only a few
elements change during an animation or optimization. A `Variable` is a named
slot with a fixed `BladeMask` (its "type"). Combining variables with constant
multivectors (and with each other) builds an `Expression` that eagerly bakes
the constant operands into a product tensor, leaving one labelled axis per
live variable plus one output axis. Evaluating the expression against concrete
multivectors returns fresh `MV`s (or a batched `list[MV]`), reusing the
existing `pytanga.tensor` stack for all contraction work.

## Background (existing building blocks)

Everything below already exists and is reused as-is:

- `py/pytanga/blade_mask/_mask.py` — `BladeMask(alg, ids=…, grades=…)`,
  `BladeMask(mv)`, `BladeMask([mvs])`, `.ids`, `.union`.
- `py/pytanga/tensor/product.py` — `product_tensor(a_mask, b_mask,
  c_mask=None, product=GP|IP|OP, left=, a_inv/b_inv/c_inv=EInv)` → 3-D ±1
  `MVTensor` with masks `(c, a, b)`; `product_tensor_rev/conj` → diagonal
  sign tensors for involutions.
- `py/pytanga/tensor/ops.py` — `contract(subscripts, *tensors)` and
  `contract_labeled(*labeled_tensors)` (label-driven einsum with `*`=contract,
  `_`=element-wise modes).
- `py/pytanga/tensor/convert.py` — `to_tensor(mv|list, mask=…)` (rank-1 single,
  rank-2 list with a `None` batch axis) and `from_tensor(t)` (MV or nested
  `list[MV]`).
- `py/pytanga/tensor/_labeled.py` — `MVLabeledTensor(tensor, labels)` with
  single-letter labels; `*`, `+`, `-`, transpose.
- `py/pytanga/blade_mask/predict.py` — `product_blade_mask(a_mask, b_mask,
  product=, left=)` to predict the output mask.
- `py/pytanga/algebra` — `EProduct`, `EInv` enums; `MV`.

## Guiding decisions (agreed in discussion)

1. **GP, IP, OP all supported** — `product_tensor` already encodes all three,
   so `*`, `|`, `^` come for free, plus reverse/conjugate via `EInv`.
2. **Constants contracted eagerly** — every `*`/`|`/`^` builds the product
   tensor and immediately contracts constant operands, so the stored tensor has
   exactly one output axis + one axis per remaining variable.
3. **Fresh MV on evaluation** — `from_tensor` builds new MVs; no scratch-buffer
   aliasing.
4. **Single-letter labels, auto-assigned** (v1) — `MVLabeledTensor`/`contract`
   use single-letter einsum labels. A `Variable` gets one stable letter at
   construction; a reserved `OUT_LABEL` marks the output axis of every
   expression. Documented cap of ~51 live variables.
5. **Addition/subtraction supported** — pointwise via broadcast-add after
   unifying the **union** output mask; requires **identical variable sets**
   (a sum is a single multilinear map only over shared axes). Constants and
   differently-variable sums are rejected — affine expressions are out of scope.
6. **Batched evaluation** — `E(V1=[...])` contracts the variable axis against a
   rank-2 `(mask, None)` tensor and returns `list[MV]` (nested list for several
   batched variables) in a single einsum.
7. **Involutions via existing sign tensors** — reverse (`~`) and Clifford
   conjugate (`.conj()`) are already available as diagonal ±1 tensors
   (`product_tensor_rev`/`product_tensor_conj`) and as `EInv` on
   `product_tensor`. The expression layer applies them by contracting the sign
   tensor onto the output axis (or a variable axis), and can bake them into a
   product at build time via `a_inv`/`b_inv`/`c_inv`.

## Files

- Add: `py/pytanga/expression/__init__.py`
- Add: `py/pytanga/expression/_variable.py`
- Add: `py/pytanga/expression/_expression.py`
- Add: `py/pytanga/expression/_labels.py` (name→letter allocator + OUT_LABEL)
- Add: `py/tests/expression/test_variable.py`
- Add: `py/tests/expression/test_expression.py`
- Add: `dev/src/dev_expression_bench.py`
- Add: `py/examples/expression/variable_rotor.py`
- Add: `py/examples/expression/equation_demo.py`
- Add: `docs/py/expression/index.md` + `docs/py/expression/usage.md`
- Modify: `py/pytanga/__init__.py` (export `Variable`, `Expression`)
- Modify: `mkdocs.yml` (register the `Expression` nav entry under Python docs)
- Modify: `docs/changelog/<branch>.md` + `docs/changelog/index.md` (per
  `dev/workflows/changelog.md`)

## Steps

### Step 1 — `_labels.py`: name→letter allocator

- [x] Add module constants: `OUT_LABEL = "k"`, `BATCH_LABEL = "n"`, and the
      variable alphabet `"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"`
      with both reserved letters removed (50 letters).
- [x] `allocate_label() -> str` — returns the next unused letter, raising
      `RuntimeError` on exhaustion (>50 live variables). Stable per `Variable`
      instance (assigned once, stored on the variable).
- [x] Reserve `BATCH_LABEL = "n"` globally for the transient count axis used in
      batched bindings (kept out of the variable alphabet to avoid collisions).

### Step 2 — `_variable.py`: the `Variable` class

- [x] `Variable(name: str, mask: BladeMask)` — stores `name`, `mask`, and the
      allocated `_label`; expose `name`, `mask`, `algebra` (from `mask`),
      `label` (read-only).
- [x] Operator overloads that each return an `Expression` via the builder in
      `_expression.py`:
      - `__mul__` / `__rmul__` (GP, incl. `MV`, `Variable`, scalar),
      - `__or__` / `__ror__` (IP),
      - `__xor__` / `__rxor__` (OP),
      - `__neg__`, `__invert__` (reverse), `conj()` (Clifford conjugate) — see
        Step 5.
- [x] `__repr__` → `Variable('V1', BladeMask([...]))`.

### Step 3 — `_expression.py`: build + evaluate a single product

- [x] `Expression` dataclass/frozen holding: `tensor: MVLabeledTensor`,
      `names: dict[str, str]` (name → label), `masks: dict[str, BladeMask]`,
      `out_label = OUT_LABEL`, and a cached `out_mask`.
- [x] `Expression.tensor` (read-only property) — expose the internal reduced
      `MVLabeledTensor` so callers can inspect it or run their own further
      contractions; also expose `out_mask`, `names`, and `masks` as read-only
      properties for introspection/debugging.
- [x] `_product(left, right, product: EProduct, invs) -> Expression`:
      - resolve each operand to a labelled `MVLabeledTensor`:
        - `Variable` → rank-1 placeholder with its mask + label (no data needed
          beyond the axis),
        - `MV` → `to_tensor(mv, mask=BladeMask(mv))` labelled with a throwaway
          contraction letter,
        - `Expression` → its stored tensor/names/masks (merge name maps),
      - `c_mask = product_blade_mask(a_mask, b_mask, product=product)`,
      - `O = product_tensor(a_mask, b_mask, c_mask, product=product, left=True,
        a_inv=…, b_inv=…)`,
      - contract constant operands eagerly via `contract_labeled` (constants
        disappear; variable axes survive),
      - wrap the reduced tensor + merged name/mask maps + `OUT_LABEL` in an
        `Expression`.
- [x] `Expression.__call__(**bindings) -> MV` (single value; `list[MV]` →
      Step 6):
      - validate each key is a known variable name and each value is an `MV`
        whose non-zero blades ⊆ that variable's `mask`;
      - `to_tensor(value, mask=…)` per binding; `contract_labeled` the
        expression tensor with all bindings; `from_tensor` → `MV`.
- [x] `Expression.__mul__`/`__or__`/`__xor__` (and reflected) chain into
      `_product` so `(v1 * a) * b` keeps reducing constants.

### Step 4 — Addition / subtraction with mask unification

- [x] `_reindex_output(expr, union_mask)` — pad an expression's output axis to
      a union `BladeMask`, zero-filling blades absent from the expression.
- [x] `_add(left, right, subtract=False)` — unify output masks (via
      `BladeMask.union` + `_reindex_output`) then broadcast add/sub.  Requires
      **identical variable sets** (`names` dicts equal): a sum of tensor
      expressions is a single multilinear map only when both share the exact
      same variables/axes; constants and differently-variable sums are rejected
      with `ValueError` (they would be affine, not linear).
- [x] `Expression.__add__` / `__sub__` / `__neg__` — dispatch to `_add`;
      `__neg__` is a scalar scale.
- [x] `__radd__`/`__rsub__` fast paths for `0 + E`, `E + 0`, `E - 0`, `0 - E`.

### Step 5 — Involutions (reverse & conjugate) + scalar ops

The two involutions already available as tensors are **reverse**
(`product_tensor_rev(mask)`) and **Clifford conjugate**
(`product_tensor_conj(mask)`); both are diagonal |mask|×|mask| ±1 tensors.
`EInv` (`ID`/`REV`/`CONJ`) exposes the same signs through
`product_tensor(..., a_inv/b_inv/c_inv=…)`.

- [x] `_involution_tensor(mask, inv: EInv) -> MVTensor` — return
      `product_tensor_rev(mask)` for `EInv.REV` and
      `product_tensor_conj(mask)` for `EInv.CONJ` (diagonal sign tensor with
      masks `(mask, mask)`).
- [x] `_apply_involution(expr, inv) -> Expression` — multiply the output axis
      (axis 0) by the involution's sign diagonal; used by `~E` and `E.conj()`.
- [x] `Expression.__invert__` (`~E`) → `_apply_involution(expr, EInv.REV)`.
- [x] `Expression.conj()` → `_apply_involution(expr, EInv.CONJ)`.
- [x] `Variable.__invert__` (`~v`) and `Variable.conj()` → wrap
      `_involution_tensor(v.mask, …)` as a 2-axis `Expression` (variable axis +
      output axis, both `v.mask`) so `~v` composes in products and additions.
- [x] Build-time involutions: `v * ~a` works because `~a` on a constant `MV`
      already returns `a.rev()` before building (`_product` also accepts
      optional `a_inv`/`b_inv` for future use).

Scalar ops:

- [x] `Expression.__mul__`/`__rmul__` with `int`/`float` → scale the tensor
      data (`mul_scalar`).
- [x] `Expression.__truediv__` by scalar.
- [x] `Expression.__neg__` → scale by −1.

### Step 6 — Batched evaluation (`E(V1=[...])`)

- [x] In `__call__`, detect `list[MV]` values:
      - `to_tensor(list, mask=…)` → rank-2 `(mask, None)` with the count axis
        labelled element-wise (`_` mode) using a fresh batch label (one per
        batched variable),
      - `contract_labeled` → rank-2 `(out_mask, None)` → `from_tensor` →
        `list[MV]`,
      - several batched variables → higher-rank tensor → nested `list[MV]`.
- [x] Verify a single batched einsum (no Python loop over the list).

### Step 7 — Public API + exports

- [x] `py/pytanga/expression/__init__.py` exports `Variable`, `Expression`.
- [x] `py/pytanga/__init__.py` re-exports `Variable`, `Expression` and adds them
      to `__all__`.
- [x] Docstrings + a short usage example in the module docstring.

### Step 8 — Tests

- [x] `test_labels.py`: label allocation (uniqueness, reserved letters, 50-var
      exhaustion limit).
- [x] `test_variable.py`: construction, properties, repr, mask type-check,
      public imports.
- [x] `test_expression.py`:
      - GP/IP/OP of `Variable * MV` equals the direct `MV` operation (E3 + N3),
      - two-variable expression `v1 * v2` matches `mv1 * mv2`,
      - constant folding: `v1 * a * b` equals `v1 * (a*b)`,
      - `E.tensor` returns the internal `MVLabeledTensor` with the expected
        masks and labels (one output axis + one axis per variable),
      - `~E` and `E.conj()` match `MV.rev()`/`MV.conj()` on the evaluated
        result (E3 + N3, incl. an N3 mixed-grade MV),
      - `~v` / `v.conj()` as a factor: `(a * ~v)(V1=x)` == `a * x.rev()`,
      - build-time involution: `v * ~a` == `v * (a.rev())`,
      - `+`/`-` with and without mask unification; `(v1*a) + (v1*b) == v1*(a+b)`,
      - batched `E(V1=[...])` returns `list[MV]` matching per-item evaluation,
        and nested lists for several batched variables,
      - no-aliasing: two calls return distinct `MV` objects,
      - error cases (unknown name, value outside mask, mismatched algebra,
        quadratic rejected).
- [x] Run `uv run pytest py/tests/expression/` green.

### Step 9 — Benchmark

- [x] `dev/src/dev_expression_bench.py`: build `E = R * v * ~R` (apply a fixed
      rotor to a variable vector) once, then compare single eval vs. the fresh
      sandwich and batched eval vs. a Python loop.
- [x] Finding: single eval is overhead-bound (~50 µs vs ~4 µs fresh GP), but
      the follow-up C++ batch converter (`to_matrix_batch`/`from_matrix_batch`)
      makes batched eval ~1.8× faster than a Python loop.

### Step 10 — Examples

- [x] Add `py/examples/expression/variable_rotor.py` — apply a fixed rotor
      `E = R * v * ~R` to a variable point, singly and as a batch (the
      higher-level counterpart to `py/examples/tensor/rotor_01.py`).
- [x] Add `py/examples/expression/equation_demo.py` — GP/IP/OP products,
      addition over a shared variable, a two-variable product, and involutions
      (`~E`, `E.conj()`).
- [x] Keep examples runnable with `uv run python py/examples/expression/...`.

### Step 11 — Docs + changelog

- [x] Add `docs/py/expression/index.md` — overview, `Variable`/`Expression`
      concepts, and a pointer to the examples.
- [x] Add `docs/py/expression/usage.md` — build/evaluate, batching,
      addition/subtraction, involutions, and the 50-variable label cap.
- [x] Register a new `Expression` entry in `mkdocs.yml` under
      `Python Documentation` (after `Tensor Operations`).
- [x] Add a **New Features** bullet to the branch changelog per
      `dev/workflows/changelog.md` (and update `docs/changelog/index.md` at PR
      time, after the hash rename).

## Verification (end-to-end)

- [x] `uv run pytest py/tests/expression/` passes (full suite: 1552 passed).
- [x] `uv run python dev/src/dev_expression_bench.py` runs and reports the
      single-vs-batched numbers.
- [x] `uv run python py/examples/expression/variable_rotor.py` and
      `.../equation_demo.py` run without error.
- [x] `uv run ruff check py/pytanga/expression py/tests/expression
      dev/src/dev_expression_bench.py` and `uv run ruff format --check …`
      clean.
- [x] `uv run python -c "import pytanga; pytanga.Variable, pytanga.Expression"`
      works.

## Non-goals / optional follow-ups

- **Names-in-labels** — replacing the single-letter allocator with a per-axis
  name tuple + integer-list `np.einsum` (drops the 51-variable cap and the
  name→letter map). Deferred; the label handling is isolated in `_labels.py` +
  `Expression` so this is a localized change later.
- **Expression trees with shared sub-expressions / common-subexpression
  elimination** — out of scope; each `Expression` stores a reduced tensor, and
  products chain eagerly.
- **Automatic differentiation / Jacobians** for optimization — not in v1; the
  batched evaluation gives a fast finite-difference path but no symbolic
  derivatives.
- **Affine expressions (linear + constant)** — `E + c` is affine, not a single
  linear tensor contraction, so it is rejected; add constants after evaluation
  (`E(...) + c`) instead.
- **Top-level `Algebra.create_variable(...)` factory** — nice-to-have sugar;
  `Variable(name, mask)` is sufficient for v1.
- **Grade involution / grade-conjugate as tensors** — `MV.grade_involution()`
  and `MV.grade_conj()` exist, but only reverse and Clifford conjugate are
  exposed as sign tensors (`product_tensor_rev`/`_conj`). A `(-1)^k` grade-
  involution tensor is a trivial follow-up if needed; v1 exposes only the two
  available tensor involutions.
