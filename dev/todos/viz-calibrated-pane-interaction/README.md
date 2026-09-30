# Calibrated Pane Interaction — Overview

**Created:** 2026-09-30 | **Status:** Planned | **Branch:** `feat/calibrated-pane-interaction`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make the calibrated **background-image** pane behave like the 2D `ImageCanvas`
pane: a clear arm/disarm drawing mode (cursor + navigation yields), and the
`Act*` entities (shapes + screen-space handles) render correctly over the
background image so they can be created, selected, and edited — using the shared
`InteractionSurface` + `Act*` primitives, not calibrated-case workarounds.

## Architecture (short)

The `InteractionSurface` unified the *interaction plane* (drag/click on empty
space). The remaining divergence between the two modes is in two places, and
that is exactly where the symptoms live:

- **Navigation and interaction are two uncoordinated gesture systems.** The 2D
  canvas uses OrbitControls (the surface drag disables it via
  `controls.enabled = false`). The calibrated pane uses a *custom* viewport-crop
  pan (`_onViewportPointerDown/Move/Up` → `_panViewport`) that the interaction
  controller never disables, so a draw-drag also pans the background.
- **The calibrated pane renders entities differently.** The `Act*` shapes are in
  the shared 3D scene and render in the orbit pane, but not over the NDC
  background in the pinhole pane (a rendering bug to fix).

The fix is one **per-pane gesture arbitration**: a single "interaction armed /
active" signal that both OrbitControls *and* the viewport-crop pan respect.

## Contract (fixed)

`InteractionController` (frontend) gains two read-only predicates:

```js
hasArmedSurface()  // true when the pane's surface has an enabled drag/click trigger
isDragActive()     // true while an interaction drag (surface or entity) is in progress
```

The viewport-crop pan handlers skip panning when
`hasArmedSurface() || isDragActive()`.  This is the only new seam; both labelers
drive it through the existing `set_enabled` / `set_cursor` surface API.

## Decisions (confirmed)

- Keep `InteractionSurface` + `Act*` as the shared interaction primitives (no new
  interaction model).
- Navigation yields to interaction via a per-pane predicate — not by special-casing
  the calibrated pane.
- The `background_image` (NDC quad) stays the calibrated visual; the shapes are 3D
  entities at the mapper depth (inherent to a calibrated photo).
- Screen-space markers stay camera-agnostic: fix the off-center-pinhole scale
  rather than adding a calibrated special case.
- The drawing-mode cursor is the **scene** cursor for now (crosshair on both
  panes); a per-pane cursor is deferred (see non-goals).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-gesture-arbitration.md](./01-gesture-arbitration.md) | Per-pane "interaction armed/active" predicate + viewport pan yields |
| 2 | [02-mode-switch.md](./02-mode-switch.md) | Complete the drawing mode-switch (surface + cursor + navigation yield) |
| 3 | [03-pinhole-entity-rendering.md](./03-pinhole-entity-rendering.md) | Fix `Act*` rendering over the background in the pinhole pane |
| 4 | [04-screen-space-markers.md](./04-screen-space-markers.md) | Correct screen-space marker scale for the off-center pinhole |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q`
- `uv run ruff check .` + `uv run ty check`
- `node --test 'js/dev/tests/*.test.mjs'` + `node js/dev/tests/check-syntax.mjs`
- `uv run mkdocs build --strict` (phase 5)
- Manual browser smoke: `uv run python py/examples/apps/calibrated_labeling_app.py`

## Non-goals

- No new interaction model; `InteractionSurface` + `Act*` stay as-is.
- No per-pane cursor override (scene cursor is accepted; see decisions).
- No change to `ImageView` / the flat `ImageCanvas` (that path already works).
