# Phase 5 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`).  This
> phase only clarifies the documented background-image lifecycle and the
> `ImageData` value model; it introduces no new architecture.

## Goal

Clarify the documented background-image lifecycle and record the fix +
`ImageData.version`/`update()` in a branch changelog per
`dev/workflows/changelog.md`.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: the `ImageData` reference page (find it under `docs/py/viz/`, if present)
- New: `docs/changelog/<YYYY>/<MM>/DD_<branch-name>.md`

## Steps

- [x] **5.1 — Developer docs.**
  - In `viz-architecture.md`'s "Image background" bullet, append: on reconnect the
    quad is rebuilt from the re-sent frame (the pane's `clear_all` tears it down);
    an unchanged background keeps its previous texture on a layout re-push; and
    `set_layout` only re-sends frames whose `ImageData.version` (a per-instance
    uuid) changed.

- [x] **5.2 — `ImageData` docs.**
  - In the `ImageData` reference page, document the `version` attribute and the
    `update()` method, and the contract: reuse the instance for an unchanged image;
    call `update()` (or construct a new instance) only when the content changes.

- [x] **5.3 — Changelog.**
  - Run `uv run python tools/last-release.py`; create the branch changelog
    `docs/changelog/<year>/<month>/DD_<branch-name>.md` titled
    `# Changes since version <last-stable> (<last-rc>)` (use the script's output).
  - Add a `## Bug Fixes` bullet: **`CameraView.background_image` no longer goes
    black after a WebSocket reconnect** — the pane rebuilds the quad on
    `clear_all`; unchanged backgrounds keep their texture and are not re-sent on a
    layout re-push (versioned by a per-instance uuid, changeable via
    `ImageData.update()`).

- [x] **5.4 — Build.**
  - `uv run mkdocs build --strict` to confirm docs link cleanly.

## Validation

`uv run mkdocs build --strict`

## Notes

- Changelog naming/renaming (branch name → squashed-hash) is finalised at PR time
  per `dev/workflows/pull-request.md`; this phase only creates the branch file.
