# Properties & Operations

Once constructed, a `BladeMask` provides fast lookup, iteration, and set
operations.  All operations assert that both masks belong to the same
algebra.

## Core properties

| Property | Type | Description |
|----------|------|-------------|
| `ids` | `list[int]` | Sorted blade IDs |
| `algebra` | `Algebra` | The owning algebra |
| `grades` | `list[int]` | The distinct grades present in the mask |

```python
mask = BladeMask(alg, grades=[0, 2])     # scalar + bivectors
print(mask.ids)                           # [0, 3, 5, 6]
print(mask.grades)                        # [0, 2]
print(mask.algebra.name)                  # "E3"
```

## Blade names

```python
names = mask.names()                      # e.g. ["s", "e12", "e13", "e23"]
```

Returns blade names sorted by grade (scalars first, then vectors, bivectors,
etc.).  Within each grade, names follow the lexical order of the basis
indices.

## Size

`len(mask)` returns the number of blade IDs — this is the dimension of any
vector or matrix axis labelled by this mask.

```python
full = BladeMask.full(alg)               # E3: 8 blades
vectors = BladeMask(alg, grades=[1])     # 3 blades
print(len(full))                          # 8
print(len(vectors))                       # 3
```

## Membership and indexing

O(1) lookup for both checking presence and finding the position of a blade:

```python
mask = BladeMask(alg, [0, 1, 2, 3, 5])

# Membership test
assert 0 in mask                         # True — scalar is included
assert 4 not in mask                     # False — e3 not present

# Position lookup
pos = mask.index(1)                      # 1 (e1 is at position 1)
pos = mask.index(5)                      # 4 (e13 is at position 4)

# Missing blade raises KeyError
mask.index(99)                           # KeyError
```

`index()` returns the 0‑based position of the blade in the mask's sorted
`ids` list.  This is the row/column position in matrices labelled by this
mask.

## Set operations

### Union

```python
mask_a = BladeMask(alg, [0, 1, 2])       # s, e1, e2
mask_b = BladeMask(alg, [2, 3])          # e2, e12
combined = mask_a.union(mask_b)          # ids: [0, 1, 2, 3]
```

### Intersection

```python
common = mask_a.intersection(mask_b)     # ids: [2]  (only e2)
```

Both return a new `BladeMask` with sorted, deduplicated IDs.  Both assert
that the masks share the same algebra.

## Copying

`BladeMask` instances are immutable in practice (the `ids` tuple is never
mutated after construction).  To create a copy with modifications, construct
a new mask from the existing `ids`:

```python
new_mask = BladeMask(mask.algebra, mask.ids)
```

## Examples

```python
from pytanga import Algebra, BladeMask
from pytanga.basis import BasisE3

alg = BasisE3()
full = BladeMask.full(alg)

# Check if a blade is in the mask
if 3 in full:
    print(f"e12 is at position {full.index(3)}")

# Find all grades present
print(full.grades)                        # [0, 1, 2, 3]

# Work with subspaces
scalars = BladeMask(alg, grades=[0])
vectors = BladeMask(alg, grades=[1])
both = scalars.union(vectors)            # scalars + vectors