# Label Iterator (`iter_labels`)

`iter_labels` is a free function that iterates synchronously over a named
axis across one or more `MVLabeledTensor` instances.  It yields slices with
the iterated axis **removed**, making it the tool for manual, element‑by‑element
computation over a batch dimension when the built‑in contraction or
element‑wise operators are not sufficient.

```python
from pytanga.tensor._labeled import iter_labels
```

## How it works

Given one or more tensors that all contain the same label name (e.g. `"n"`),
`iter_labels` takes slices along that axis for each tensor.  Each yielded
slice is a new `MVLabeledTensor` where:

- The `"n"` axis has been **removed** (collapsed, not kept as size‑1).
- The corresponding blade mask has been dropped.
- The label string has been trimmed (e.g. `"n*a*"` → `"a*"`).

The iteration runs from `0` to `length - 1`, where `length` is the size of
the named axis.  All tensors must have the same length along that axis.

## Single tensor iteration

```python
A = MVLabeledTensor.zeros("n*a*", [5, mask])    # shape (5, 8)

for a_slice in iter_labels("n", A):
    # a_slice.labels == "a*"
    # a_slice.shape == (8,)
    # a_slice is the i-th row of A along the "n" axis
    ...
```

Each slice is the coefficient vector of a single multivector from the batch,
with the batch dimension removed.

## Multi‑tensor iteration

When multiple tensors are passed, the iterator yields **tuples** of slices
— all taken at the same position along the shared label:

```python
A = MVLabeledTensor.zeros("n*a*", [5, mask])
B = MVLabeledTensor.zeros("n*b*", [5, 3])

for a_s, b_s in iter_labels("n", A, B):
    # a_s.labels == "a*", shape (8,)
    # b_s.labels == "b*", shape (3,)
    ...
```

If only one tensor is passed, the iterator yields single `MVLabeledTensor`
instances (not 1‑tuples).

## Contracting per batch element

The most common use case: you have a batch of operands but the contraction
cannot be expressed as a single labeled‑tensor product (e.g. because you need
to compute a nonlinear function, or because the operands are in separate
batches).  `iter_labels` lets you pull out one element at a time from each
batch:

```python
from pytanga.tensor._labeled import iter_labels

batch_size = 10
A_batch = MVLabeledTensor.zeros("n*a*", [batch_size, mask])
B_batch = MVLabeledTensor.zeros("n*b*", [batch_size, mask])
O = product_tensor(mask, mask)["kij"]
result_parts = []

for a_i, b_i in iter_labels("n", A_batch, B_batch):
    # a_i labels "a*", shape (|mask|,)
    # b_i labels "b*", shape (|mask|,)
    c_i = O["kij"] * a_i["i"] * b_i["j"]       # labels "k*", shape (|mask|,)
    result_parts.append(c_i)

# result_parts is a list of MVLabeledTensor, each of shape (|mask|,)
```

This performs `batch_size` independent geometric products, one per pair.
For large batches, the batch GP via element‑wise labels
(`O["kij"] * A["in_"] * B["jn_"]`) is more efficient.  Use `iter_labels`
when the per‑element computation is not expressible as a single einsum.

## Applying a function per pair

`iter_labels` is also the entry point for arbitrary per‑element processing.
For example, computing the squared magnitude of each GP result:

```python
for a_i, b_i in iter_labels("n", A_batch, B_batch):
    c_i = O["kij"] * a_i["i"] * b_i["j"]
    mag2 = c_i.tensor.data @ c_i.tensor.data     # dot product
    print(f"element {mag2}")
```

Or applying a custom GA operation that is not a single product:

```python
for a_i, b_i in iter_labels("n", A_batch, B_batch):
    # Outer product of each pair
    outer = a_i["i"] * b_i["j"]          # labels "i*j*"
    # Then contract with something else
    projected = O["kij"] * outer["ij"]
    ...
```

## Accumulating results into a tensor

To accumulate per‑element results back into a labeled tensor, use
`__setitem__` assignment:

```python
C_batch = MVLabeledTensor.zeros("n*k*", [batch_size, mask])

for idx, (a_i, b_i) in enumerate(iter_labels("n", A_batch, B_batch)):
    c_i = O["kij"] * a_i["i"] * b_i["j"]
    # Insert back at position idx
    C_batch.tensor.data[idx, :] = c_i.tensor.data
```

This builds the output batch incrementally.  Equivalent to the batched
contraction but useful when the result cannot be computed in a single pass.

## When to use `iter_labels` vs. batch contraction

| Situation | Use |
|-----------|-----|
| Same GP/IP/OP applied to all batch pairs | Element‑wise batch contraction (`O["kij"] * A["in_"] * B["jn_"]`) |
| Different operation per element | `iter_labels` with per‑element logic |
| Nonlinear post‑processing per element | `iter_labels` |
| Accumulating into a custom structure | `iter_labels` |