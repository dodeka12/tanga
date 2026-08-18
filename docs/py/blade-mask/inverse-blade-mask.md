# Inverse Blade Mask — Derivation and Algorithm

## Motivation

Given the equation $A \circ X = C$ in a geometric algebra (where $\circ$ is the
geometric, inner, or outer product), and knowing the blade masks of $A$ and $C$,
what is the _maximal_ set of basis blades that $X$ can contain?

If the mask of $X$ is unknown, the solver would otherwise need to search the
full algebra ($2^D$ blades).  The inverse blade mask computes a tight upper
bound on $\operatorname{supp}(X)$ directly from $\operatorname{supp}(A)$ and
$\operatorname{supp}(C)$ in $O(|A| \cdot |C|)$ time using bitmask algebra on
blade IDs.

---

## 1. Bitmap Representation of Basis Blades

In a $D$-dimensional geometric algebra, each basis blade $E_i$ is indexed by an
integer $i \in [0, 2^D-1]$ whose binary representation encodes which basis
vectors comprise the blade:

$$
i = \sum_{v=0}^{D-1} b_v \cdot 2^v, \qquad
b_v = \begin{cases}
1 & \text{if } e_{v+1} \in E_i \\
0 & \text{otherwise}
\end{cases}
$$

For example, in $D=3$: $E_0 = 1$ (scalar), $E_1 = e_1$, $E_2 = e_2$,
$E_3 = e_{12}$, $E_4 = e_3$, $E_5 = e_{13}$, $E_6 = e_{23}$, $E_7 = e_{123}$.

Bitwise operations on blade IDs correspond to set operations on basis vectors:

| Operation       | Meaning                          |
|-----------------|----------------------------------|
| $i \;|\; j$    | Union of basis vectors           |
| $i \;\&\; j$   | Intersection of basis vectors    |
| $i \;\hat{}\; j$ | Symmetric difference (XOR)     |
| $i \subseteq j$ | $(i \;\&\; j) = i$              |
| $i \cap j = \varnothing$ | $(i \;\&\; j) = 0$      |

---

## 2. Product-by-Product Derivation

### 2.1 Geometric Product

The geometric product of two basis blades is always another basis blade
(up to sign):

$$
E_i \, E_k = \pm E_j
$$

In Euclidean signature (sig=0), every basis blade is its own inverse up to
sign: $E_i^{-1} = \operatorname{rev}(E_i) = \pm E_i$.  Left-multiplying by
$E_i^{-1}$ gives:

$$
E_k = \pm E_i^{-1} \, E_j = \pm E_i \, E_j
$$

The resulting blade id is $k = i \oplus j$ (bitwise XOR), and **every** $(i, j)$
pair is valid—no subset or disjointness preconditions apply.

Thus the inverse mask of $X$ for $A \, X = C$ is simply:

$$
\operatorname{mask}(X) = \{\, i \oplus j \mid i \in \operatorname{mask}(A),\; j \in \operatorname{mask}(C) \,\}
$$

This is exactly the _forward_ product blade mask of $A$ and $C$ under GP, so
`inverse_blade_mask` delegates to `product_blade_mask(a_mask, c_mask, product=GP)`.

**Complexity:** $O(|A| \cdot |C|)$ — two nested loops over the blade ID sets.

### 2.2 Outer Product

The outer product of two basis blades is:

$$
E_i \wedge E_k = \begin{cases}
\pm E_{i \,|\, k} & \text{if } i \cap k = \varnothing \\
0 & \text{otherwise}
\end{cases}
$$

The result is non-zero exactly when the two blades share no basis vectors.
Let $j = i \,|\, k$ (bitwise OR).  From $i \cap k = \varnothing$ we have
$k = j \setminus i = j \oplus i$ (XOR, which equals OR when operands are
disjoint).

To solve for the possible $k$ values given $i \in \operatorname{mask}(A)$ and
$j \in \operatorname{mask}(C)$, we require that $i$ is a subset of $j$
(if $E_i \wedge E_k = E_j$, then every basis vector of $E_i$ must appear in
$E_j$).  With this precondition, the solution is straightforward:

$$
k = j \oplus i \quad \text{when} \quad i \subseteq j \;( (i \;\&\; j) = i )
$$

Note the bitwise condition is $(i \;\&\; j) == i$, not $(i \;\&\; k) == 0$.
The latter is the forward-product condition; the inverse condition checks
whether the _given_ $i$ and $j$ are compatible before computing $k$.

Thus:

$$
\operatorname{mask}(X) = \{\, j \oplus i \mid i \in \operatorname{mask}(A),\; j \in \operatorname{mask}(C),\; (i \;\&\; j) = i \,\}
$$

**Complexity:** $O(|A| \cdot |C|)$.

### 2.3 Inner Product (Symmetric)

The symmetric inner product $A \mathbin{|} X$ at the blade level is non-zero
exactly when one blade is contained in the other:

$$
E_i \mathbin{|} E_k = \begin{cases}
\pm E_{k \setminus i} & \text{if } i \subseteq k \\
\pm E_{i \setminus k} & \text{if } k \subseteq i \\
0 & \text{otherwise}
\end{cases}
$$

The result is the symmetric difference of the two blade sets — the contained
blade's vectors are removed from the containing blade.  There are therefore
two inverse cases when solving $E_i \mathbin{|} E_k = E_j$:

