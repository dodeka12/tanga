# Phase 5 — Docs, changelog, PR

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Document the new API and the `ui_options` message, record the architecture
changes, add the branch changelog, and prepare the PR.

## Files

- Edit: `docs/py/viz/ui/controls.md`
- Edit: `docs/py/viz/ui/control-views.md`
- Edit: `docs/py/viz/ui/menus.md`
- Edit: `docs/py/viz/ui/runtime-updates.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/changelog/2026/11/09_feat-tooltips.md`

## Steps

- [x] **5.1 — User docs**
  - `controls.md`: a “Tooltips” subsection covering `tooltip=` at construction,
    `ControlView.set_tooltip(text)` / `Visualizer.set_control_tooltip(id, text)`
    (empty string clears, no layout re-push), the icon-only `aria-label`
    behaviour, and `GroupView.set_tooltip` + `GroupUI(tooltip=…)`.
  - `control-views.md`: add `set_tooltip` to the shared method table/list next
    to `set_enabled` / `set_visible`.
  - `menus.md`: document `MenuView(tooltip=…)` (static; rebuilt on re-push).
  - `runtime-updates.md`: document the `tooltip` field on `control_state`, the
    new `ui_options` message, and
    `Visualizer.set_tooltips_enabled(bool)` / `tooltips_enabled` (including that
    only framework-set tooltips are switched).

- [x] **5.2 — Architecture docs**
  - `viz-controls-and-interactions.md`: the single `applyTooltip` helper +
    `data-tanga-tooltip` bookkeeping and why the switch lives client-side.
  - `viz-architecture.md`: mention `UIOptionsHost` among the feature hosts and
    the `ui_options` server → client message (sent in `_push_full_state`).

- [x] **5.3 — Branch changelog**
  - Follow `dev/workflows/changelog.md`: create
    `docs/changelog/2026/11/09_feat-tooltips.md` (branch name with `/` → `-`),
    title from `uv run python tools/last-release.py`, sections Feat/Docs/API as
    applicable.

- [x] **5.4 — PR prep**
  - Follow `dev/workflows/pull-request.md` (squash → rename changelog to
    `DD_<hash>.md` → PR body from the changelog).
  - Done: branch squashed to `e6c7c3cd7`, changelog renamed to
    `docs/changelog/2026/11/09_e6c7c3cd7.md`, `docs/changelog/index.md` entry
    added.

## Validation

```bash
uv run mkdocs build --strict && uv run python tools/build-viewer-js.py --check
```

## Notes

- `mkdocs build --strict` fails on broken nav entries — re-run
  `tools/generate-example-docs.py` first if phase 4 added a page.
- Changelog screenshots are not needed; the example is the demo.
