# Example Docs Gallery — Overview

**Created:** 2026-08-29 | **Status:** In progress | **Branch:** `feat/example-docs`

## Goal

Make it easy for users to find a fitting example for their task, straight from
the docs:

- **one doc page per example**, grouped by topic exactly like the
  `py/examples/` folder tree;
- every page carries **searchable keywords** so MkDocs search surfaces the
  right example for a task;
- every page embeds the **full source code** of the example so users can read
  it without leaving the docs;
- a **top-level "Examples" nav section** (after Home) with the whole tree, plus
  a keyword index on the overview page.

## Architecture (short)

- **Metadata lives in the examples.** Each `.py` example's module docstring gets
  a one-line description (already present on most) plus a `Keywords:` line; each
  `.ipynb` gets the same in its first markdown cell. Metadata is co-located and
  self-documenting, and it also feeds `install_examples()`.
- **A generator builds the pages.** `tools/generate-example-docs.py` walks
  `py/examples/`, parses the docstrings/notebooks, and emits committed markdown
  under `docs/py/examples/` mirroring the folder tree:
  - `index.md` — overview + full **keyword → examples** index;
  - `<topic>/index.md` — per-folder table (`Example | Keywords | Description`)
    plus that topic's aggregate keywords;
  - `<topic>/<name>.md` — per-example page (title, keywords, description, run
    command, GitHub link, and the **embedded source code**).
  It also emits `docs/py/examples/_nav.json` (the nav subtree for the section).
- **A hook injects the nav.** `docs/_hooks/examples_nav.py` (`on_config`) reads
  `_nav.json` and injects the Examples section into `config["nav"]`; `mkdocs.yml`
  gains a `hooks:` entry. With an explicit `nav`, MkDocs only builds pages listed
  there, so the hook is what makes every generated page searchable/built.

## Decisions (confirmed)

- Keyword source = a `Keywords: <comma-separated>` line at the **end** of each
  example's module docstring (and first markdown cell for notebooks). Fallback
  to the title + folder tokens when missing, so the generator never hard-fails.
- Doc pages **embed the full source** (`.py` as one fenced `python` block;
  `.ipynb` as its code cells) rather than only linking to GitHub.
- Output tree = `docs/py/examples/<mirror of py/examples/>`, committed to the
  repo; regenerated idempotently (with a `--check` mode for CI/drift).
- Nav is injected at build time from the generator's `_nav.json` (single source
  of truth), not hand-maintained in `mkdocs.yml`.
- Notebooks are **linked externally**, not compiled by `mkdocs-jupyter`
  (matches the existing "linked externally, not compiled" convention).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-example-metadata.md](./01-example-metadata.md) | Inventory every example; add/verify a description + `Keywords:` line in each docstring / first notebook cell |
| 2 | [02-generate-doc-pages.md](./02-generate-doc-pages.md) | `tools/generate-example-docs.py`: parse metadata, emit per-example pages (with source), topic indexes, keyword index, `_nav.json` |
| 3 | [03-nav-integration.md](./03-nav-integration.md) | `docs/_hooks/examples_nav.py` + `hooks:` in `mkdocs.yml` so the section is built and searchable |
| 4 | [04-consolidate-existing-lists.md](./04-consolidate-existing-lists.md) | Point the scattered example tables at the new section (single source of truth) |
| 5 | [05-changelog-validation.md](./05-changelog-validation.md) | Changelog + full validation |
| 6 | [06-example-authoring-workflow.md](./06-example-authoring-workflow.md) | `dev/workflows/example-docs.md` + `.clinerules/rules.md` link for authoring new examples |

## Testing as you go

- `uv run python tools/generate-example-docs.py` — must be idempotent (re-run
  yields no diff) and `--check` must pass.
- `uv run mkdocs build --strict` — the docs gate (broken links / nav warnings
  fail it).
- `uv run ruff check` on touched Python (`tools/`, `docs/_hooks/`).
- `uv run pytest -q` (full suite) at the end.

## Non-goals

- Compiling/executing the notebook examples in the docs (they stay external).
- Changing `py/pytanga/` library code.
- Migrating the existing internal warning banners / other unrelated docs.
- Auto-publishing/deploying (docs deploy is unchanged).
