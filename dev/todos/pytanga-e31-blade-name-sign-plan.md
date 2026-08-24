# Fix reversed-order blade-name sign (e31 → −e13) in string parsing / bracket indexing

**Created:** 2026-08-24 | **Status:** Planned

Related bug report: [`pytanga-e31-blade-name-sign-bug.md`](./pytanga-e31-blade-name-sign-bug.md)

## Goal

Blade names are resolved from strings and tuple/dict keys without tracking the
order of the indices, so a reversed-order name silently maps to the canonical
ascending-order blade with the **wrong sign** (e.g. `"e31"` currently equals
`"+e13"` instead of `"-e13"`). This makes string parsing / bracket access
disagree with the wedge-product attribute (`BasisE3.e31 == -BasisE3.e13`).

We will:

1. Make blade-name resolution sign-aware (general permutation sign, not just a
   one-off `e31` alias), so any index order resolves to the canonical ascending
   blade with the correct sign — consistently with `blade_name()` (which already
   normalizes to ascending order for display).
2. Ensure the predefined basis members use only the canonical ascending order
   (`e13`, never `e31` as the primary blade), while keeping a `e31` compat alias
   that returns `-e13` so existing code keeps running.
3. Add the `e31` string and the `e31` member to the 3D-space algebras
   (`BasisE3`, `BasisP3`, `BasisN3`, `BasisPGA3`) returning `-e13`.

## Background / root cause

`py/pytanga/algebra/_blade_names.py::blade_id()` builds the bitmask by OR-ing
`1 << (i-1)` for each index in the order given, ignoring the permutation sign:

```python
result = 0
for i in indices:
    result |= 1 << (i - 1)
return result
```

So `blade_id("e31", 3) == blade_id("e13", 3) == 5` with no sign. This propagates
to every name→coefficient path:

- `_parse.py::_parse_mv_string` — `alg("1 e31")` and `alg("1 e13")` build
  identical multivectors.
- `_algebra.py::_resolve_key` (str and tuple keys) — used by
  `MV.__getitem__`/`__setitem__` and by `Algebra.multivector(dict)`.
- `_mv.py::__getitem__`/`__setitem__` — `mv["e31"]` and `mv["e13"]` read/write
  the same slot with no sign.

Tuple keys have the same bug: `{(3, 1): v}` and `{(1, 3): v}` are treated
identically. Meanwhile the wedge-product attribute is geometrically correct:
`BasisE3.e31 = op(e3, e1) = -e13`. The attribute and the string/bracket path
disagree in sign.

## Design decision (chosen: option A — general permutation sign)

- Add a sign-aware resolver that returns `(bitmask, sign)`, where `sign` is the
  parity of the permutation that sorts the indices ascending (inversion-count
  parity). This makes `"e31" → (5, -1)`, `"e21" → (3, -1)`, `"e32" → (6, -1)`,
  `"e321" → (7, -1)`, and canonical names `→ (…, +1)`.
- Keep the existing `blade_id()` **order-independent** (returns the canonical
  bitmask, unsigned) so the current `test_order_independent` and every existing
  `basis.blade_id("eN")` caller keep working. The sign is only applied at the
  coefficient boundaries (parser, `multivector(dict)`, `MV.__getitem__`,
  `MV.__setitem__`), which is exactly where the bug lives.

## Changes

### Phase 1 — sign-aware blade-name resolution (core fix)

- [x] 1.1 `py/pytanga/algebra/_blade_names.py`
  - Add `_permutation_sign(indices: list[int]) -> int` (inversion-count parity:
    `+1` for even, `-1` for odd).
  - Add `blade_id_signed(name: str, dim: int) -> tuple[int, int]` that reuses the
    existing parse/validation (scalar `s`/`0`, pseudoscalar `I`, digit parsing,
    distinct + in-range checks), then returns `(bitmask, sign)`.
  - Refactor `blade_id(name, dim) -> int` to return
    `blade_id_signed(name, dim)[0]` (behavior unchanged: canonical unsigned
    bitmask).
  - Add `blade_id_signed` to `__all__`.

