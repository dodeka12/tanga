# Phase 1 — `existing_only` on the Python model

## Goal

Add the `existing_only` flag to `FileChooser`, `FileChooserView`, and
`FileChooserDialog`, serialize it, and lock it in with tests.

## Files

- Edit: `py/pytanga/viz/_controls.py` (`FileChooser`)
- Edit: `py/pytanga/viz/views/control_views.py` (`FileChooserView`)
- Edit: `py/pytanga/viz/_dialog.py` (`FileChooserDialog`)
- Edit: `py/tests/viz/test_file_chooser.py`

## Steps

- [x] **1.1 — `FileChooser.existing_only`**
  - Add `existing_only: bool = True` to `FileChooser` and include
    `"existing_only": self.existing_only` in `_fields()` (always present, like
    `folders_only`).
- [x] **1.2 — `FileChooserView` pass-through**
  - Add an `existing_only: bool = True` kwarg to `FileChooserView.__init__` and
    forward it to the wrapped `FileChooser`.
- [x] **1.3 — `FileChooserDialog` pass-through**
  - Add an `existing_only: bool = True` kwarg to `FileChooserDialog.__init__`,
    store it, and forward it in `build_dialog` → `FileChooserView(...)`.
- [x] **1.4 — Serialization tests**
  - Update `test_file_chooser_serialization` (exact dict gains
    `"existing_only": True`), `test_file_chooser_view_serialization` (assert
    `data["existing_only"] is True`), and
    `test_file_chooser_dialog_serialization` (assert
    `content["existing_only"] is True`).
  - Add a test that `FileChooserDialog("fc", existing_only=False)` serializes
    `content["existing_only"] is False`.

## Validation

```
uv run pytest py/tests/viz/test_file_chooser.py -q
```

## Notes

- `existing_only=True` is the default so existing open-dialog call sites are
  unchanged.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
