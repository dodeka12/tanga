# Phase 8 — Docs + changelog

## Goal

Document the canonical-frame + transform-placement architecture and record the
change in the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/changelog/2026/09/<DD>_<branch-name>.md` (branch changelog; final
  name per `dev/workflows/changelog.md`)

## Steps

- [x] **8.1 — architecture docs**
  - In `viz-architecture.md`, document the canonical-frame + `Transform`
    placement contract: entities render in a canonical frame (linear +Y, planar
    XY/+Z, volumes at origin), placement/rotation is the node `Transform`
    (quaternion TRS, `geometry/transform.py`), content is shape-only, and
    `set_entity` diffs shape vs placement. Note the quaternion wire
    (`transform.rotation: [x,y,z,w]`) and the `geometry/transform.py` /
    `geometry/transforms.py` split (with `viz` re-export shims).

- [x] **8.2 — changelog**
  - Per `dev/workflows/changelog.md`: create the branch changelog
    (`docs/changelog/2026/09/DD_<branch-name>.md`, branch name with `/` → `-`)
    with the since-relative title from `uv run python tools/last-release.py`
    (currently `2.9.0` — re-run to confirm). A `## Bug Fixes` bullet for the
    `Circle` center update, and a `## Refactor` bullet for canonical-frame +
    transform placement (quaternion `Transform`, shape-only serialization,
    `Frustum` re-parameterization). Do not predict a version number.

- [x] **8.3 — full validation**
  - `uv run pytest -q && uv run mkdocs build --strict`.

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- The changelog filename follows the actual implementation branch name and is
  renamed to the hash form at PR time per `dev/workflows/pull-request.md`; do
  not predict the version number.
- Update the `Status:` line in `README.md` to `Done` once all phases pass.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
