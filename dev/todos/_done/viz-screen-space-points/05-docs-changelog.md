# Phase 5 — Changelog + docs

## Goal

Record the feature in the branch changelog and update developer/example docs.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` for the style docs that enumerate `PointStyle` fields, so the new
> `screen_space` field is documented.  No architecture change is expected.

## Files

- Edit: `docs/changelog/2026/09/DD_<branch-name>.md` (branch changelog)
- Edit: docs listing `PointStyle` fields (if any)

## Steps

- [x] **5.1 — changelog entry**
  - Append a `## New Features` bullet for screen-space point markers, following
    `dev/workflows/changelog.md`.
- [x] **5.2 — docs**
  - Document `screen_space` on `PointStyle` in the style docs if they enumerate
    its fields.

## Validation

```
uv run pytest -q
uv run ruff check .
uv run python tools/build-viewer-js.py --check
uv run python tools/generate-example-docs.py --check
```

## Notes

- The changelog filename is finalized/renamed at PR time (see
  `dev/workflows/pull-request.md`).
