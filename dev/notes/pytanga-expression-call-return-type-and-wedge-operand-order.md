# Feature requests: `Expression.__call__` return type, and constant-wedge operand order

**Status:** proposed upstream (not a wafer-grinding task) — kept here for reference, with local workarounds.

Two independent, small pytanga API rough edges hit while building
`wafer_grinding.mass_object`/`wafer_grinding.cylinder_mass`'s
`Expression`-based inertia operators. Neither is a runtime bug; both are
typing/ergonomics gaps.

## 1. `Expression.__call__`'s return type can't be narrowed by the caller

`Expression.__call__` always declares its return type as `MV | Expression |
list` (`pytanga/expression/_expression.py`), because a single call site can:

- fully evaluate to a plain `MV`, if every variable/axis ends up bound,
- partially evaluate to another `Expression`, if at least one variable or
  counting axis is still unbound, or
- fan out to a `list`, for certain batch bindings.

Which case applies is *known statically by the caller* (it depends on which
variable names/axes are passed as kwargs), but that knowledge isn't
expressible through the current signature, so a static type checker (`ty`,
also pyright) can never narrow the result — every downstream use of a
result the author knows is still partial (e.g. combining it further with
`|`/`^`/`+`, or annotating a variable as `Expression`) is flagged as
`invalid-assignment`/`invalid-return-type`/`unsupported-operator`.

### Minimal repro

```python
from pytanga.basis import BasisN3
from pytanga.expression import Variable
from pytanga.blade_mask import BladeMask

N3 = BasisN3()
mask = BladeMask(N3, ["e1", "e2", "e3"])
x_b = Variable("x_b", mask)
rot_plane = Variable("rot_plane", BladeMask(N3, ["e12", "e13", "e23"]))

wedge_expr = x_b ^ (rot_plane | x_b)  # Expression, still 2 free variables
partial: Expression = wedge_expr(x_b=some_data_array)  # binds x_b only
# ty: error[invalid-assignment] -- MV | Expression | list is not assignable to Expression
# (even though rot_plane is still free, so this MUST be an Expression)
```

### Suggested fix sketch

Split the single flexible `__call__` into intent-specific methods with
narrower declared return types, keeping `__call__` as today's dynamic
fallback for interactive/exploratory use:

- `.bind(**kwargs) -> Expression` — for callers who know at least one
  variable/axis remains free; raises if the binding would fully collapse.
- `.evaluate(**kwargs) -> MV` — for callers who know every variable is now
  bound to a concrete value; raises if anything is still free.

This mirrors common "safe vs. asserting" API splits (e.g. `dict.get()` vs.
`dict[key]`) and would let call sites express their own invariant statically
instead of needing a runtime-checked narrowing helper at every partial-
evaluation site.

### Workaround (used in wafer-grinding)

`wafer_grinding.mass_object._as_expression`:

```python
def _as_expression(result: MV | Expression | list) -> Expression:
    """Narrow `Expression.__call__`'s `MV | Expression | list` return type
    down to `Expression`, for a binding known (by the caller) to still leave
    at least one variable/counting axis unbound.
    """
    assert isinstance(result, Expression)
    return result
```

Used in `CylinderMass.inertia_operator_expression`'s density/quadrature
branch, where `rot_plane` (`omega_expr`) is deliberately left unbound across
two successive partial calls:

```python
partial = _as_expression(wedge_expr(x_b=DataArray(points, masks=("quad_pt", _POINT_MASK))))
return _as_expression(partial(quad_pt=density_weights))
```

`assert isinstance(...)` is preferred over `typing.cast(Expression, ...)`
here: both satisfy the type checker, but the `assert` is actually checked at
runtime — if the "still partial" invariant ever turns out wrong, this fails
loudly at the point of the mistake instead of silently mis-typing a value
that propagates downstream.

## 2. Wedging a constant `MV` against a `Variable`/`Expression` only works in one operand order

`a ^ b` (and similarly `|`, `*`) is supported when `a` is a `Variable`/
`Expression` and `b` is a constant `MV`, but **not** the reverse: a plain
constant `MV` on the left with a `Variable`/`Expression` on the right raises
(or is simply not implemented) rather than building the expected
`Expression`.

### Minimal repro

```python
from pytanga.basis import BasisN3
from pytanga.expression import Variable
from pytanga.blade_mask import BladeMask

N3 = BasisN3()
x_cm = N3({(1,): 1.0, (2,): 2.0, (3,): 3.0})  # constant MV
omega = Variable("omega", BladeMask(N3, ["e12", "e13", "e23"]))

omega ^ x_cm  # works: Variable/Expression op constant
x_cm ^ omega  # does NOT work the same way: constant op Variable/Expression
```

Since wedging two vectors anticommutes (`a ^ b == -(b ^ a)`), every affected
term can be rewritten with the supported operand order and negated, but this
requires callers to know the anticommutation identity and apply it
manually rather than pytanga handling both operand orders symmetrically.

### Suggested fix sketch

Add the reflected dunders (`__rxor__`, `__ror__`, `__rmul__` etc.) to
`Expression`/`Variable` so a constant `MV` on the left dispatches to the
same product logic as the constant-on-the-right case (negated where the
product anticommutes), instead of requiring callers to manually rewrite the
operand order.

### Workaround (used in wafer-grinding)

`MassObject.spin_bivector_about_expression` builds each wedge term as
`-(omega_expr_term ^ constant)` instead of `constant ^ omega_expr_term`:

```python
x_cm_term = -((omega_expr | x_cm) ^ x_cm)  # == x_cm ^ (omega_expr | x_cm), rewritten to the supported operand order
d_term = -((omega_expr | d) ^ d)
```

See the docstring of `spin_bivector_about_expression` in
[`src/wafer_grinding/mass_object.py`](../../src/wafer_grinding/mass_object.py)
for the in-context explanation.
