# Using Variables and Expressions

## Building expressions

Combine a `Variable` with constants or other variables using the geometric
(`*`), inner (`|`), and outer (`^`) products.  Constant operands are folded into
the expression tensor at build time.

```python
v = Variable("V1", BladeMask.full(alg))
w = Variable("V2", BladeMask.full(alg))

e1 = v * a          # GP
e2 = v | a          # IP
e3 = v ^ a          # OP
e4 = v * w          # two-variable product
e5 = 2.0 * v * a    # scalar scale
e6 = v * v          # repeated variable (polynomial form)
```

### Constant expressions

An `Expression` can also be built directly from a multivector, producing a
zero-variable constant expression:

```python
E = Expression(A)              # out mask = non-zero blades of A
E = Expression(A, mask)        # out mask = mask (BladeMask); A's other blades dropped
E()                            # -> A (or A restricted to mask)
```

## Evaluating

Call the expression with some or all variables bound by name.  A value is either
a single `MV` (whose non-zero blades lie within the variable's mask) or a
`DataArray` whose blade axis matches the variable's mask.

```python
result = e(V1=x)                                       # all bound -> MV
batch = e(V1=DataArray([x0, x1], masks=("n", full)))   # list[MV]
```

A `DataArray` pairs a NumPy array (or a list of MVs) with per-axis specs: one
`BladeMask` per blade axis, and a `str` name per counting axis.

```python
import numpy as np
from pytanga import DataArray

points = DataArray(np.random.rand(100, 3), masks=("pnt_idx", point_mask))
```

A counting axis introduced by a binding is reduced with the same `__call__`
syntax: a raw 1-D array sums it away, while a `DataArray` can sum or
multiply-and-keep.

```python
contract = expr(x_pnt=points)
contract(pnt_idx=scalars)                               # sum
contract(pnt_idx=DataArray(scalars, masks=("_",)))      # multiply, keep
```

For a multi-axis reduction, `"_"`/`"*"` mark the key axis (multiply vs sum) and
the other axes are kept as new named dimensions:

```python
contract(pnt_idx=DataArray(scalars2d, masks=("pnt_idx", "group_idx")))
```

Rename counting axes with `data.rename_axis("n", "pnt_idx")` (returns a new
`DataArray`) or `data(n="pnt_idx")` (in place, returns `data`).

### Partial evaluation (Jacobians)

Binding only some variables returns a new `Expression` over the remaining
variables (which may carry counting axes):

```python
e = v * w
jac = e(V1=x)     # Jacobian of e w.r.t. w, holding v = x
jac(V2=z)         # == x * z
jac.tensor        # (output × w) matrix
```

Stacked (batched) partial results can be evaluated and inspected via `.tensor`.
Two stacked expressions with the same axis layout merge under `+`/`-`, and a
single stacked expression composes with a constant or variable under `*`.
Composing two stacked expressions, or calling `inv` on a stacked expression,
still requires full evaluation.

## Addition, subtraction, and affine sums

`+`/`-` merge two expressions that share the same variables **in the same
order** into a single tensor (unifying their output blade masks):

```python
e = v * a + v * b   # == v * (a + b)
```

The same merge applies to stacked expressions that share the exact same axis
layout (including their counting axes): binding `X` and `Y` to `DataArray`s with
the same counting-axis name makes `(motor * X) - (Y * motor)` a single stacked
`Expression` over `motor`.

When the operands cannot be merged (different variable sets, different
occurrence degrees, or a constant), the result is an `AffineExpression` — a
list of `Expression` terms that is evaluated by summing the per-term results:

```python
f = (v * v) + v + c   # AffineExpression of 3 terms
f(V1=x)               # == x*x + x + c
```

Products distribute over the terms (`f * g`, `~f`, `2 * f`, `-f` all work).
`lstsq`, `svd`, and `inv` also apply to an `AffineExpression` whenever its sum
reduces to a single linear map in one remaining variable (see below).

## Repeated variables (polynomial forms)

A variable may appear more than once in a product, up to `MAX_DEGREE` (4)
occurrences per term:

```python
sq  = v * v       # x*x
cub = v * v * v   # x*x*x
```

Repeated occurrences use consecutive labels from the variable's fixed block, so
identically-shaped terms merge under `+`/`-` (`v*v + v*v == 2·(v*v)`,
`v*v - v*v == 0`).

## Involutions

Reverse (`~`) and the Clifford conjugate (`.conj()`) are available as diagonal
sign tensors:

```python
~e          # reverse of the expression
e.conj()    # Clifford conjugate
~v          # reverse of a variable (composes in products)
```

## Named product functions

The usual GA products are available as named methods and module-level
functions: `gp`, `ip`, `op`, `vp`, `nvp`, `sp`, `cp`, `acp`, and `rc`.  Every
one accepts a constant multivector, a `Variable`, or an expression as *either*
operand (mixed and reflected forms included):

```python
from pytanga.expression import vp, sp, cp, rc

E_rot = R.vp(X)     # R * X * ~R        (versor product)
E_ip  = v.ip(a)     # v | a             (inner product)
E_op  = v.op(a)     # v ^ a             (outer product)
E_cp  = v.cp(a)     # (v*a - a*v) / 2   (commutator)
E_acp = v.acp(a)    # (v*a + a*v) / 2   (anti-commutator)
E_rc  = v.rc(a)     # v ⌊ a             (right contraction)
E_gp  = v.gp(a)     # v * a             (geometric product)

E_rot2 = vp(R, X)   # module-level function form
```

`vp` composes `*` with `~` (reverse), so a variable versor appears twice in the
sandwich and is subject to the `MAX_DEGREE` limit.  `nvp` uses the true
inverse instead of the reverse and therefore requires a *constant* versor (a
symbolic versor's inverse is not representable); `nvp(variable, X)` raises
`ValueError`.

`sp` is scalar-valued: with two concrete multivectors it returns a Python
`float`/`int` directly, and with symbolic operands it returns a
`ScalarExpression` whose fully-bound value is a `float`/`int` (matching the
multivector dtype):

```python
sp(a, b)          # float/int
s = v.sp(a)       # ScalarExpression
s(V1=x)           # float/int (scalar part of x * a)
```

## Renaming and unifying variables

Variables are keyed internally by a label block, not by name, so two
`Variable("X", mask)` instances created independently are distinct and their
expressions do not merge under `+`/`-`.  Re-key them onto one canonical variable
with `bind(...)` (passing a `Variable` as the value), rename them in place with
`rename_var`, or re-key a whole list in one call with `unify`:

```python
X = Variable("X", mask)          # one canonical variable

e1 = Variable("X", mask) * a     # created elsewhere, distinct block
e2 = Variable("Y", mask) * b     # same mask, different name

e1 = e1.bind(X=X)                # replace "X" with the canonical X
e2 = e2.bind(Y=X)                # replace "Y" with the canonical X (rename)

E = e1 + e2                      # now a single merged expression in X

[e1, e2] = unify([e1, e2], X=X, Y=X)   # same, for a whole list at once

e1.rename_var("X", "P")          # name-only rename (keeps the label block)
```

`bind` with a `Variable` value substitutes that variable (a `MV`/`DataArray`
value still binds to data, unchanged).  `unify` is lenient — names absent from a
given expression are skipped — and returns a list of re-keyed expressions that
you combine with `+`.  The target variable's blade mask must equal the source's
mask, otherwise `ValueError` is raised.

## Projecting onto a subspace

Restrict an expression (or an affine sum of expressions) to a blade subspace
with `project_onto`, mirroring `MV.project_onto`:

```python
from pytanga import BladeMask

euclid = BladeMask(alg, [alg.E1, alg.E2, alg.E3, alg.E12, alg.E13, alg.E23])

p = expr.project_onto(euclid)        # Expression — output restricted to euclid
p = aff.project_onto(euclid)         # AffineExpression — terms dropped if empty
p = expr.project_onto(some_mv)       # keep output blades non-zero in some_mv
```

`other` is either a `BladeMask` (exact blade-id membership) or an `MV` (its
non-zero blades).  The result's output mask is the intersection; a disjoint
projection collapses to a zero constant expression.  A module-level
`project_onto(x, other)` dispatches over `MV` / `Expression` /
`AffineExpression`.

## Inverse

For a single-variable, single-occurrence expression whose tensor is a square,
invertible matrix, `inv(name)` returns the inverse linear map as a new
expression keyed by *name*:

```python
e_inv = e.inv("V2")     # solve y = e(x) back to x
x = e_inv(V2=y)
```

Multi-variable, repeated-variable, non-square, or singular expressions raise
`ValueError`.

An `AffineExpression` supports the same `inv(name)` when its sum reduces to a
single linear map: exactly one variable, appearing once per term, non-stacked
and square.

## Least squares (`lstsq`)

For a single-variable expression whose tensor is a linear map in that
variable, `lstsq()` solves it in the least-squares sense (the single variable
is inferred, so no name is needed):

```python
x = e.lstsq()              # homogeneous: smallest singular vector
x = e.lstsq(rhs=y)         # M · vec(x) = y via np.linalg.lstsq
```

When no `rhs` is given, the homogeneous system `M · vec(x) = 0` is solved and
the smallest-singular-vector solution is returned (the right singular vector of
the least singular value) — the standard approach for fitting entities from an
incidence constraint such as `P ^ L = 0`.  With an explicit `rhs` (an `MV`
over the output mask), `numpy.linalg.lstsq` is used, requiring a non-stacked
expression.  See `py/examples/ga/expression/line_fitting_p3.py`.

An `AffineExpression` that reduces to a single linear map (one variable, once
per term) supports `lstsq()` the same way.

## Singular-value decomposition (`svd`)

`svd()` returns `(values, mvs)` — the descending list of singular values of
the expression's linear map plus the corresponding right-singular vectors as
`MV`s over the variable's blade mask:

```python
values, mvs = e.svd()
smallest = mvs[-1]   # == e.lstsq()
```

It applies to a single-variable expression (with stacked/batch axes allowed),
and raises `ValueError` for no-variable, multi-variable, or repeated-variable
expressions.  An `AffineExpression` that reduces to a single linear map (one
variable, once per term) supports `svd()` the same way.

## The internal tensor

`Expression.tensor` exposes the reduced `MVLabeledTensor` (one output axis, one
axis per variable occurrence, plus optional `None` counting axes), for
inspection or custom contraction.

## Limits

- A variable may appear at most `MAX_DEGREE` (4) times per product term;
  exceeding this raises `ValueError`.
- Variable axis labels are **integers** from a monotonic, effectively unbounded
  pool, so there is no practical limit on the number of live variables (the old
  12-variable single-letter ceiling is gone).
- A single stacked expression may be composed with a constant or variable under
  `*`, and matching stacked expressions merge under `+`/`-`; two stacked
  operands still cannot be composed with each other.
