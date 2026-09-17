# Changes since version 2.6.0

## New Features
- **Bind a variable to a sub-expression (composition)** — `Expression.bind`
  and `Expression.__call__` now accept an `Expression` as a binding value:
  the bound variable is replaced by the sub-expression's tensor (its output
  mask must equal the variable's mask and it must not carry counting axes),
  and the sub-expression's free variables become the result's new axes.
  Repeated occurrences substitute consistently — the sub-expression's free
  variables stay one shared block, so binding them later feeds the same value
  to every occurrence.  `AffineExpression.bind`/`__call__` inherit the same
  behaviour through their per-term evaluation.
