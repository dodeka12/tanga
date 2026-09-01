# Feature request: allow `+`/`-` to merge structurally identical stacked (batched) Expressions


## Summary

`Expression.__add__`/`__sub__` (via the private `_add()` in
`pytanga/expression/_expression.py`) unconditionally refuses to combine two
`Expression` operands if *either* one carries a counting (batch) axis:

```python
def _add(left, right, subtract: bool = False):
    L = _to_expression(left)
    R = _to_expression(right)
    if L._has_counting_axes() or R._has_counting_axes():
        raise ValueError("cannot add a stacked (batched) expression; fully evaluate it before addition")
    if _raw_names(L.tensor.labels) == _raw_names(R.tensor.labels):
        ...  # merge into one Expression
    return AffineExpression(...)
```

This guard runs *before* the existing raw-label-equality check that already
decides whether two (non-batched) expressions may merge. So even when both
stacked operands are byte-for-byte structurally identical — same variable
name, same variable mask, same output mask, same counting-axis label *and*
length — the library still refuses to merge them and raises instead of
falling through to the (already-correct) merge branch.

## Minimal repro

Building a per-correspondence "sandwich" constraint (`motor * X_i - Y_i *
motor = 0`) by binding `X`/`Y` to their own batches, keeping `motor` free:

```python
from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, Motor, Point

N3 = BasisN3()
geo = Geometry(N3)
motor = geo.create_var("motor", Motor)
X = geo.create_var("X", Point)
Y = geo.create_var("Y", Point)

local_points = [geo(Point(0, 0, 0)), geo(Point(1, 0, 0)), geo(Point(0, 1, 0))]
world_points = [geo(Point(1, 2, 3)), geo(Point(2, 2, 3)), geo(Point(1, 3, 3))]

lm = (motor * X)(X=("n", local_points))
rm = (Y * motor)(Y=("n", world_points))

lm - rm
# ValueError: cannot add a stacked (batched) expression; fully evaluate it
# before addition
```

Inspecting both operands shows they are structurally identical apart from
their tensor *data*:

```python
lm.tensor.labels == rm.tensor.labels  # True, both 'k*a*n_'
lm.names == rm.names  # True, both {'motor': ('a',)}
lm.masks == rm.masks  # True (same Motor blade mask)
lm.out_mask == rm.out_mask  # True (same Point-product output mask)
lm.tensor.data.shape == rm.tensor.data.shape  # True, both (16, 12, 3)
```

Given this, `lm - rm` should be exactly as valid as merging two non-batched
expressions with the same raw labels — the existing `_reindex_output` +
tensor-subtract logic doesn't care whether the shared axis happens to be a
counting axis or a variable axis; it operates on `.data` directly.

## Why the guard is (probably) there

Nothing in the tensor tracks *provenance* of a counting axis beyond its
label string and length. Two independently-built batches could coincidentally
share a label and length without actually corresponding index-for-index (the
label may be user-supplied *or* auto-generated via `_next_batch_label`), so
the library conservatively refuses to guess and always raises.

## Suggested fix sketch

In `_add()` (and similarly in `_product()`'s guard for `*`), replace the
unconditional raise with a check that also allows the merge when both
operands' *raw* axis-label sequences already match exactly (which, for
`MVLabeledTensor`, already encodes axis identity — including counting axes)
and their output/variable masks match:

```python
def _add(left, right, subtract: bool = False):
    L = _to_expression(left)
    R = _to_expression(right)
    same_axes = _raw_names(L.tensor.labels) == _raw_names(R.tensor.labels)
    if (L._has_counting_axes() or R._has_counting_axes()) and not same_axes:
        raise ValueError(
            "cannot add stacked (batched) expressions with different axis layouts; fully evaluate them before addition"
        )
    if same_axes:
        ...  # existing merge branch, unchanged
    return AffineExpression(...)
```

This keeps the safety net for genuinely mismatched batches (different
labels, different lengths, different variables) while allowing the
already-safe case to succeed instead of raising.

## Workaround (used in wafer-grinding)

A local helper bypasses the guard once the structural-equality preconditions
are verified explicitly, reusing the public `Expression(tensor, names,
masks)` constructor (see
[`src/dev/eval_transform_1.py`](../../src/dev/eval_transform_1.py)):

```python
def merge_stacked(left: Expression, right: Expression, subtract: bool = False) -> Expression:
    """Zip two stacked (batched) single-variable Expressions.

    ``pytanga.expression._expression._add`` unconditionally refuses to
    combine two expressions that carry counting (batch) axes, even when
    they are structurally identical -- see
    dev/todos/pytanga-batched-expression-merge.md. When both operands share
    the same variable/mask and the exact same axis labels (including the
    counting axis), the merge is a plain element-wise add/subtract of their
    tensor data, so we bypass the guard here.
    """
    if left.names != right.names or left.masks != right.masks:
        raise ValueError("merge_stacked() requires matching variable names/masks")
    if left.tensor.labels != right.tensor.labels:
        raise ValueError("merge_stacked() requires identical axis labels (incl. counting axes)")
    if left.out_mask != right.out_mask:
        raise ValueError("merge_stacked() requires identical output blade masks")
    if left.tensor.data.shape != right.tensor.data.shape:
        raise ValueError("merge_stacked() requires identical tensor shapes")

    data = left.tensor.data - right.tensor.data if subtract else left.tensor.data + right.tensor.data
    tensor = MVTensor(data, left.tensor.tensor.masks)
    labeled = MVLabeledTensor(tensor, left.tensor.labels)
    return Expression(labeled, left.names, left.masks)
```

Usage:

```python
lm = (motor * X)(X=("n", local_points))
rm = (Y * motor)(Y=("n", world_points))
eqn = merge_stacked(lm, rm, subtract=True)  # single stacked Expression, ready for .svd()
```
