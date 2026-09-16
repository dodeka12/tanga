# Phase 7 — Developer docs + changelog

## Goal

Record the new seams in the developer architecture docs and add the branch
changelog; run the full validation suite.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/geometry-module-layering.md`
- New: `docs/changelog/2026/09/15_feat-viz-detached-subtree.md` (branch changelog)

## Steps

- [x] **7.1 — `viz-architecture.md`**
  - Document `Scene.add_subtree` and the detached-subtree insertion flow
    (register descendants, backfill partial styles from scene defaults,
    node-first `update`/`update_entity`), and add the new `_ids.py` id helper
    to the file map.

- [x] **7.2 — `geometry-module-layering.md`**
  - Note the `expect=` hint on `analyze_operator`/`analyze` (an extension to the
    analysis layer, no layering change).

- [x] **7.3 — Branch changelog**
  - Per `dev/workflows/changelog.md`: create the changelog with the
    since-relative title from `uv run python tools/last-release.py`; `## New
    Features` bullets for (a) detached subtree insertion and (b) the
    `analyze_operator(expect=...)` hint.  Leave `docs/changelog/index.md` for PR
    time.

- [x] **7.4 — Full validation**
  - `uv run pytest -q` and `uv run mkdocs build --strict`; confirm the two
    offline-export skips (per `dev/workflows/pull-request.md`) if they appear.

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- The changelog filename uses the branch name and is renamed to the hash form at
  PR time (do not predict a version number).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture. If this
work introduces or changes architecture, update the developer docs.
