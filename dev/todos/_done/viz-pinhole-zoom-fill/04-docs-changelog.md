# Phase 4 — Developer docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`).  Update
> the "Viewport navigation" / "pinhole-framing" description to reflect the
> pane-shaped crop window and the grow-to-fill zoom behaviour.

## Goal

Document the corrected crop-window/zoom semantics and add a branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/changelog/2026/10/DD_fix-background-image-scale.md`
- Edit: `docs/changelog/index.md` (deferred to PR time)

## Steps

- [x] **4.1 — Update the architecture doc.**
  - In `docs/dev/architecture/viz-architecture.md`, the "Viewport navigation"
    bullet (and the `pinhole-framing.js` bullet if it mentions the square crop):
    note that the `{zoom, pan}` viewport folds into a **pane-shaped** crop window
    whose letterbox `{hx, hy}` grows toward `1` as zoom increases (so the image
    fills the pane and crops at the edges), and that `pinholeFraming` now also
    returns `fitHx`/`fitHy` (base fit half-extents used for pan clamping) and
    `_pinholeLetterbox`/`_pinholeFit` are retained on `camera.userData`.

- [x] **4.2 — Changelog.**
  - Create `docs/changelog/2026/10/DD_fix-background-image-scale.md` per
    `dev/workflows/changelog.md`: title from `uv run python tools/last-release.py`;
    a single `## Bug Fixes` bullet — zooming a calibrated background image now
    scales it to fill the pane (letterbox bars shrink, then crop) instead of
    pinning it to the initial fit size.

- [x] **4.3 — Changelog index (deferred).**
  - The `docs/changelog/index.md` entry is added at PR time, after the
    hash-based rename, per `dev/workflows/changelog.md` § Index update — not on
    the feature branch.

## Validation

`uv run mkdocs build --strict`

## Notes

- The changelog filename uses `DD_` + branch name with `/`→`-`; the PR-time hash
  rename happens later (see `dev/workflows/pull-request.md`).
- Only touch the paragraph describing the crop-window contract — do not rewrite
  unrelated architecture sections.