- [x] 1.2 `py/pytanga/algebra/_parse.py`
  - In `_parse_mv_string`, switch the primitive-blade branch from `blade_id` to
    `blade_id_signed` and accumulate `coeffs[bid] += coeff * sign`.
  - Leave the `named_basis` composite branch untouched (composites like
    `e0 = ep + em` already carry signed expansions).

- [x] 1.3 `py/pytanga/algebra/_algebra.py`
  - Add `_resolve_key_signed(key) -> tuple[int, int]`:
    - `int` → `(key, 1)`
    - `tuple` → same bitmask logic as today **plus** permutation sign (fixes the
      tuple-key sign bug too; `(0,)`/`()` stay scalar `(0, 1)`)
    - `str` → `blade_id_signed(key, self._dim)`
  - Keep `_resolve_key(key) -> int` as `_resolve_key_signed(key)[0]` (preserves
    int-returning callers such as `dev/src/dev_rotorfunc_bench.py`).
  - In `multivector()`'s dict branch, use `_resolve_key_signed` and set
    `impl.set(bid, sign * val)`.

- [x] 1.4 `py/pytanga/algebra/_mv.py`
  - `__getitem__`: `bid, sign = self._alg._resolve_key_signed(key)`;
    `return sign * self._impl.get(bid)`.
  - `__setitem__`: `bid, sign = self._alg._resolve_key_signed(key)`;
    `self._impl.set(bid, sign * value)`.

### Phase 2 — canonical basis members + `e31` compat alias

- [x] 2.1 `py/pytanga/basis/e3.py` — flip to canonical primary:
  ```python
  self.e12 = self.op(self.e1, self.e2)
  self.e13 = self.op(self.e1, self.e3)   # canonical basis blade
  self.e23 = self.op(self.e2, self.e3)
  self.e31 = -self.e13                    # compat alias: e3∧e1 = −e1∧e3
  ```
  (Values are unchanged — only which member is "primary" flips.)

- [x] 2.2 `py/pytanga/basis/p3.py`, `py/pytanga/basis/n3.py`,
  `py/pytanga/basis/pga3.py` — add the canonical bivector members plus the alias:
  ```python
  self.e12 = self.op(self.e1, self.e2)
  self.e13 = self.op(self.e1, self.e3)
  self.e23 = self.op(self.e2, self.e3)
  self.e31 = -self.e13
  ```
  (Strictly required: `e13` + `e31`; `e12`/`e23` are included for a complete,
  symmetric bivector set matching `BasisE3`.)

- [ ] 2.3 (optional, display only) `py/pytanga/basis/pga3.py::_display_basis`
  rename the non-canonical label `_entry("e31", e3.op(e1))` to `"e13"` and build
  it as `e1.op(e3)`. Sign is already handled there via the `ip(mv, pinv)`
  fallback, so this is a cosmetic consistency change; it alters displayed output.

### Phase 3 — tests

- [x] 3.1 `py/tests/algebra/test_blade_names.py`
  - Keep `test_order_independent` (still valid — `blade_id` stays order-independent).
  - Add `blade_id_signed` tests: `("e31", 3) == (5, -1)`, `("e21", 3) == (3, -1)`,
    `("e32", 3) == (6, -1)`, `("e321", 3) == (7, -1)`, `("e13", 3) == (5, +1)`;
    roundtrip via `blade_name` stays `+1`.

- [x] 3.2 `py/tests/algebra/test_algebra_e3.py` (or a new focused test file)
  - String parsing: `alg("1 e31") == -alg("1 e13")`.
  - Bracket access: `mv["e31"] == -mv["e13"]`; and `mv["e31"] = v` sets
    `mv["e13"] == -v`.
  - Tuple keys: `alg({(3, 1): v}) == -alg({(1, 3): v})`.

