# Phase 3 — Remove vendored assets + obsolete tool

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Delete the now-unused third-party files and the vendor build tool.

## Files

- Delete: `js/three/` (recursive)
- Delete: `py/pytanga/viz/templates/vendor/` (recursive)
- Delete: `tools/vendor-third-party.py`

## Steps

- [x] **3.1 — Remove vendored directories + tool**
  - `git rm -r js/three py/pytanga/viz/templates/vendor tools/vendor-third-party.py`.

## Validation

`uv run python -c "from pathlib import Path; assert not Path('js/three').exists() and not Path('py/pytanga/viz/templates/vendor').exists() and not Path('tools/vendor-third-party.py').exists(); print('removed')"`

## Notes

- `js/tanga-viewer.js` + `js/tanga-viewer.manifest.json` stay (our CDN bundle).
- The wheel no longer ships the ~2.4 MB vendor directory.
