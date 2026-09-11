# Repeated Variables & Affine Expressions — Plan

**Created:** 2026-08-20 | **Status:** Done

## Goal

1. Allow the same variable to appear multiple times in a product (e.g. `v * v`),
   turning expressions from multilinear maps into multilinear forms (→ Hessians).
2. Introduce `AffineExpression`, a flat `list[Expression]`, created by `+`/`-`
   when two expressions cannot be broadcast-merged, so the system is closed
   under `+`, `-`, `*`.

## Motivation

Rotor-valued functions over an angle: build the multilinear form once and
evaluate it over many angles instead of constructing a new rotor per angle.
Repeated variables let a form carry products of the same input; the affine
wrapper lets sums of differently-shaped terms live in one object.

## Design

### 1. Repeated variables (one-to-many)

- `Expression.names` becomes `dict[str, tuple[str, ...]]` (name → ordered
  occurrence labels); `masks` stays per-name.
- **Canonical occurrence labels (decision 1):** each `Variable` owns a
  contiguous block of `D` labels, where `D` is the maximum occurrence degree
  (configurable, default e.g. 4).  The `k`-th occurrence of a variable uses
  `block[k]`, a deterministic function of (variable, occurrence index) — never
  the global allocator.  Consequences:
  - two independently built `v*v` share identical labels, so they broadcast-merge
    (`v*v + v*v == 2·(v*v)`, `v*v - v*v == 0`);
  - `AffineExpression` is needed only for genuinely different structures
    (degree mismatch, differing variable sets, or constants);
  - budget: `D` labels per variable, so roughly `50/D` live variables;
  - exceeding `D` occurrences raises a clear error.
- `_product`: on a repeated variable, take the next unused slot in that
  variable's block (occurrence index = left-to-right position in the term)
  instead of raising.  `v * v` reuses the ordinary bilinear product tensor
  `(out, v_a, v_b)`; binding `x` contracts both slots with the same value — no
  new tensor math.
- `__call__`: contract the bound value against every occurrence label of the
  name (one contraction tensor per occurrence, all carrying the same data).
- `inv`: require exactly one name with a single occurrence, no counting axes,
  square.
