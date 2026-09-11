# Phase 5 — Example, docs, changelog, full validation

## Goal

Exemplify and document the file chooser; update the changelog; run the full
suite.

## Steps

- [x] **5.1 — Example (`py/examples/viz/interaction/file_chooser.py`)**
  - A `VisualizerApp` with a `FileChooserView` (or `add_file_chooser`) whose
    `on_change` reads/echoes the chosen path, and a button that calls
    `open_file_chooser` to open the browser from the backend.

- [x] **5.2 — Docs**
  - Add a "File Chooser" page/section under `docs/py/viz/visualizerapp/`
    (mkdocs nav + `index.md` row) documenting `add_file_chooser` /
    `open_file_chooser`, the modal behavior, `root=`, and the `on_change`
    event.

- [x] **5.3 — Changelog**
  - Append a "File chooser" bullet to
    `docs/changelog/2026-08-26_feat-small-extensions.md`.

- [x] **5.4 — Full validation**
  - `uv run pytest -q` + `uv run ruff check` on touched Python.

## Validation

`uv run pytest -q && uv run ruff check py/pytanga/viz/`
