# Phase 5 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Update the developer docs to reflect the widened reconciliation allow-list and
record the fix in the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- New: `docs/changelog/2026/10/05_fix-small-bugs.md` (per
  `dev/workflows/changelog.md`; `DD` = branch start day)
- Edit: `docs/changelog/index.md` (entry added at PR time — see `pull-request.md`)

## Steps

- [x] **5.1 — `viz-architecture.md` ("Layout re-push" bullet, ~lines 82–90)**
  - Rewrite the bullet to say the frontend reuses **every content view** by
    stable id (scene panes, simple controls, `log_view`, `file_chooser_view`,
    `table_view`, `progress_bar_view`, and `group`); only the pure-layout
    containers `split`/`stack`/`toolbar`/`menu` are rebuilt and re-attach the
    reused children in the new order.
  - Note the identity-safe teardown invariant: a registry-backed view only
    forgets its runtime-registry entry when it still owns it.

- [x] **5.2 — `viz-controls-and-interactions.md`**
  - Update the reconciliation/`_viewRegistry` invariant (single live-view
    registry, identity = `View.id`) to list the now-reusable content views and
    the identity-safe `forgetMessageView` / `unregisterFileBrowser` teardown.
  - Extend the `control_state` runtime-state section with `collapsed` (group
    only) and document `GroupView.on_toggle` / `set_collapsed` plus the
    `control:group_toggle` dispatch that mutates `GroupView.collapsed`.

- [x] **5.3 — Changelog (`docs/changelog/2026/10/05_fix-small-bugs.md`)**
  - Title from `uv run python tools/last-release.py` (currently `2.14.0`, i.e.
    `# Changes since version 2.14.0`).  Bullets:
    - **Bug Fixes** — `LogView` keeps receiving `.log()` updates after any
      `set_layout()` re-push that reuses its `id`.
    - **New Features / enhancements** — layout reconciliation now preserves
      `log_view`, `file_chooser_view`, `table_view`, `progress_bar_view`, and
      `group` across re-pushes instead of rebuilding them.
    - **New Features** — `GroupView.on_toggle` / `set_collapsed`: the group
      collapse state is backend-synced (pushed via `control_state`) and settable
      programmatically.

- [x] **5.4 — Regenerate + verify**
  - Run the full gate: `mkdocs build --strict`, bundle drift check, pytest, JS
    syntax + unit tests.

## Validation

```
uv run python tools/last-release.py
uv run mkdocs build --strict
uv run python tools/build-viewer-js.py --check
uv run pytest py/tests/viz -q
node js/dev/tests/check-syntax.mjs
node --test 'js/dev/tests/*.test.mjs'
```

## Notes

- The `docs/changelog/index.md` entry is finalized at PR time
  (`dev/workflows/pull-request.md`); the branch changelog filename is
  `05_fix-small-bugs.md` (branch `fix/small-bugs`).
