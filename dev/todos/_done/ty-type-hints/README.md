# ty + ruff ANN type-hint coverage — Overview

**Created:** 2026-09-13 | **Status:** In progress | **Branch:** `feat/more-quadric`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`, `type-system-and-storage.md`, `quadric-module.md`,
> and `viz-architecture.md`) for the subsystem(s) this work touches, so the new
> code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Add complete type-annotation coverage to the library (`py/pytanga`) and the
examples (`py/examples`) and enforce it with Astral tooling: **ty** for type
*correctness* and **ruff `ANN`** (flake8-annotations) for type-annotation
*coverage*.  `py/tests`, `main.py`, and `tools` are out of scope for now (see
Non-goals).

## Background / why two tools

`ty` checks that the types you *have* are *correct*; it has **no** rule for
*missing* annotations (confirmed against `ty`'s rule list and its
"Coming from mypy, pyright" guide, which maps `disallow_untyped_defs` /
`reportMissingParameterType` → **ruff `ANN` rules**).  So "enforce type hints"
means **ty (correctness) + ruff `ANN` (coverage)** — both Astral tools already a
natural fit for this repo (ruff 0.14.0 is in use; ty is not yet installed).

## Architecture (short)

- **`pyproject.toml`** — a `[tool.ty]` section (correctness) and
  `[tool.ruff.lint]` `extend-select = ["ANN"]` + a `per-file-ignores` entry for
  `py/tests/**` (coverage).  Config is added incrementally: `[tool.ty]` in Phase
  1, the ruff `extend-select` gate only in Phase 8.
- **`py/pytanga/**` and `py/examples/**`** — annotated in documented dependency
  order (leaf-first, per `geometry-module-layering.md`): `entity` → algebra core
  → `quadric` → `geometry` → `viz`.  No runtime or behavior changes; annotations
  only.
- **Baseline inventory** — `dev/todos/ty-type-hints/inventory-ann.json` (ruff ANN
  JSON) committed in Phase 1 as the ratchet, plus the per-subpackage tally below.

## Fixed contract (decided up front)

### Tooling

- `ty` added as a dev dependency (`uv add --dev ty`); invoked via `uv run ty`.
- **Correctness gate**: `uv run ty check <paths>` → 0.  Every ty diagnostic is
  either fixed or suppressed (see the suppression convention below).
- **Coverage gate**: `uv run ruff check --select ANN --ignore ANN401 <paths>` →
  0.  `ANN401` (ban `Any`) is *reported for visibility* (the committed inventory)
  but **is not gated** — see Decisions.
- No mypy, no pyright.

### Suppression convention (`# ty: ignore`)

- Suppress a **verified false positive** with a specific rule + reason:
  `x = f(...)  # ty: ignore[unknown-argument]  # dynamic module dispatch`.
- Multiple rules are comma-separated:
  `# ty: ignore[unsound-return-statement, invalid-argument-type]`.
- **Never** a bare `# ty: ignore` — it hides unrelated errors and loses the
  reason.  A comment on its own line suppresses a whole file (use sparingly).
- Prefer a fix; a suppression documents "correct code ty cannot follow".
- `# ty: ignore[<rule>]` is the **only** suppression ty honours here — a
  mypy-style `# type: ignore[<code>]` does *not* suppress for ty (only a bare
  `# type: ignore` or `# type: ignore[ty:<rule>]` does).
- Stale suppressions are removed: ty's `unused-ignore-comment` rule (warn) plus
  `terminal.error-on-warning = true` (the default) fail the gate when a
  suppression is no longer needed.

### Config (target shape, reached by Phase 8)

```toml
[tool.ty.rules]
dynamic-function-decorator-return = "error"
missing-type-argument = "error"
possibly-unresolved-reference = "warn"
unsound-return-statement = "error"

[tool.ty.src]
include = ["py/pytanga", "py/examples"]

[tool.ruff.lint]
unfixable = ["F401"]
extend-select = ["ANN"]
ignore = ["ANN401"]

[tool.ruff.lint.per-file-ignores]
"py/tests/**" = ["ANN"]
```

### Annotation conventions (every phase follows these)

- `from __future__ import annotations` at the top of every annotated module.
- Circular-import-sensitive names (`MV`, `Algebra`, `BladeMask`, entity types)
  imported under `if TYPE_CHECKING:` only — never at runtime.
- Entities stay "pure data containers": no runtime import of `pytanga.algebra` /
  `pytanga.MV`; annotate `MV` under `TYPE_CHECKING` (as `geometry/analysis.py` /
  `geometry/create.py` already do).
- Reuse existing aliases — `MV`, `MVLike`, `Point`, `Direction` — do not invent
  new ones.
- `__init__` and other `-> None` methods are annotated `-> None`.
- Adding annotations must not change runtime behavior (no coercion / control-flow
  changes).  The only acceptable non-annotation edits are `if TYPE_CHECKING:`
  imports and, rarely, a `# ty: ignore[rule]` with a note.

## Decisions (confirmed)

- Scope = `py/pytanga` + `py/examples` (409 untyped functions); `py/tests`
  deferred to a follow-up plan.
- Enforcement = ty + ruff `ANN` (both Astral); no mypy/pyright.
- `ANN401` (disallow `Any`) is **not gated**: it is reported for visibility (the
  committed inventory and an informational `ruff check --select ANN401`) but the
  per-phase gate is `--select ANN --ignore ANN401`.  The `Any` ban is a separate,
  more opinionated change deferred to a follow-up plan.  Config:
  `extend-select = ["ANN"]` + `ignore = ["ANN401"]`.
- ty-found **genuine bugs** are fixed (Phase 1.5 and during triage); verified
  false positives get `# ty: ignore[<rule>]  # <reason>`.
- Per-directory zero-gate: each phase leaves its paths at 0 `ANN` + 0 `ty`
  diagnostics.
- ty correctness diagnostics found while annotating are fixed in the same phase
  (or suppressed with `# ty: ignore[rule]` + a note) — never left behind.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-tooling-baseline.md](./01-tooling-baseline.md) | Install ty, add config, commit baseline inventory |
| 2 | [02-entity.md](./02-entity.md) | `pytanga/entity` (Vec3/Point/Direction) — 31 |
| 3 | [03-algebra-core.md](./03-algebra-core.md) | algebra + blade_mask + basis + codegen + expression + matrix + solver + tensor — 34 |
| 4 | [04-quadric.md](./04-quadric.md) | `pytanga/quadric` — 101 |
| 5 | [05-geometry.md](./05-geometry.md) | `pytanga/geometry` (incl. `Plane.__init__`) — 101 |
| 6 | [06-viz.md](./06-viz.md) | `pytanga/viz` — 64 |
| 7 | [07-examples.md](./07-examples.md) | `py/examples` — 78 |
| 8 | [08-enforcement-docs.md](./08-enforcement-docs.md) | pre-commit + CI + docs + changelog |

Per-subpackage untyped-function tally (from the Phase-1 AST scan):

| area | functions |
|------|---:|
| `entity` | 31 |
| `algebra`+`blade_mask`+`basis`+`codegen`+`expression`+`matrix`+`solver`+`tensor` | 34 |
| `quadric` | 101 |
| `geometry` | 101 |
| `viz` | 64 |
| `py/examples` | 78 |
| **Total** | **409** |

Per-directory `ty` diagnostic baseline (the triage worklist; `uv run ty check
py/pytanga`, 2026-09-13; `py/examples` counted in Phase 7):

| area | ty diagnostics |
|------|---:|
| `viz` | 330 |
| `geometry` | 183 |
| `expression` | 50 |
| `tensor` | 29 |
| `algebra` | 29 |
| `quadric` | 21 |
| `solver` | 12 |
| `matrix` | 10 |
| `basis` | 8 |
| `entity` | 7 |
| `codegen` | 7 |
| `blade_mask` | 6 |
| **Total (`py/pytanga`)** | **692** |

## Testing as you go

- `uv run ruff check --select ANN --ignore ANN401 <paths>` — per-phase coverage gate.
- `uv run ty check <paths>` — per-phase correctness gate (fix or suppress).
- `uv run pytest py/tests/<area>` — targeted regression per phase.
- `uv run pytest -q` — full regression (Phases 1 and 8).
- `uv run pre-commit run --all-files` — enforcement (Phase 8).

## Non-goals

- `py/tests` (deferred), `tools` (already fully annotated), and `main.py` beyond
  its single `-> None` (handled in Phase 1).
- `ANN401` (disallow `Any`) and any other opinionated lint rule.
- Runtime / behavior changes of any kind — annotation-only, **except** the
  genuine bugs ty surfaced (fixed in Phase 1.5 and during triage; verified false
  positives are suppressed rather than "fixed").
- No mypy / pyright configuration.