- **Merge condition must compare the ordered occurrence-label sequence** (the
  tensor's axis labels), not just the `names` dict: `names` maps a name to a
  tuple and cannot capture interleaved axis order (`v*w*v` vs `v*v*w` have equal
  `names` but different axis order).

### 2. AffineExpression

- Holds a flat `list[Expression]` (terms).  Output mask = union of term masks.
- Created by `_add` when operands cannot broadcast-merge (differing ordered
  label sequence, differing `masks`, or stacked terms).  Broadcast-merge stays
  the fast path; `E + c` and `v*w + v` become legal affine sums.
- `__call__` (partial and full): bind per term — a variable applies to every
  term that has it and is ignored by terms that do not; "fully bound" = no term
  has an unbound variable.
  - full single → sum of `MV`s
  - full batch → elementwise sum of `list[MV]`
  - partial → new `AffineExpression` of per-term partials
- `*` distributes over terms (`A * B` → terms `Ei * Fj`); `~`/`.conj()`/scalar
  scale/`-` distribute.  `inv` only on a single linear (single-occurrence) term.

### 3. Building blocks

- `_to_expression` already promotes `MV` → zero-variable `Expression` (constant),
  keeping the term list homogeneous under partial binding.
- **New:** promote a fully-bound batch (`list[MV]`) → zero-variable `Expression`
  with a counting axis (stacked constant), so terms stay homogeneous under
  batched partial evaluation.
- Defer tensor addition to full evaluation; no cross-term batch-label
  coordination is needed (terms are summed, not contracted together).

## Decisions

1. **Canonical occurrence labelling:** per-variable fixed label sets (option a).
2. **Batch-partial representation:** keep the counting-axis (one-einsum)
   semantics of `Expression`, adding the stacked-constant primitive.
3. **Blade checks:** validate a binding against the union of its per-term masks,
   while contraction uses each term's own mask.
4. **Simplification:** none — collapse happens only via broadcast-merge
   (`v*v + v*v`, `E - E`); like-term collection across different structures is
   out of scope.

## Implementation steps

Ordered so each step is independently testable and no later step refactors an
earlier one: variable label blocks → repeated variables → affine wrapper → docs.

### Step 1 — Per-variable label blocks ✅

- Add `MAX_DEGREE` (`D`, default 4) to `_labels.py`; `Variable` creation
  allocates a contiguous block of `D` labels (`allocate_block(D)`) instead of
  one.  `Variable.labels` exposes the tuple; `Variable.label` returns
  `labels[0]` (backward compatible).  The alphabet budget becomes
  `floor(50/D)` live variables.
- **Tests:** blocks are contiguous and deterministic across builds; `label` is
  the first label; creating `floor(50/D)+1` variables raises; existing suites
  stay green (update `test_labels.py`, `test_variable.py` for the new budget).

### Step 2 — Repeated variables (build & evaluate `v * v`) ✅

- Migrate `Expression.names` to `dict[str, tuple[str, ...]]` (single-occurrence
  entries are 1-tuples); update `__call__`, `_product`, `_add`, `inv`,
  `_involution`, `repr`, and the `names`/`masks` properties accordingly.
- `_product`: on a repeated variable, assign the next unused slot in that
  variable's block (left-to-right occurrence order) instead of raising; a degree
  `> D` repeat raises a clear error.
- `__call__`: contract the bound value against every occurrence label of a name.
- `inv`: require exactly one name with a single occurrence (plus the existing
  no-counting + square checks).
- `_add`: merge iff the ordered occurrence-label sequences (and per-axis masks)
  match, not merely `names` equality.
- **Tests:** `v*v == x*x`; `v*v*v`; `v*v + v*v` merges to one tensor and
  `v*v - v*v == 0`; `v*w*v` vs `v*v*w` do not merge; `inv` on `v*v` raises;
  degree `> D` raises; full existing suite stays green.

### Step 3 — AffineExpression (sums of non-mergeable expressions) ✅

- New `AffineExpression` holding a flat `list[Expression]`; `out_mask` = union
  of term masks; `names` = union of term names.
- `_add`/`_sub` fallback: when broadcast-merge fails (differing label sequence,
  differing masks, or stacked terms), return `AffineExpression`.  Handle
  `Expression ± MV`, `Expression ± AffineExpression`, and
  `AffineExpression ± AffineExpression` (list concat).  Extend `Expression`'s
  `__add__`/`__sub__`/`__radd__`/`__rsub__` to route to it.
- `AffineExpression.__call__`: bind per term (apply a variable to every term
  that has it, ignore otherwise); full single → summed `MV`, full batch →
  elementwise summed `list[MV]`, partial → `AffineExpression` of per-term
  partials.  Promote `MV` → 0-var `Expression` (`_to_expression`) and
  `list[MV]` → stacked constant `Expression` (new primitive) to keep terms
  homogeneous.
- Operators distribute: `*`, `~`, `.conj()`, scalar scale, `-`, `/`.  `inv`
  only on a single linear (single-occurrence) term; on an affine object it
  raises.
- **Tests:** `v*v + w` and `E + c` produce affine; full/partial/batched-partial
  evaluation; `A * B` distributes; `~A`, `2*A`, `-A`; `A.inv(...)` raises;
  mixed-mask blade-check uses the union of per-term masks.

### Step 4 — Docs, changelog, examples, benchmark ✅

- Update `docs/py/expression/usage.md` (and `index.md` if needed) for repeated
  variables, `AffineExpression`, and the new label budget; add a changelog
  bullet; add an example (e.g. a rotor-valued function using `v*v`); extend
  `dev/src/dev_expression_bench.py`.
- **Verification:** docs render; examples and benchmark run; full test suite
  green.

## Non-goals

- Automatic differentiation / symbolic gradients (repeated vars are the building
  block for Hessians, not a full AD pass).
- Automatic canonical-form / like-term collection.

## Verification

- Unit tests: `v*v` quadratic eval; `v*v*v`; `v*v - v*v == 0` (merge);
  `v*w*v` vs `v*v*w` not merged (axis-order guard); degree `> D` error;
  `v*v + w` affine add; `A * B` distribution; partial & batched partial through
  affine; `inv` guards; mixed-mask blade-check union.
