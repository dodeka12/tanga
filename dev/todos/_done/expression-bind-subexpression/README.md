# Expression Bind-to-Subexpression — Overview

**Created:** 2026-09-17 | **Status:** Done | **Branch:** `feat/bind-expression`

## Goal

Let `Expression.bind(name=expr)` (and, through the shared evaluation path,
`Expression.__call__`) bind a variable to another **`Expression`** — genuine
function composition/substitution — instead of only to an `MV`/`DataArray`
(numeric) or a bare `Variable` (pure relabel).  "Wherever this variable appears,
replace it with this other expression's tensor, keeping that other expression's
free variables as the result's new axes."

This removes the `TypeError: binding for 'Omega_b' must be a single MV or
DataArray, got Expression` failure, and lets `wafer_grinding` (and similar
placement/rotation composition) build a placement-independent local operator
once, cache it, and derive the world-frame expression cheaply on every call by
substituting the sandwich sub-expressions.

Repeated occurrences of the bound variable are supported and must substitute
**consistently**: the sub-expression's own free variables become a single shared
block, so binding that free variable later feeds the same value to every
occurrence (the same semantics the existing `DataArray`/`MV` binding already
gives repeated variables).

## Architecture (short)

- `pytanga.expression` stores every `Expression` as an `MVLabeledTensor` whose
  axis 0 is the output axis labelled `OUT_LABEL` (`"k"`), followed by one axis
  per variable occurrence (integer block labels from `_labels.allocate_block`),
  then optional `None`-mask counting axes.
- `Expression._evaluate` already contracts a bound variable by appending one
  labelled tensor per occurrence to a `contract_labeled(*labeled)` einsum.  A
  sub-expression binding is the same idea, but the appended tensor is the inner
  expression's tensor with its **output axis relabelled onto the host variable's
  occurrence label(s)** and its free-variable axes re-keyed onto fresh blocks.
- `AffineExpression.bind`/`__call__` delegate per term to
  `Expression._evaluate`, so they inherit the feature with no new dispatch.
- File to edit: `py/pytanga/expression/_expression.py`.  Tests live in a new
  `py/tests/expression/test_bind_expression.py`.

## Canonical contract (fixed up front)

### 1. Value kinds accepted by a binding

`Expression.bind(**bindings)` and `Expression.__call__(**bindings)` accept a
third value kind for a variable, selected by type (unchanged for the other two):

| Value type | Behaviour |
|------------|-----------|
| `Variable` | pure relabel via `_substitute` (existing) |
| `MV` / `int` / `float` / `DataArray` | numeric contraction via `_evaluate` (existing) |
| `Expression` | **composition** via the new path below (new) |

### 2. `Expression._evaluate` composition branch

For a host variable `name` with occurrence labels `L = self._names[name]`
(`k = len(L)`) and mask `M = self._masks[name]`, binding `name` to an inner
`Expression inner`:

