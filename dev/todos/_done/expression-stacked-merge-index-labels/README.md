# Expression stacked merge + integer axis labels — Overview

**Created:** 2026-09-02 | **Status:** Done | **Branch:** `fix/expressions`

## Goal

Extend the expression subsystem in two ways:

1. Let `+`/`-` merge two stacked (batched) `Expression`s that already share the
   same axis layout, and let `*` compose a stacked expression with a constant
   MV or a `Variable` operand. This makes per-correspondence constraints such as
   `(M·X)(X=batch) − (Y·M)(Y=batch)` produce a single stacked `Expression`
   instead of raising `ValueError` (see
   `dev/notes/pytanga-batched-expression-merge.md`).
2. Replace the exhaustible letter-based variable-label pool with integer axis
   labels, and extend `MVLabeledTensor` so an axis label may be a `str` (single
   letter) or an `int` (pool index). Classes that instantiate many `Variable`s
   no longer run out of names.

## Background

- `_add` (`py/pytanga/expression/_expression.py`) unconditionally refuses
  stacked operands *before* its existing raw-label merge branch. The note shows
  the guard is over-conservative: when the raw axis labels match, the merge is a
  plain element-wise `+`/`-` of tensor data.
- `_product` (`py/pytanga/expression/_expression.py`) has a similar guard for
  `*`. It is conservative for a different reason: the builder threads
  variable/constant axes through a single `np.einsum` but does not yet carry the
  element-wise (`_`) mode of counting axes, so it would mis-label them. See
  [02-product-stacked-guard.md](./02-product-stacked-guard.md) for the full
  explanation and the chosen relaxation.
- Variable labels come from a global 50-letter alphabet in
  `py/pytanga/expression/_labels.py`; each `Variable` consumes a `MAX_DEGREE`
  block forever, so `max_variables()` is 12. The contraction path
  (`py/pytanga/tensor/ops.py::contract_labeled`) builds `numpy.einsum` *string*
  subscripts, which caps distinct axis names at 52 letters.

## Decisions (confirmed)

- Unbound `M·X − Y·M` (X and Y with the same blade mask) stays an
  `AffineExpression`; only the *bound* form merges. Blade-mask equality does not
  make two distinct variables one.
- `_add` merges stacked operands **iff** their ordered axis-name sequences
  (`_axis_names`) are equal; otherwise it keeps raising. Mismatched counting-axis
  lengths surface as a NumPy broadcast error inside the merge.
- `_product` relaxes to allow **at most one** stacked operand; the other side may
  be a constant MV or a `Variable`. Two stacked operands remain rejected
  (element-wise zip semantics are out of scope).
- `MVLabeledTensor.labels` changes from a `str` to a structured tuple of
  `AxisLabel(name, mode)` values where `name: str | int`. `AxisLabel` is a public
  frozen dataclass (exported from `pytanga.tensor`) that owns validation,
  rendering, and the `is_elemwise`/`is_contract` predicates. String *input* stays
  supported; this is a deliberate breaking change to the stored attribute (and
  to a handful of tensor tests that assert `.labels == "..."`).
- Contraction switches from `einsum` string subscripts to the list form, so
  integer names work and the 52-letter ceiling disappears.
- Variables use a monotonic integer pool: `Variable.labels` becomes a
  `tuple[int, ...]` and `Variable.label` becomes an `int`; `Variable.name` stays
  the user-facing string key. `OUT_LABEL` stays the reserved string `"k"`, and
  batch/counting labels keep the per-evaluation letter pool
  (`_next_batch_label`).

### Fixed contract

```python
# py/pytanga/tensor/_labeled.py
AxisName = str | int          # str = single ASCII letter (legacy), int = pool index

@dataclass(frozen=True, slots=True)
class AxisLabel:
    """One labeled-tensor axis: a name plus a contraction/element-wise mode."""
    name: AxisName
    mode: str = "*"           # "*" contraction, "_" element-wise

    def __post_init__(self) -> None:
        if isinstance(self.name, bool) or not isinstance(self.name, (str, int)):
            raise TypeError(f"axis name must be str or int, got {type(self.name).__name__}")
        if self.mode not in ("*", "_"):
            raise ValueError(f"axis mode must be '*' or '_', got {self.mode!r}")

    @property
    def is_elemwise(self) -> bool: return self.mode == "_"
    @property
    def is_contract(self) -> bool: return self.mode == "*"
    def __str__(self) -> str: return f"{self.name}{self.mode}"

# MVLabeledTensor
tensor: MVTensor
labels: tuple[AxisLabel, ...]            # canonical, one AxisLabel per axis

# MVLabeledTensor(tensor, labels) accepts for `labels`:
#   str                           -> legacy canonicalisation ("kij", "k*i*j*", "i*n_")
#   AxisName                      -> single axis, mode "*"
#   Iterable[AxisName]            -> each mode "*"
#   Iterable[AxisLabel]           -> used as-is (validated)
#   Iterable[tuple[AxisName, str]] -> coerced to AxisLabel (convenience)

# Canonical accessors (stable across every phase):
_axis_names(labels) -> tuple[AxisName, ...]   # tuple(ax.name for ax in labels)
_axis_modes(labels) -> tuple[str, ...]        # tuple(ax.mode for ax in labels)
_canonicalise(s: str) -> str                  # legacy string parsing (unchanged)
_labels_str(labels) -> str                    # "".join(str(ax) for ax in labels), letters only
```

```python
# py/pytanga/expression/_labels.py
allocate_block(size: int = MAX_DEGREE) -> tuple[int, ...]   # monotonic integer pool
block_for_label(label: int) -> tuple[int, ...]              # full occurrence block
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-stacked-add-sub-merge.md](./01-stacked-add-sub-merge.md) | Let `+`/`-` merge stacked expressions with identical axis layouts. |
| 2 | [02-product-stacked-guard.md](./02-product-stacked-guard.md) | Explain and relax `_product`'s stacked guard (one stacked operand). |
| 3 | [03-structured-axis-labels-and-contraction.md](./03-structured-axis-labels-and-contraction.md) | Structured `AxisLabel` (`str | int` names) + list-form contraction. |
| 4 | [04-integer-variable-pool.md](./04-integer-variable-pool.md) | Integer pool for `Variable` labels + expression integration. |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Update docs and write the branch changelog. |

## Testing as you go

- Python expression tests: `uv run pytest py/tests/expression/ -q`
- Python tensor tests: `uv run pytest py/tests/tensor/ -q`
- Full suite (final phase): `uv run pytest`
- Lint: `uv run ruff check py/pytanga/expression py/pytanga/tensor`
- Docs build (final phase): `uv run mkdocs build --strict`

## Non-goals

- No merge of the *unbound* `M·X − Y·M` into a single term — it remains an
  `AffineExpression`.
- No element-wise zip semantics for `stacked * stacked` (two stacked operands) —
  `_product` keeps rejecting it.
- No removal of the legacy string label input path.
- No change to the C++ core or the blade-mask/product-tensor machinery.
