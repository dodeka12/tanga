# BladeMask Construction

`BladeMask` supports many construction patterns that make it easy to specify
which blades of an algebra are relevant to a computation.

```python
from pytanga import Algebra, BladeMask
from pytanga.basis import BasisE3

alg = BasisE3()
```

## From explicit blade IDs

The simplest form: pass a list of integer blade IDs.

```python
BladeMask(alg, [0, 1, 2, 4])             # s, e1, e2, e12
```

Blade IDs follow the standard binary encoding.  In E3:
- 0 = scalar (s)
- 1 = e1, 2 = e2, 3 = e12
- 4 = e3, 5 = e13, 6 = e23
- 7 = I (pseudoscalar)

## From string expressions

Pass a multivector string expression — signs and coefficients are discarded,
only the blade names matter:

```python
BladeMask(alg, "1 + e12 + e23")          # ids: {0, 3, 6}
BladeMask(alg, "e1")                     # ids: {1}
```

A list of strings unions multiple expressions:

```python
BladeMask(alg, ["e12", "1 + e13"])       # ids: {0, 3, 5}
```

The convenience alias `BladeMask.from_str(alg, s)` does the same thing.

## By grade

Select all blades of specific grades:

```python
BladeMask(alg, grades=[0])               # scalar only
BladeMask(alg, grades=[1])               # all vectors (e1, e2, e3)
BladeMask(alg, grades=[2])               # all bivectors (e12, e13, e23)
BladeMask(alg, grades=[0, 2])            # even sub‑algebra
```

## Combined

String expressions and grade filters can be combined — the result is the
union:

```python
BladeMask(alg, "e1", grades=[2])         # e1 plus all bivectors
```

## All blades

```python
BladeMask.full(alg)                      # all 2^dim blades
```

For E3 this produces 8 blades, for Conformal GA (5D) it produces 32.

## From an existing multivector

Extract the non‑zero blades of an `MV`:

```python
a_mask = BladeMask.from_mv(alg, mv)
```

This is how the solvers determine which blades the known operand A occupies.
Only blades with non‑zero coefficients are included.

To include structural zeros (blades present in the MV with coeff = 0), use
`solver.blade_mask(mv, only_nonzero=False)` instead.

## From multiple multivectors

Union the non‑zero blades across a list of MVs:

```python
combined = BladeMask.from_array(alg, [mv1, mv2, mv3])
```

This is used by `product_matrix_array` when no explicit `a_mask` is provided.
It computes the union of all blades occupied by any MV in the list, ensuring
the product matrix covers all basis elements.

## Constructor parameters

```python
BladeMask(
    algebra: Algebra,
    *str_args: str,           # optional string expression(s)
    grades: list[int] | None, # optional grade filter
)
```

The `ids` list is:
1. Parsed from `str_args` (union of all blade names found).
2. Unioned with all blades matching the `grades` filter.
3. Sorted and deduplicated.

At least one of `str_args` or `grades` must be provided (or an empty list
of explicit IDs can be passed directly to the internal constructor).