# Phase 4 — Changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Record the fixes in the branch changelog. No architecture/API docs change is
required — none of the three fixes changes a public contract (issue 3 makes the
SDF renderer match already-documented `align_center` semantics).

## Files

- New: `docs/changelog/2026/09/24_fix-algebra-hotpath-sdf-cylinder.md` (per
  `dev/workflows/changelog.md`)
- Edit: `docs/changelog/index.md` (entry finalized at PR time, per
  `dev/workflows/pull-request.md`)

## Steps

- [x] **4.1 — Create the branch changelog**
  - Run `uv run python tools/last-release.py` and use its output verbatim for the
    title (`# Changes since version <...>`).
  - Create `docs/changelog/2026/09/24_fix-algebra-hotpath-sdf-cylinder.md` with:
    - `## Bug Fixes` — `SdfObject(Cylinder(...))` now honours `align_center=0.0`
      (base at `origin`), matching the mesh renderer.
    - `## Refactor` — cache blade-name string parsing
      (`Algebra._resolve_key_signed`, per algebra) to remove the per-access parse
      cost; `Algebra` operators no longer re-check the `modulus` flag on every
      call.
  - Follow the changelog structure in `dev/workflows/changelog.md` (only include
    the sections that apply; wrap bullets at ~80 columns).

- [x] **4.2 — Verify the full gate**
  - Run the full validation gate from `dev/workflows/pull-request.md` step 1
    (`pytest`, `ruff`, `ty`, `node` checks) and fix anything that surfaces.

## Validation

```
uv run python tools/last-release.py
uv run pytest -q
uv run ruff check .
uv run ty check
```

## Notes

- The `docs/changelog/index.md` entry is finalized at PR time (hash rename +
  index entry); this phase only authors the branch changelog.
- Branch name `/` → `-` in the filename: `fix/algebra-hotpath-sdf-cylinder` →
  `fix-algebra-hotpath-sdf-cylinder`.
