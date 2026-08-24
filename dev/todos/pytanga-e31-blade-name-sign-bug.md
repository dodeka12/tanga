# Bug report: reversed-order blade names lose sign in string parsing / bracket indexing

**Status:** reported upstream (not a wafer-grinding task) — kept here for reference.

## Summary

`blade_id()` in `pytanga/algebra/_blade_names.py` converts a blade name to a
bitmask by OR-ing the bit for each index, ignoring the order the indices were
given in:

```python
def blade_id(name: str, dim: int) -> int:
    ...
    indices = [int(c) for c in tail]
    ...
    result = 0
    for i in indices:
        result |= 1 << (i - 1)
    return result
```

So `blade_id("e31", 3) == blade_id("e13", 3)` — both resolve to the same
bitmask, with **no sign correction** for the transposition. Mathematically
$e_3\wedge e_1 = -e_1\wedge e_3$, so "e31" and "e13" should differ by a sign.

This affects every code path that resolves blade names through `blade_id`:

- String parsing (`_parse.py::_parse_mv_string`): `alg("1 e31")` and
  `alg("1 e13")` build identical multivectors.
- Bracket coefficient access (`_mv.py::MV.__getitem__`/`__setitem__`, via
  `Algebra._resolve_key`): `mv["e31"]` and `mv["e13"]` read/write the same
  slot.

Meanwhile, blades built via the actual wedge product are correct — e.g.
`BasisE3.e31` (`pytanga/basis/e3.py`) is computed as `self.op(self.e3, self.e1)`,
which correctly equals `-e13`. That file's own comment says
`# alias matching Perwass notation e₁₃ = −e₃₁`.

**Result: `BasisE3.e31` (the attribute) and `E3("1 e31")` / a multivector's
`["e31"]` slot disagree in sign.** The attribute is the geometrically correct
`-e13`; the string/bracket path silently treats "e31" as a positive alias for
canonical ascending "e13".

## Minimal repro

```python
from pytanga.basis import BasisE3

E3 = BasisE3()
alg = E3.e1.algebra

a = alg("1 e13")
b = alg("1 e31")
(a - b).show()          # expect e13 - (-e13) = 2 e13, but prints 0

(a + E3.e31).show()     # expect e13 + (-e13) = 0 -- correct, uses the attribute
(b - E3.e31).show()     # expect e13 - (-e13) = 2 e13, but the string-parsed
                         # "1 e31" (=b) silently equals +e13, not -e13
```

## Expected behavior

`blade_id()` (and therefore string parsing and bracket indexing) should sort
the given indices and track the sign of the permutation needed to reach
ascending order, the same way `blade_name()` normalizes to ascending order
for display. E.g. `blade_id("e31", 3)` should behave as `-blade_id("e13", 3)`
(same bitmask, sign flag of -1), consistent with `BasisE3.e31 == -BasisE3.e13`.

## Suggested fix sketch

In `blade_id`, after building `indices`, compute the sign of the permutation
that sorts `indices` into ascending order (e.g. via a simple bubble-sort /
inversion count), and return `(bitmask, sign)` or apply the sign directly to
the caller's coefficient in `_parse_mv_string` and in
`Algebra._resolve_key`/`MV.__getitem__`/`__setitem__`.

## Workaround (used in wafer-grinding)

Only use ascending-order index names/tuples (`"e12"`, `"e13"`, `"e23"` or
tuple keys `(1,2)`, `(1,3)`, `(2,3)`) for string parsing and bracket
indexing/construction; avoid mixing these with descending-order attribute
names like `e31` in the same arithmetic expression. See
[`src/wafer_grinding/spin_bivector.py`](../../src/wafer_grinding/spin_bivector.py)
for an example (builds results via `algebra({(1,2): ..., (1,3): ..., (2,3): ...})`).
