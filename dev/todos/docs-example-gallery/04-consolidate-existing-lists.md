# Phase 4 — Consolidate existing example listings

## Goal

Replace the hand-maintained, partial example tables with links into the new
Examples section so there is one source of truth.

## Steps

- [x] **4.1 — `docs/py/index.md`**
  - Replace the "Example Scripts" table (GA examples) with a pointer to
    `py/examples/index.md` (Geometric Algebra topic).

- [x] **4.2 — `docs/py/viz/index.md`**
  - Replace the "Example Scripts" section (viz examples) with a pointer to the
    Visualization topic of the Examples section.

- [x] **4.3 — Use-case pages**
  - In `docs/py/viz/use-cases-scripts.md` and `use-cases-notebooks.md`, replace
    the inline example tables with links to the Examples section.

- [x] **4.4 — Build**
  - `mkdocs build --strict` stays green (no broken links from the rewiring).

## Validation

```
uv run mkdocs build --strict
```
