# Phase 4 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture. If this work introduces or changes architecture, update the
> developer docs.

## Goal

Clarify the documented transform-placement invariant and record the change in the
branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/changelog/2026/10/05_fix-html-export-transform.md`

## Steps

- [ ] **4.1 — Clarify the documented invariant**
  - In `viz-architecture.md` "Canonical frame + transform placement", state
    explicitly that even an identity `Transform` gets a wrapper `THREE.Group`
    (so `entry.obj !== entry.mesh` always).
- [ ] **4.2 — Write the branch changelog**
  - Per `dev/workflows/changelog.md`: title via
    `uv run python tools/last-release.py`, then add a "Bug Fixes" bullet for the
    always-wrap invariant. Note this branch also carries the animation
    transform-reapplication fix (already applied) and record it in the same file.
    Use the branch's actual start date in the filename (assumed `2026-10-05`
    here). Do **not** touch `docs/changelog/index.md` — that happens at PR time
    (see `dev/workflows/pull-request.md`).

## Validation

```
uv run mkdocs build --strict
uv run pytest py/tests/viz -q
```

## Notes

- The architecture note says to update the developer docs if architecture changes;
  here the change *aligns* code to the already-documented invariant, so 4.1 is a
  clarification, not a new architecture contract.
