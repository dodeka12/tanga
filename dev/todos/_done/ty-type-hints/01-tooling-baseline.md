# Phase 1 — Tooling & baseline inventory

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Install `ty`, add the `[tool.ty]` scaffolding, capture a machine-readable
inventory of the missing annotations, and leave the repo in a state where later
phases can be gated per-directory.

## Files

- Edit: `pyproject.toml` — add `[tool.ty]` (do **not** yet add `ANN` to
  `extend-select`; that is Phase 8).
- Edit: `uv.lock` — via `uv add --dev ty`.
- Edit: `main.py` — `def main() -> None:`.
- New: `dev/todos/ty-type-hints/inventory-ann.json` — committed baseline.

## Steps

- [x] **1.1 — Install ty as a dev dependency**
  - `uv add --dev ty`
  - Confirm with `uv run ty --version` (pin the resolved version in `uv.lock`).
- [x] **1.2 — Capture the baseline inventory**
  - `uv run ruff check --select ANN --output-format=json py/pytanga py/examples > dev/todos/ty-type-hints/inventory-ann.json`
  - Verify the JSON parses (`uv run python -c "import json,sys; json.load(open('dev/todos/ty-type-hints/inventory-ann.json'))"`).
  - Baseline captured: **1,398** items total — `ANN001`=662, `ANN003`=13,
    `ANN201`=14, `ANN202`=191, `ANN204`=53, `ANN205`=2 (**935 gated**
    missing-annotation items) plus `ANN401`=463 (visibility only, not gated).
- [x] **1.3 — Add the `[tool.ty]` config** (correctness gate; scoped to library +
  examples)
  - Add `[tool.ty.rules]` with the four recommended rules and
    `[tool.ty.src] include = ["py/pytanga", "py/examples"]` (see README contract).
  - Record the measured baseline as the triage worklist: `uv run ty check
    py/pytanga` → **692** diagnostics (per-directory table in the README).
  - ty is a **gate**: each later phase must leave its paths at 0 ty diagnostics,
    by fixing genuine bugs / annotation inaccuracies or by adding
    `# ty: ignore[<rule>]  # <reason>` for verified false positives (see the
    README "Suppression convention").
- [x] **1.4 — Annotate `main.py`**
  - `def main() -> None:` (single missing return; keeps the Phase-8 global ruff
    gate clean).
- [x] **1.5 — Fix the confirmed bugs ty surfaced (group A)**
  - `py/pytanga/algebra/_mv.py`: remove the duplicated `@property` on
    `MV.is_versor` — currently `mv.is_versor` raises
    `TypeError: 'property' object is not callable`.
  - `py/pytanga/algebra/_mv_utils.py`: `to_rotor()` — raise a clear `ValueError`
    when neither `vec_pair` nor `bivec` is provided (currently
    `AttributeError: 'NoneType' object has no attribute 'is_grade'`).
  - `py/pytanga/blade_mask/_mask.py`: reconcile `_ids_from_mv_list`'s `set[int]`
    return with its `list[int]` annotation, behavior-preserving (return a sorted
    list, or widen the annotation to `set[int]` and adjust the caller).
  - `py/pytanga/matrix/_data.py`: fix the `TYPE_CHECKING` import
    `from .algebra import Algebra` → `from pytanga.algebra import Algebra`.
  - Add focused regression coverage for the fixed bugs (e.g. `mv.is_versor`
    returns a bool; `to_rotor(0.5)` raises `ValueError`).

## Validation

`uv run ty check py/pytanga py/examples` runs (baseline recorded — not yet zero);
`uv run ruff check --select ANN --output-format=json py/pytanga py/examples`
reproduces `inventory-ann.json`; `uv run pytest -q` passes after the 1.5 fixes.

## Notes

- Do **not** add `ANN` to `extend-select` yet — per-phase gates use
  `--select ANN --ignore ANN401 <paths>` on the CLI so untyped directories don't
  fail unrelated checks.  `extend-select` + `per-file-ignores` land in Phase 8.
- `ty` is an early-stage tool; pin it via `uv add --dev ty` and re-check the four
  rules' defaults if the version changes behavior.
- Two ratchets run in parallel: the ruff `ANN` inventory (935 gated items) shrinks
  per phase, and the `ty` worklist (692 in `py/pytanga`) shrinks to 0 per
  directory.  Phase 8 drives both to zero for `py/pytanga` + `py/examples`.
