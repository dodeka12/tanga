# Phase 5 — Wire Save As in the image-labeling app

## Goal

Make the app's Save As… dialog a save-mode chooser that filters to `.json` and
appends `.json` to a filename with no extension.

## Files

- Edit: `py/examples/apps/image_labeling_app.py`

## Steps

- [ ] **5.1 — Save dialog**
  - In `_show_save_dialog`, build
    `FileChooserDialog("save_file", on_accept=_on_file, existing_only=False,
    file_filter=".json")` (prefill `value` with the current basename when
    `self._file_path` is set, if the frontend supports it — see Notes).
- [ ] **5.2 — Extension normalization**
  - In the save `_on_file`, append `.json` when `os.path.splitext(path)[1] == ""`
    before setting `self._file_path` and saving.

## Validation

```
uv run python -c "import ast; ast.parse(open('py/examples/apps/image_labeling_app.py').read())" \
  && uv run ruff check py/examples/apps/image_labeling_app.py \
  && uv run ty check
```

## Notes

- The Open… dialog is unchanged (`existing_only` defaults to `True`).
- Prefill is optional polish: if the `value`→basename split is not yet
  implemented in phase 4, skip prefill and only pass the two new kwargs.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
