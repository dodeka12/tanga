# Phase 2 — `ECompose` enum + `SdfElement` operators + `Combine`

## Goal

Introduce the composition vocabulary: an `ECompose` string enum, a common
`SdfElement` base carrying the combine mode + Python operator overloading, and a
`Combine(op, a, b)` binary CSG node. This makes CSG expressible with arithmetic
operators and fixes the combine-mode strings in one place.

## Files

- New: `py/pytanga/viz/sdf/_compose.py` — `ECompose`, `SdfElement`, `Combine`,
  `_coerce()`.
- Modify: `py/pytanga/viz/sdf/__init__.py` — export `ECompose`, `Combine`,
  `SdfElement`.
- New: `py/tests/viz/sdf/test_ecompose_operators.py`.

## Steps

- [x] **2.1 — `ECompose(StrEnum)`** (`_compose.py`)
  - `UNION = "union"`, `INTERSECTION = "intersection"`, `SUBTRACT = "subtract"`,
    `XOR = "xor"`. String-compatible (`ECompose.SUBTRACT == "subtract"`).
  - A `_coerce_mode(value)` helper accepting `ECompose` or a legacy string
    (`"union"`/`"intersection"`/`"subtract"`), raising on `"xor"` in fold
    contexts (XOR is binary-only).

- [x] **2.2 — `SdfElement` base** (`_compose.py`)
  - `@dataclass(frozen=True)` with `combine: ECompose = ECompose.UNION`.
  - Unary operators: `__neg__` → `dataclasses.replace(self,
    combine=ECompose.SUBTRACT)`; `__invert__` → `... combine=ECompose.INTERSECTION`.
  - Binary operators (each returns `Combine(op, self, _coerce(other))`):
    `__add__`/`__or__` → `UNION`, `__sub__` → `SUBTRACT`, `__and__` →
    `INTERSECTION`, `__xor__` → `XOR`.
  - Reflected operators (`__radd__`, `__rsub__`, `__rand__`, `__ror__`,
    `__rxor__`) so `entity + sdf_element` also works once `_coerce` understands
    raw entities.

- [x] **2.3 — `Combine`** (`_compose.py`)
  - `@dataclass(frozen=True) class Combine(SdfElement): op: ECompose; a:
    SdfElement; b: SdfElement`.
  - `to_sdf_node()` lowers to a `combine(op, a.to_sdf_node(), b.to_sdf_node())`
    `SdfNode` (delegating to `primitives.combine`); XOR lowers to a dedicated
    `xor` combinator node (Phase 5 adds the GLSL `opXor`).

- [x] **2.4 — `_coerce()`** (`_compose.py`)
  - `SdfElement` → pass through; `None` → error. (Raw-entity wrapping is added in
    Phase 3 once `SdfObject` exists.)

- [x] **2.5 — Tests** (`test_ecompose_operators.py`)
  - `ECompose.SUBTRACT == "subtract"`; `_coerce_mode("subtract")` round-trips.
  - `-el.combine == SUBTRACT`, `~el.combine == INTERSECTION`.
  - `el1 + el2` / `el1 - el2` / `el1 & el2` / `el1 | el2` / `el1 ^ el2` produce
    `Combine` with the right `op` and operand order.
  - `Combine(UNION, a, b).to_sdf_node()` shape.

- [x] **2.6 — Validate**
  - `uv run pytest py/tests/viz/sdf/test_ecompose_operators.py -q` +
    `uv run pytest py/tests/viz/ -q`.

## Validation

`uv run pytest py/tests/viz/ -q` +
`uv run pytest py/tests/viz/sdf/test_ecompose_operators.py -q`.

## Notes

- Operators are defined once on `SdfElement`, so `SdfObject`/`Composed`/`SdfGroup`
  inherit them uniformly in later phases.
- Python precedence (`+`/`-` bind tighter than `&`, then `^`, then `|`) means
  mixed expressions may need parentheses — document this in the example/docs.
