# Phase 4 — Tests

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Rewrite the offline tests for the export-time download/bundle model, and test
the missing-toolchain error.

## Files

- Delete: `py/tests/viz/test_export_offline.py`
- Edit: `py/tests/viz/test_export_delivery.py`

## Steps

- [x] **4.1 — Toolchain-error test**
  - Monkeypatch `_offline.find_esbuild`/`find_node` to raise; assert
    `render_snapshot(delivery="offline")` raises `OfflineToolchainError`.
- [x] **4.2 — Offline output test (skipif)**
  - `@pytest.mark.skipif(no node/esbuild)` on a test asserting offline HTML has
    `createEntityMesh`, no import map, inlined `html2canvas`.
- [x] **4.3 — Remove vendored-asset tests**
  - Delete `test_export_offline.py` (vendored files no longer exist).

## Validation

`uv run pytest py/tests/viz/test_export_delivery.py py/tests/viz/test_export_cdn.py -q`

## Notes

- The offline test runs only when node + esbuild are present (CI provides them;
  local dev may skip).
