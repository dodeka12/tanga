# Phase 1 — GA Folder Restructure

## Goal

Create `docs/py/ga/`, move the eight GA topic folders into it, author
`ga/index.md` as the GA overview, and turn `docs/py/index.md` into a slim
"pytanga" landing. Update `mkdocs.yml` and fix GA cross-references so the site
still builds.

## Files

- New: `docs/py/ga/index.md`
- Edit: `docs/py/index.md`
- Edit: `mkdocs.yml`
- Move: `docs/py/{algebra,basis,blade-mask,matrix,solver,tensors,expression,geometry}/` → `docs/py/ga/`
- Edit: any `docs/py/ga/**/*.md` with stale relative links

## Steps

- [x] **1.1 — Create `docs/py/ga/` and move the eight GA topic folders**
  - `git mv docs/py/algebra docs/py/ga/algebra` (repeat for `basis`,
    `blade-mask`, `matrix`, `solver`, `tensors`, `expression`, `geometry`).
  - `docs/py/env/`, `docs/py/examples/`, and `docs/py/viz/` stay put.
  - Confirm `docs/py/ga/` now contains exactly the eight folders.

- [x] **1.2 — Author `docs/py/ga/index.md` (GA overview)**
  - Copy the GA overview content from the current `docs/py/index.md`
    (title, "Topics" table, Quick Start, AI-tool docs access, background).
  - Drop the viz-specific "Example Scripts → Visualization" and visualizer
    mentions; keep the GA Topics rows and GA quick-start code.
  - Fix relative links for the new depth: `env/index.md` → `../env/index.md`,
    `algebra/index.md` → `algebra/index.md`, `basis/index.md` → `basis/index.md`,
    `viz/index.md` → `../viz/index.md`, `examples/index.md` →
    `../examples/index.md`.

- [x] **1.3 — Rewrite `docs/py/index.md` as a slim landing**
  - New H1 "pytanga" with a one-paragraph intro plus a small table linking to
    `ga/index.md` (Geometric Algebra), `viz/index.md` (Visualization),
    `env/index.md` (Environment & Setup), `examples/index.md` (Examples).
  - Keep a short note that GA examples live under `examples/ga/` and viz
    examples under `examples/viz/`.

- [x] **1.4 — Update `mkdocs.yml` nav**
  - Add a top-level `Python (pytanga)` section with `Overview: py/index.md`
    (place it after `Environment`, before `Geometric Algebra`).
  - Change the `Geometric Algebra` section overview from `py/index.md` to
    `py/ga/index.md` and prefix every GA sub-page path with `ga/` (see the
    target nav in `README.md`).

- [x] **1.5 — Fix cross-references in the moved GA files**
  - Grep `docs/py/ga/` for `../viz/`, `../env/`, `../examples/`, and
    `../index.md` and re-point anything that now crosses one extra directory
    boundary (add one `../`). Intra-GA sibling links (`../algebra/`, etc.) are
    already correct and should not change.

## Validation

```powershell
uv run mkdocs build --strict
Get-ChildItem docs/py -Recurse -Include *.md |
  Select-String -Pattern 'py/algebra/|py/basis/|py/blade-mask/|py/matrix/|py/solver/|py/tensors/|py/expression/|py/geometry/'
```

The second command must return no matches (no page or nav still references the
old top-level GA paths).

## Notes

- Moving the whole folder tree preserves each topic's internal `index.md` and
  relative sibling links, so the main breakage risk is links that point *out*
  of `ga/`.
- Do not touch `docs/py/examples/` — it is auto-generated and references
  example paths, not GA doc paths.
