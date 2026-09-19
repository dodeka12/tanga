# Phase 4 — Documentation, example, and changelog

## Goal

Document the new composition binding in the user docs, add a runnable example,
record the feature in the branch changelog, and run the full validation gate.

## Files

- Edit: `docs/py/ga/expression/usage.md`
- Edit: `docs/py/ga/expression/index.md`
- New: `py/examples/ga/expression/bind_subexpression.py`
- New: `docs/changelog/2026/09/17_feat-bind-expression.md`

## Steps

- [x] **4.1 — User docs**
  - Add a "Binding a variable to a sub-expression (composition)" section to
    `docs/py/ga/expression/usage.md`: the `bind(name=expr)`/`__call__` semantics,
    the mask-must-match and no-counting-axes rules, repeated-occurrence
    consistency, and the collision `ValueError`s.

- [x] **4.2 — Index mention**
  - Add a one-line pointer in `docs/py/ga/expression/index.md` to the new usage
    section.

- [x] **4.3 — Example script + regenerate**
  - Add `py/examples/ga/expression/bind_subexpression.py` with the license header
    (`SPDX-License-Identifier: Apache-2.0` / `Copyright 2021 Christian Perwass`)
    and a module docstring per `dev/workflows/example-docs.md`:
    one-line description, a short explanation, a `Run with:` line, and a
    `Keywords:` line (`expressions, bind, composition, sub-expression, rotor`).
  - **Script scenario (E3 vectors + a fixed rotor), self-contained:**
    - `alg = BasisE3()`; `vec = BladeMask(alg, grades=[1])`;
      `R = create_rotor(alg, 0.5, Direction(1, 0, 0))` (constant rotor `MV`).
    - Local/body-frame expression built **once**, with a repeated variable:
      `v_b = Variable("v_b", vec)`, `B = alg.multivector({"e12": 1.0})`,
      `local = v_b ^ (v_b | B)` (two occurrences of `v_b`, bivector output).
    - World-frame symbol + sandwich sub-expression:
      `V = Variable("V", vec)`, `local_v = R * V * ~R` (an `Expression`, free
      `V`, vector output mask — matches `v_b`'s mask).
    - Compose: `world = local.bind(v_b=local_v)`.
    - Assert/demonstrate: `set(world.names) == {"V"}` and
      `len(world.names["V"]) == 2` (the repeated occurrence stays one shared
      variable); print these.
    - Numeric check: for `w = alg.multivector({"e1": 1.0, "e2": 2.0, "e3": 0.5})`,
      compare `world(V=w)` against `(R * w * ~R) ^ ((R * w * ~R) | B)` and print
      both.
    - Close with a one-line note that `bind` accepts an `Expression` value when
      the sub-expression's output mask equals the bound variable's mask.
  - Then run `uv run python tools/generate-example-docs.py` and its `--check`.

- [x] **4.4 — Changelog**
  - Create `docs/changelog/2026/09/17_feat-bind-expression.md` per
    `dev/workflows/changelog.md`: title from `uv run python tools/last-release.py`
    and a "New Features" bullet; do not touch `docs/changelog/index.md`.

- [x] **4.5 — Full validation**
  - Run the full gate: pytest, ruff, ty, example-docs drift check, and
    `uv run mkdocs build --strict`.

## Validation

`uv run pytest py/tests -q && uv run ruff check py/pytanga/expression py/tests/expression/test_bind_expression.py && uv run ty check py/pytanga/expression && uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`

## Notes

- No developer-doc update is required: the change is additive (one private
  helper + one new branch in an existing method) and alters no documented
  architecture.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
