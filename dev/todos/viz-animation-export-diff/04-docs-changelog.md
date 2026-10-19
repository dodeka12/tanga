# Phase 4 — Developer docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the export section) — this phase
> updates it to describe the new `initial` + `deltas` + `_expandFrames` format.

## Goal

Document the new serialized animation-data format and record the change in the
branch changelog.

## Files

- **Edit** `docs/dev/architecture/viz-architecture.md` (export section)
- **Edit** `dev/todos/viz-html-export-animation-diff.md` (mark superseded / reference this plan)
- **New** `docs/changelog/2026/10/DD_feat-optimize-anim-recording.md` (branch changelog)

## Steps

- [x] **4.1 — Update the developer docs**
  - In `docs/dev/architecture/viz-architecture.md`, extend the export paragraph to
    say the animation data is stored as `initial` + per-frame `deltas` (whole-entity
    diffs) and expanded to full `frames[]` in the browser via `_expandFrames` before
    `_reconcileFrame`; note `to_dict()` still emits full `frames` for legacy consumers.

- [x] **4.2 — Mark the old analysis note superseded**
  - In `dev/todos/viz-html-export-animation-diff.md`, add a header note that the
    export-time diff is implemented by this plan (`dev/todos/viz-animation-export-diff/`),
    pointing at the still-open improvement ideas (field-level diff, short-circuit
    transform-only frames).

- [x] **4.3 — Branch changelog**
  - Follow `dev/workflows/changelog.md`: create
    `docs/changelog/2026/10/DD_feat-optimize-anim-recording.md` (DD = branch start day)
    with the `# Changes since version …` title printed by
    `uv run python tools/last-release.py`.
  - Add a `## Refactor` bullet: animated HTML export now stores frame 0 + per-frame
    entity deltas and expands them at load, so static entities are stored once instead
    of once per frame.

## Validation

```bash
uv run mkdocs build --strict
```

## Notes

- Do **not** touch `docs/changelog/index.md` here — that entry is added at PR time
  after the hash rename (see `dev/workflows/changelog.md` /
  `dev/workflows/pull-request.md`).
