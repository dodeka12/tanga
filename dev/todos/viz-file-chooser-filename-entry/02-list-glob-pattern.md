# Phase 2 — `pattern` glob filter in `list_directory`

## Goal

Add a dynamic, always-glob `pattern` filter to `list_directory` and forward it
from the `file_browser_navigate` handler.

## Files

- Edit: `py/pytanga/viz/_file_browser.py`
- Edit: `py/pytanga/viz/_layout.py` (`_handle_file_browser_navigate`)
- Edit: `py/tests/viz/test_file_chooser.py`

## Steps

- [x] **2.1 — `list_directory(pattern=…)`**
  - Add `pattern: str = ""`; when non-empty, additionally skip non-directory
    entries where `fnmatch.fnmatchcase(name.lower(), pattern.lower())` is false
    (after the existing `file_filter` check).  Update the docstring.
- [x] **2.2 — Forward `pattern` from the navigate handler**
  - In `_handle_file_browser_navigate`, read `payload.get("pattern", "")` and
    pass it to `list_directory`.
- [x] **2.3 — Tests**
  - Add `test_list_directory_pattern` (a literal filename glob and a `*` glob,
    case-insensitive), plus a dispatch test that a navigate payload carrying
    `pattern` narrows the pushed listing.

## Validation

```
uv run pytest py/tests/viz/test_file_chooser.py -q
```

## Notes

- `pattern` is distinct from `file_filter`: it is **always** a glob (a bare
  `foo.json` matches only that file, not every `*.foo.json`), and both filters
  must match.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
