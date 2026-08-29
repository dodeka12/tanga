# Phase 2 — Generator (`tools/generate-example-docs.py`)

## Goal

A single, idempotent generator that turns the example metadata (Phase 1) into
committed doc pages that mirror the folder tree and embed each example's source.

## Steps

- [ ] **2.1 — Scan + parse**
  - Walk `py/examples/` (skip `__pycache__` / `*.pyc`).
  - For each `.py`: parse the module docstring via `ast` into
    title (first line, `name.py — …` prefix stripped), description (remaining
    lines minus the `Run with:` block and `Keywords:` line), run command, and
    keywords.
  - For each `.ipynb`: read the first markdown cell for title + `Keywords:`.
  - Fall back to the title + folder tokens when `Keywords:` is missing.

- [ ] **2.2 — Per-example pages**
  - Emit `docs/py/examples/<rel-path>.md` with:
    - H1 title;
    - a visible keyword list (also the plain text MkDocs search indexes);
    - the description;
    - the `uv run python …` run command (scripts) or source link (notebooks);
    - the **full embedded source code** — `.py` as one fenced `python` block,
      `.ipynb` as its code cells in `python` fences;
    - a GitHub source link.

- [ ] **2.3 — Topic index pages**
  - Emit `docs/py/examples/<topic>/index.md` per folder with a table
    `Example | Keywords | Description` and that topic's aggregate keyword list.

- [ ] **2.4 — Root index**
  - Emit `docs/py/examples/index.md`: how to run examples, links to every topic,
    and a full **keyword → examples** index.

- [ ] **2.5 — Nav subtree**
  - Emit `docs/py/examples/_nav.json` (the Examples nav subtree mirroring the
    folder tree) for the Phase 3 hook to inject.

- [ ] **2.6 — Idempotency + `--check`**
  - Make generation deterministic and add a `--check` mode that exits non-zero
    on any diff.

## Validation

```
uv run python tools/generate-example-docs.py && git diff --exit-code
uv run python tools/generate-example-docs.py --check
uv run ruff check tools/generate-example-docs.py
```
