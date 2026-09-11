# Phase 1 — Python `FileChooser` model + `list_directory`

## Goal

Add the backend data model and filesystem listing, mirroring the existing
`Control` + `serialize_controls` approach.

## Steps

- [x] **1.1 — `list_directory` (`py/pytanga/viz/_file_browser.py`, new)**
  - `list_directory(path, *, root=None, show_hidden=False) -> dict` using
    `pathlib.Path` / `os.scandir`: resolve *path* (default `root` or
    `Path.home()`), and return `{ "path": <resolved str>, "entries": [...] }`
    where each entry is `{ "name", "path", "is_dir" }` — dirs-first, then
    alphabetical; dot-files omitted unless `show_hidden`.
  - On failure return `{ "path": path, "entries": [], "error": "missing" | "permission" }`.
  - If `root` is given and the resolved *path* escapes it, clamp to `root`.

- [x] **1.2 — `FileChooser` dataclass (`_controls.py`)**
  - `FileChooser(Control)`: `kind="file_chooser"`, `value: str = ""`,
    `placeholder: str = ""`, `root: str | None = None`, `accept: str = ""`,
    `on_change: Handler | None = None`.

- [x] **1.3 — Serialization**
  - Add a `FileChooser` branch to `_serialize_one_control` →
    `{ id, kind, label, value, placeholder, root, accept }`.

- [x] **1.4 — Export**
  - Export `FileChooser` from `py/pytanga/viz/__init__.py`.

- [x] **1.5 — Tests (`py/tests/viz/test_file_chooser.py`, new)**
  - `list_directory` on a temp dir: dirs-first order, hidden omitted, error on
    a missing directory, root clamping.
  - `FileChooser` serialization shape.

## Validation

`uv run pytest py/tests/viz/test_file_chooser.py -q`
