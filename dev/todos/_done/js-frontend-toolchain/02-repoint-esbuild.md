# Phase 2 — Repoint esbuild discovery to `js/dev/`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

The offline HTML export (`delivery="offline"`) resolves esbuild from
`dev/node_modules`; repoint it to the new `js/dev/node_modules` location so the
consolidated toolchain keeps working. This is Python-only — no JS runs here.

## Files

- Edit: `py/pytanga/viz/export/_offline.py`
- Edit: `py/tests/viz/test_export_delivery.py`

## Steps

- [x] **2.1 — `find_esbuild()` (`_offline.py`)**
  - Change the repo-local candidate from
    `parents[4] / "dev" / "node_modules" / "esbuild" / "bin" / "esbuild"` to
    `parents[4] / "js" / "dev" / "node_modules" / "esbuild" / "bin" / "esbuild"`.
  - Keep the order: `TANGA_ESBUILD` env → repo `js/dev/node_modules/...` →
    `shutil.which("esbuild")`/`esbuild.cmd`.
  - Update the `OfflineToolchainError` hint to reference `npm install` inside
    `js/dev/` (instead of `npm install -g esbuild`).

- [x] **2.2 — `test_export_delivery.py` comment**
  - Update the "install the dev JS deps locally (`npm install` in `dev/`)" note
    to `js/dev/`.
  - No test-logic change: the toolchain tests already skip when node/esbuild are
    absent (that remains correct).

## Validation

```
uv run ruff check py/pytanga/viz/export/_offline.py py/tests/viz/test_export_delivery.py
uv run pytest py/tests/viz/test_export_delivery.py -q
```

## Notes

- `find_node()` (`shutil.which("node")`) is unchanged — node is on PATH in a
  dev checkout, not vendored in the repo.
- The offline tests are gated behind a `requires_toolchain` skip; CI runs them
  skipped (no node/esbuild in CI) and that stays true.
