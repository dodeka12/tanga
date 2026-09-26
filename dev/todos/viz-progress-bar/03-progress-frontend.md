# Phase 3 — ProgressBar frontend (JS)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add the JS DOM factory and view, and dispatch the `progress_bar_view` node type
in `build.js`.

## Files

- New: `py/pytanga/viz/templates/controls/progress-bar.js`
- New: `py/pytanga/viz/templates/views/progress-bar-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`

## Steps

- [x] **3.1 — DOM factory (`controls/progress-bar.js`)**
  - `createProgressBar(ctrl)` builds `.tanga-control.tanga-progress` with
    `.tanga-progress-title`, `.tanga-progress-track` > `.tanga-progress-fill`,
    `.tanga-progress-value` (percent, determinate), and `.tanga-progress-text`.
  - Toggle `.tanga-progress-indeterminate` on the track per
    `indeterminate || !(total > 0)`; hide empty title/text.
  - `registerControl` with `apply(payload)` updating title/value/total/
    indeterminate/text and clamping the fill width to 0–100%; `applyTooltip` +
    `applyControlStateToElement`.

- [x] **3.2 — JS view (`views/progress-bar-view.js`)**
  - `class ProgressBarView extends ControlView` with `constructor`,
    `update(node)` (all five fields), and `render()` → `createProgressBar(...)`.

- [x] **3.3 — Dispatch (`build.js`)**
  - Import `ProgressBarView`; add a `node.type === 'progress_bar_view'` branch
    with the `existing.update(node)` reuse pattern (mirror `slider_view`).

## Validation

```bash
node js/dev/tests/check-syntax.mjs
uv run python -c "from pytanga.viz import ProgressBarView; print(ProgressBarView('p', title='T', total=10)._serialize())"
```

## Notes

- The factory `kind` is `"progress"`; the JS view class is `ProgressBarView` to
  match the Python class (node type `progress_bar_view`).
