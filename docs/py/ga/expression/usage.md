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

## Evaluating

Call the expression with some or all variables bound by name.  Values must be
`MV`s whose non-zero blades lie within the variable's mask.

```python
result = e(V1=x)           # all bound -> MV
results = e(V1=[x0, x1])   # batch -> list[MV] (one einsum)
```

Binding several variables to lists returns a nested `list` (cross product).
A batch may carry an explicit counting-axis label via a `(label, list)` tuple:

```python
e(V1=("n", [x0, x1]), V2=y)
```

### Partial evaluation (Jacobians)

Binding only some variables returns a new `Expression` over the remaining
variables (which may carry counting axes):

```python
e = v * w
jac = e(V1=x)     # Jacobian of e w.r.t. w, holding v = x
jac(V2=z)         # == x * z
jac.tensor        # (output × w) matrix
```

Stacked (batched) partial results can be evaluated and inspected via `.tensor`,
but cannot be further composed with `*`/`+`/`inv` until fully evaluated.

## Addition, subtraction, and affine sums

`+`/`-` merge two expressions that share the same variables **in the same
order** into a single tensor (unifying their output blade masks):

```python
e = v * a + v * b   # == v * (a + b)
```

When the operands cannot be merged (different variable sets, different
occurrence degrees, or a constant), the result is an `AffineExpression` — a
list of `Expression` terms that is evaluated by summing the per-term results:

```python
f = (v * v) + v + c   # AffineExpression of 3 terms
f(V1=x)               # == x*x + x + c
```

Products distribute over the terms (`f * g`, `~f`, `2 * f`, `-f` all work), but
`inv` requires a single linear term.

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
expressions.

## The internal tensor

`Expression.tensor` exposes the reduced `MVLabeledTensor` (one output axis, one
axis per variable occurrence, plus optional `None` counting axes), for
inspection or custom contraction.

## Limits

- A variable may appear at most `MAX_DEGREE` (4) times per product term;
  exceeding this raises `ValueError`.
- Each variable owns a contiguous block of `MAX_DEGREE` **single-letter axis
  labels**, so the 50-letter alphabet supports `floor(50 / MAX_DEGREE)` = 12
  live variables per process.
- Stacked (batched) partial expressions are read-only: they support evaluation
  and `.tensor` inspection, but not further `*`/`+`/`inv` composition.
