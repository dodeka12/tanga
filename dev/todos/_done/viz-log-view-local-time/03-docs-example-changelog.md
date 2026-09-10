# Phase 3 — Docs, example, changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Document the new flags, demonstrate them in the example, and record the change
in the branch changelog.

## Files

- Edit: `docs/py/viz/visualizer/split-views.md`
- Edit: `py/examples/viz/ui/static/log_view.py`
- New: `docs/changelog/2026-09-09_fix-misc.md`

## Steps

- [x] **3.1 — Document the flags**
  - In `docs/py/viz/visualizer/split-views.md`, note that the first column
    shows local time with microseconds by default and that `show_date` /
    `show_utc_offset` opt into the date and local UTC offset.
- [x] **3.2 — Update the example**
  - In `py/examples/viz/ui/static/log_view.py`, demonstrate the flags (e.g.
    `show_date=True, show_utc_offset=True`) with a brief comment; keep the
    `Keywords:` header per `dev/workflows/example-docs.md`.
  - Regenerate `docs/py/examples/viz/ui/static/log_view.md` with
    `uv run python tools/generate-example-docs.py`.
- [x] **3.3 — Branch changelog**
  - Create `docs/changelog/2026-09-09_fix-misc.md` with title
    `# Changes since version 2.0.0` (from `uv run python tools/last-release.py`)
    and a `## New Features` bullet per `dev/workflows/changelog.md`.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`

## Notes

- The changelog index entry (`docs/changelog/index.md`) is added at PR time
  (hash rename), per `dev/workflows/changelog.md` — not in this phase.
- This change is additive to a display view; no architecture doc update is
  required.