**Case 1 — $i \subseteq k$** (the result is $j = k \setminus i$).  Here $i$
and $j$ must be disjoint, since a vector cannot be both "removed" and "present
in the result":

$$
k = i \;|\; j \quad \text{when} \quad i \cap j = \varnothing \; ((i \;\&\; j) = 0)
$$

**Case 2 — $k \subseteq i$** (the result is $j = i \setminus k$).  Here $j$
must be a subset of $i$:

$$
k = i \oplus j \quad \text{when} \quad j \subseteq i \; ((i \;\&\; j) = j)
$$

(When $j \subseteq i$, XOR equals set-difference, so $i \oplus j = i \setminus j$.)

Combining both cases:

$$
\operatorname{mask}(X) = \{\, i \;|\; j \mid (i \;\&\; j) = 0 \,\}
                          \;\cup\;
                          \{\, i \oplus j \mid (i \;\&\; j) = j \,\}
$$

with $i \in \operatorname{mask}(A)$ and $j \in \operatorname{mask}(C)$.  Because
the symmetric inner product has the same support in either operand order, this
mask is identical for $A \mathbin{|} X$ and $X \mathbin{|} A$.

**Complexity:** $O(|A| \cdot |C|)$.

---

## 3. Summary of Formulas

| Product | Condition for valid $(i,j)$ | $k$ (blade ID of $X$) | Operation    |
|---------|----------------------------|------------------------|-------------|
| GP      | *none*                     | $i \oplus j$           | XOR         |
| OP      | $i \subseteq j$            | $j \oplus i$           | XOR (subset)|
| IP      | $i \cap j = \varnothing$ or $j \subseteq i$ | $i \;\| j$ or $i \oplus j$ | OR / XOR    |

All three are computed in $O(|A| \cdot |C|)$ by iterating over pairs $(i, j)$
with simple integer bitwise operations—no C++ bindings or $O(2^D)$ exhaustive
searches are needed.

---

## 4. Integration into the Solver

When `b_mask` is not provided by the user, the solver:

1. Extracts `a_mask` from the non-zero blades of $A$
2. Extracts `c_mask` from the non-zero blades of $C$
3. Computes `b_mask = inverse_blade_mask(a_mask, c_mask, product=...)`
4. Sets `c_mask = b_mask` (so the product-matrix system is square)
5. Builds the product matrix with the restricted `b_mask`

For the least-squares solver (`solve_lsq`), the same pipeline applies—the
inverse blade mask restricts the search space, and stacking $N$ equations
produces a tall matrix that `numpy.linalg.lstsq` solves for the single $X$.

### Example

Consider $D=5$ ($32$ blades).  If $A$ has $a$-mask $= \{e_1, e_{23}\}$
(IDs $[1, 6]$) and $C$ has $c$-mask $= \{e_{12}, e_{13}, e_{123}\}$
(IDs $[3, 5, 7]$):

- **GP**: $k = \{1 \oplus 3, 1 \oplus 5, 1 \oplus 7, 6 \oplus 3, 6 \oplus 5, 6 \oplus 7\} = \{2, 4, 6, 5, 3, 1\} = [1,2,3,4,5,6]$
- **OP**: Check $i \subseteq j$ — from $i=1$ only $j=3,5,7$ pass; from $i=6$ only $j=7$ passes.  $k = \{3 \oplus 1, 5 \oplus 1, 7 \oplus 1, 7 \oplus 6\} = \{2, 4, 6, 1\} = [1,2,4,6]$
- **IP**: No compatible $(i, j)$ pair: for $i \subseteq k$ we need $i \cap j = \varnothing$, and for $k \subseteq i$ we need $j \subseteq i$.  Neither holds for any $i \in \{1, 6\}$, $j \in \{3, 5, 7\}$, so $\operatorname{mask}(X) = \varnothing$.

For sparse MVs the reduction is dramatic compared to searching all 32 blades.

---

## 5. Python Implementation

The inverse blade mask is computed by `inverse_blade_mask` in
`py/pytanga/blade_mask/predict.py`:

```python
from pytanga.blade_mask.predict import inverse_blade_mask

def inverse_blade_mask(a_mask, c_mask, *, product=GP, left=True):
    a_ids = a_mask.ids
    c_ids = c_mask.ids
    if not left:
        a_ids, c_ids = c_ids, a_ids

    if product == EProduct.GP:
        ids = sorted({i ^ j for i in a_ids for j in c_ids})
    elif product == EProduct.OP:
        ids = sorted(
            {j ^ i for i in a_mask.ids for j in c_mask.ids if (i & j) == i}
        )
    elif product == EProduct.IP:
        ids = sorted(
            {i | j for i in a_mask.ids for j in c_mask.ids if (i & j) == 0}
            | {i ^ j for i in a_mask.ids for j in c_mask.ids if (i & j) == j}
        )
    else:
        raise ValueError(f"Unknown product {product!r}")

    return BladeMask(a_mask.algebra, ids)
```

No C++ bindings are required—the bitmask algebra is purely integer arithmetic
available in both Python and C++.

## 6. Related

- [Solver documentation](../solver/index.md) — Python API for equation solving
- [Matrix Mapping and Equations](../../cpp/matrix-mapping-and-equations.md) — C++
  blade-mask machinery (forward product masks)
- [Product matrices](../../cpp/product-matrices.md) — product matrix construction