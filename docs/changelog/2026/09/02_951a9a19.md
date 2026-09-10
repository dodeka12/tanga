# Changes since version 1.16.0

## New Features
- **Stacked expression merge under `+`/`-`** — two batched (stacked)
  expressions with the same axis layout now merge into a single stacked
  `Expression` instead of raising, enabling per-correspondence constraints such
  as `(motor * X)(X=batch) - (Y * motor)(Y=batch)`.
- **Single stacked operand under `*`** — a stacked expression can now be
  composed with a constant multivector or a `Variable`; its counting axes pass
  through element-wise. Composing two stacked expressions is still rejected.
- **Integer axis labels** — `MVLabeledTensor` accepts integer axis names
  alongside single-letter strings via a new public frozen dataclass
  `AxisLabel(name, mode)` (exported from `pytanga.tensor`), and contraction now
  uses einsum's list form, removing the 52-letter ceiling.
- **Integer variable-label pool** — `Variable` labels are integers from a
  monotonic, effectively unbounded pool, so there is no practical limit on the
  number of live variables.
- **`project_onto`** — new `MV.project_onto` / `Algebra.project_onto` keeps the
  receiver's components for the blades of `b` (`MV`) or the blade ids of `b`
  (`BladeMask`, exact membership).
- **Constant expressions** — `Expression(A)` and `Expression(A, BladeMask)`
  build a zero-variable constant expression; calling it returns `A` (restricted
  to the mask).

## Breaking Changes
- **`MVLabeledTensor.labels` is no longer a string** — it is stored as a
  `tuple[AxisLabel, ...]`; string *input* remains supported but code that reads
  `.labels` as a string must use `_labels_str(...)`/`_axis_names(...)` instead.
- **`Variable.label` is an integer** — `Variable.label` and `Variable.labels`
  now return integers rather than single letters; `Variable.name` is unchanged.
- **`project_to` removed** — the confusing `MV.project_to` / `Algebra.project_to`
  (which projected in the wrong direction for the `MV` case) is removed; use
  `project_onto` instead.