- [x] 3.3 `py/tests/basis/test_basis.py` (guarded by the existing `_NEEDS_BUILD`)
  - `BasisE3().e13 == BasisE3().e1 ^ BasisE3().e3` and
    `BasisE3().e31 == -BasisE3().e13`.
  - Same assertions for `BasisP3`, `BasisN3`, `BasisPGA3`.

### Phase 4 — docs / examples

- [x] 4.1 Skim `py/examples/basis/base_e3_demo.py` and
  `py/examples/basis/basis_usage.py` (both reference `E3.e31`, which still works
  returning `-e13`); update comments/output only if a printed value changes sign.
  (No changes needed — `e31`'s value is unchanged, so output is identical.)
- [x] 4.2 `docs/py/` — add a note (if a fitting page exists, e.g. the blade-mask
  construction page) that blade names are interpreted in ascending canonical
  order with a permutation sign for reversed indices (`"e31"` → `-e13`).
  (Added to `docs/py/algebra/mv.md` under "Grade and Blade Names".)

### Phase 5 — changelog

- [x] 5.1 Append to the existing branch changelog
  `docs/changelog/2026-08-24_fix-dual-pga.md` (this branch; its title is
  `# Changes since version 1.0.0`, matching `uv run python tools/last-release.py`).
  Add to the existing `## Bug Fixes` section (wrap at ~80 columns, self-contained):

  ```markdown
  - **Blade-name parsing now honors index order (sign fix)** — `blade_id()`
    gains a sign-aware companion `blade_id_signed()`; string parsing
    (`Algebra("…")`), bracket access (`mv["e31"]`), and dict/tuple-key
    construction now apply the permutation sign, so reversed names resolve
    correctly (`"e31"` → `-e13`, `"e21"` → `-e12`, `"e321"` → `-e123`).
    Previously `"e31"` silently equaled `+e13`, disagreeing with
    `BasisE3.e31 == -BasisE3.e13`.
  - **Canonical bivector attributes on 3D-space bases** — `BasisP3`,
    `BasisN3`, and `BasisPGA3` now expose `e12`/`e13`/`e23` in canonical
    ascending order plus the `e31` alias (`-e13`); `BasisE3` now defines
    `e13` canonically with `e31` as its negation.
  ```

  Note: if this fix is instead moved to its own branch, create a new
  `docs/changelog/YYYY-MM-DD_<branch>.md` per `dev/workflows/changelog.md`
  instead of appending. The `docs/changelog/index.md` entry is added only at PR
  time (after the hash-based rename), per `dev/workflows/pull-request.md`.

## Verification (end-to-end)

- [x] `uv run pytest py/tests/algebra/test_blade_names.py py/tests/algebra/test_algebra_e3.py py/tests/basis/test_basis.py py/tests/blade_mask/test_blade_mask.py -q`
- [x] Minimal repro from the bug report now behaves:
  ```python
  from pytanga.basis import BasisE3
  E3 = BasisE3()
  alg = E3.e1.algebra
  a = alg("1 e13")
  b = alg("1 e31")
  (a - b).show()          # 2 e13 (was 0)
  (b - E3.e31).show()     # 0 (was 2 e13)
  ```
- [x] `uv run ruff check` and `uv run ruff format --check` on the touched files.
- [x] Full suite before PR: `uv run pytest`.

## Non-goals / optional follow-ups

- **C++ side** — the C++ bases (`cpp/Tan.GA/BasisE3.h` etc.) use `wE31` in their
  *display* naming only; the bug is in the Python name-resolution layer, so C++
  is out of scope.
- **`Algebra.blade_id()` public method** — stays order-independent (unsigned
  canonical bitmask); the sign only matters at the coefficient boundary, which
  the parser/accessor paths now handle. Making it raise or return signed would
  be a broader API change and is out of scope.
- **PGA display labels** — renaming the remaining cyclic PGA display labels
  (`e021`, `e032`, …) is cosmetic and tracked separately in 2.3 only if desired.


