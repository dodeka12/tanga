# Phase 6 — Example authoring workflow + cline rule

## Goal

Make the example-doc convention durable: capture it in an internal workflow
doc and link it from the cline rules, so future examples (and coding agents)
get the right header comments automatically.

## Steps

- [x] **6.1 — Workflow doc (`dev/workflows/example-docs.md`)**
  - Document the required header for a new example under `py/examples/`:
    - a module docstring with a one-line description (`<name>.py — …`);
    - a `Run with: uv run python py/examples/<path>` line;
    - a trailing `Keywords: <comma-separated>` line (task-oriented, reused
      across related examples);
    - for `.ipynb`, the same description + `Keywords:` in the **first markdown
      cell**.
  - Note that after adding/editing an example, re-run
    `uv run python tools/generate-example-docs.py` so its doc page and nav entry
    are regenerated (and run `--check` in CI).

- [x] **6.2 — Link it from `.clinerules/rules.md`**
  - Add a rule pointing to `dev/workflows/example-docs.md` for adding/editing
    examples (mirroring how the changelog and pull-request workflows are
    already referenced there).

- [x] **6.3 — Cross-reference from Phase 1**
  - Update `01-example-metadata.md` to cite the workflow doc as the source of
    truth for the `Keywords:` convention.

## Validation

```
uv run python tools/generate-example-docs.py --check
uv run ruff check py/examples tools/generate-example-docs.py docs/_hooks/examples_nav.py
```
