# Phase 1 — Example metadata (description + keywords)

## Goal

Give every example a parseable, searchable header so the generator (Phase 2)
can produce one keyworded doc page per example. No behavior changes.

## Steps

- [x] **1.1 — Inventory**
  - Enumerate all `py/examples/**/*.py` and `py/examples/**/*.ipynb`
    (skipping `__pycache__`), grouped by folder, and confirm the full list
    against the current tree (~85 scripts + 3 notebooks + `binding_demo.py`).

- [x] **1.2 — `.py` examples: description + `Keywords:`**
  - For every `py/examples/**/*.py` (and `py/examples/binding_demo.py`), make
    sure the module docstring has:
    1. a one-line description in its first line (most already do — keep the
       `name.py — …` form);
    2. a trailing `Keywords: <comma-separated list>` line added/updated.
  - Keywords are task-oriented and reused across related examples (e.g.
    `animation`, `frame streaming`, `animate`, `orbit`, `Point`) so search
    clusters them. Keep each list concise (3–8 terms).
  - Do not change any code — docstrings only.

- [x] **1.3 — `.ipynb` examples: description + `Keywords:`**
  - For `py/examples/ga/jupyter/*.ipynb`, ensure the **first markdown cell**
    has an H1 title + a `Keywords: <comma-separated>` line (add where missing).

- [x] **1.4 — Verify coverage**
  - Add a tiny check (script or grep) confirming every example file declares a
    `Keywords:` line, and that `uv run ruff check py/examples` stays green.

## Validation

```
uv run ruff check py/examples
uv run python tools/generate-example-docs.py --check   # Phase 2; fails until it exists
```
