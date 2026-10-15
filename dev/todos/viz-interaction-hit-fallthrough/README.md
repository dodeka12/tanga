# Trigger-aware interaction hit resolution — Overview

**Created:** 2026-10-15 | **Status:** Done | **Branch:** `feat/bg-image-shader`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> — the "Interaction surface" section — and `viz-architecture.md`).  This work
> **changes** the documented surface behavior ("fires on empty space" → "fires on
> empty space *or* when nearer entities decline the gesture"), so the developer
> docs are updated in Phase 2.

## Goal

Route pointer gestures to the **nearest hit object that has a matching trigger**,
falling through to the pane's interaction surface (the furthest/background
candidate) when nearer entities decline — and fix trigger matching so a trigger
with no `modifiers` requires *no* modifiers held (not "any modifier").  Together
these make ctrl+left-drag brightness/contrast work over a label entity: the
label's plain drag trigger no longer matches ctrl, so the drag falls through to
the surface.

## Architecture (short)

- **Frontend only** — `py/pytanga/viz/templates/interaction.js` plus a new pure
  helper module `py/pytanga/viz/templates/hit-resolution.js`.
- `raycaster.intersectObjects` already returns hits nearest→furthest, and
  `_findMatchingTriggers` already answers "is this event registered for this
  object?" — the missing piece is walking that sorted list instead of returning
  only the nearest entity and treating the surface as an exclusive fallback.
- `_findMatchingTriggers` had a latent bug: a trigger with no `modifiers` matched
  *any* modifier.  The shared `matchTriggers` now matches modifiers **exactly**
  (empty = no modifiers held).
- Hover is unchanged (it uses `_getInteractiveHit` directly, nearest entity,
  no trigger matching).
- Backend, wire protocol, trigger config, and per-object drag/click/scroll state
  are all unchanged.

## Decisions (confirmed)

- The trigger-aware nearest→furthest resolution applies to **all four** `_getHit`
  gesture events: **drag** (pointerdown), **click** (pointerup), **dblclick**,
  and **scroll** (wheel).
- The **surface is the furthest/background candidate** — checked last, regardless
  of ray↔plane distance, so it only receives a gesture no nearer entity claims.
- Preserve the existing **image-plane-last mesh sort** (the `z = 0` tie-break so
  shape bodies win over the image plane).
- **Click detection stays consistent** — record `_clickState` keyed by the
  *click*-resolution target at pointerdown, and re-resolve the *click* target at
  pointerup.  Drag resolution and click resolution are independent.
- Extract `matchTriggers` + `resolveHitTarget` as pure, DOM-free functions in a
  new module, unit-tested with `node --test` (repo convention: pure logic out of
  DOM/WebGL modules).
- **Exact modifier match** — `matchTriggers` requires the held modifiers to match
  a trigger's `modifiers` exactly; a trigger without `modifiers` fires only when
  no modifiers are held.
- No backend or wire-protocol change; the `object_id` chosen at pointerdown flows
  through the existing drag pipeline unchanged.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-trigger-aware-hit-resolution.md](./01-trigger-aware-hit-resolution.md) | Pure helpers + rewire the four gesture sites + unit test + rebuild bundle |
| 2 | [02-docs-changelog.md](./02-docs-changelog.md) | Developer docs + `_surface.py` docstring + changelog |

## Testing as you go

- `node --test js/dev/tests/*.test.mjs` (new resolver unit tests + existing)
- `node js/dev/tests/check-syntax.mjs` (syntax gate)
- `uv run python tools/build-viewer-js.py && uv run python tools/build-viewer-js.py --check` (bundle)
- `uv run mkdocs build --strict` (phase 2)
- Manual smoke: `uv run python py/examples/apps/calibrated_labeling_app.py` —
  ctrl+drag over a label entity now adjusts brightness/contrast; a plain click on
  a label still selects it; drawing still works.

## Non-goals

- No unified "hit registry" — the surface stays a separate per-pane field; only
  the resolution *order* changes.
- No change to hover behavior.
- No backend, wire-protocol, or trigger-config-model change.