1. Require `inner.out_mask == M` (same algebra + same blade ids, via
   `BladeMask.__eq__`); else `ValueError` (mirrors `_substitute`'s "blade masks
   differ").
2. Require `not inner._has_counting_axes()`; else `ValueError` (v1 limitation —
   composing a batched sub-expression is out of scope).
3. Build `k` labelled tensors — one per occurrence label `l_j` — each a copy of
   `inner.tensor` with:
   - its output axis (`"k"`, position 0) renamed to `l_j` (mode `"*"`);
   - every free-variable axis relabelled so its variable gets one fresh,
     contiguous block of size `m_v * k` (see §3).
4. Append those tensors to `labeled` and run the existing
   `contract_labeled(*labeled)`.
5. Merge the inner free variables into the result's `_names`/`_masks` (they join
   the host's still-unbound variables), subject to the collision rules in §4.

### 3. Repeated-occurrence block expansion (consistent substitution)

For each inner free variable `v` with `m_v = len(inner.names[v])` internal
occurrences, allocate `block_v = allocate_block(m_v * k)`.  Copy `j` (`0..k-1`)
maps inner occurrence index `occ` (`0..m_v-1`) to `block_v[j * m_v + occ]`.

- `k == 1`: one copy, fresh block of size `m_v` (no reuse of inner labels).
- `k > 1`: every occurrence of the sub-expression contributes `m_v` occurrences
  of `v` to the **same** block, so a later `bind(v=mv)` / `bind(v=DataArray(...))`
  contracts one value against all of them — never treated as independent copies.
- Result `_names[v] = block_v`, `_masks[v] = inner.masks[v]`.

### 4. Collision rules (v1)

After composition, the introduced free names must not collide; otherwise
`ValueError` with a clear message:

- an inner free name equal to a **remaining** host variable name;
- an inner free name equal to a name being **substituted away** in the same call
  (self-referential substitution);
- the **same** free name introduced by two different inner bindings in one call.

Merging same-named inner variables across bindings (the "multiple attachments
share one operator" shape) is a **non-goal** for v1 and raises.

### 5. Degenerate cases

- A constant inner `Expression` (no free variables) composes exactly like binding
  its `MV` value (the result may still collapse fully, in which case `bind`
  raises its existing "fully collapsed" `ValueError`).
- `evaluate()` is unchanged in contract: it still requires a fully-bound `MV`
  result, so `evaluate(name=expr_with_free_vars)` raises "left variables
  unbound".

## Decisions (confirmed)

- Composition is implemented **in `Expression._evaluate`** (not only in `bind`),
  so `bind`, `__call__`, and `AffineExpression.bind/__call__` all share one path.
  This is a deliberate difference from the `Variable`-substitution feature, which
  was kept out of `__call__`/`evaluate` because a relabel is not a "value"; an
  `Expression` *is* a symbolic value, so evaluating with it is coherent.
- Repeated occurrences are **fully supported** via §3 block expansion, and are
  validated with a dedicated test (not deferred).
- Inner expressions carrying counting/batch axes are rejected in v1.
- Name collisions (inner free name vs. host name / substituted-away name /
  duplicate free name) raise `ValueError` in v1; merging same-named inner
  variables is out of scope.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-compose-expression-binding.md](./01-compose-expression-binding.md) | Add `_expression_binding_tensors` + wire the `Expression` branch into `_evaluate`; single-occurrence tests |
| 2 | [02-repeated-occurrence-composition.md](./02-repeated-occurrence-composition.md) | Validate the `m_v * k` block expansion for repeated occurrences + consistency tests |
| 3 | [03-affine-and-edge-cases.md](./03-affine-and-edge-cases.md) | `AffineExpression` composition, collision/error handling, edge cases + tests |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | User docs + explicit `bind_subexpression.py` example + changelog + full validation |

## Testing as you go

- Python: `uv run pytest py/tests/expression/test_bind_expression.py -q`
- Lint: `uv run ruff check py/pytanga/expression/_expression.py py/tests/expression/test_bind_expression.py`
- Types: `uv run ty check py/pytanga/expression`
- Example docs: `uv run python tools/generate-example-docs.py --check`
- Docs build: `uv run mkdocs build --strict`

## Non-goals

- No mask change / reindexing (the inner output mask must equal the variable mask).
- No composition of sub-expressions that carry counting/batch axes.
- No merging of same-named inner free variables introduced by *different* bindings
  in one call (raises for v1).
- No canonical label sharing across two *independent* `bind` calls, so two
  identically-composed results do not merge under `+` (each call allocates fresh
  blocks) — acceptable, matching how numeric binding behaves.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.

Relevant docs: `docs/py/ga/expression/index.md` and
`docs/py/ga/expression/usage.md` (the authoritative Python expression API);
`docs/dev/architecture/system-overview.md` (module layering).  This work is
additive (one private helper + one new branch in an existing method) and changes
no documented architecture.
