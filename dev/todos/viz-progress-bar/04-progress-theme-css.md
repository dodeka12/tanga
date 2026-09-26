# Phase 4 — ProgressBar theme CSS

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add the themed component sheet and register it, keeping the theme drift guard
green.

## Files

- New: `py/pytanga/viz/templates/themes/controls/progress-bar.css`
- Edit: `py/pytanga/viz/templates/themes/registry.json`
- Edit: `py/tests/viz/test_themes.py`

## Steps

- [x] **4.1 — Component sheet (`controls/progress-bar.css`)**
  - Style `.tanga-progress-track` (`var(--tanga-input-bg)`,
    `var(--tanga-border-strong)`), `.tanga-progress-fill`
    (`var(--tanga-accent)`), `.tanga-progress-title`
    (`var(--tanga-fg-strong)`), `.tanga-progress-text`
    (`var(--tanga-fg-muted)`), `.tanga-progress-value`
    (`var(--tanga-accent-soft)`).
  - Add `@keyframes tanga-progress-indeterminate` +
    `.tanga-progress-indeterminate` fill animation.  No inline appearance (see
    `docs/dev/architecture/viz-theme-system.md`).

- [x] **4.2 — Register (`registry.json`)**
  - Add `"controls/progress-bar.css"` to `components`.

- [x] **4.3 — Theme test (`test_themes.py`)**
  - Add `"controls/progress-bar.css"` to `_COMPONENTS` at the same position.

## Validation

```bash
uv run pytest py/tests/viz/test_themes.py -q
```
