# Phase 2 — Rewire the delivery path

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Point the offline branches of `_cdn.py` and `_bootstrap/_html.py` at the new
`_offline.py` module instead of the removed vendored files.

## Files

- Edit: `py/pytanga/viz/export/_cdn.py`
- Edit: `py/pytanga/viz/export/_bootstrap/_html.py`

## Steps

- [x] **2.1 — `build_library_script_tag("offline")`**
  - Delegate to `_offline.offline_library_js()` (lazy import); drop
    `_VENDOR_DIR` / `_OFFLINE_BUNDLE` constants from `_cdn.py`.
- [x] **2.2 — `third_party_scripts("offline")`**
  - Return `_offline.offline_third_party_html()` instead of reading vendored files.
- [x] **2.3 — `offline_katex_css()`**
  - Return `_offline.offline_katex_css()`; remove the `_read_vendor` helper.

## Validation

`uv run ruff check py/pytanga/viz/export && uv run python -c "from pytanga.viz.export._html import render_snapshot; render_snapshot([], {}, delivery='offline'); print('offline ok')"`

## Notes

- `delivery="cdn"` / `"inline"` are unchanged.
