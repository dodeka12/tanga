# Viz hit precedence & icon alpha — Overview

**Created:** 2026-11-13 | **Status:** Done | **Branch:** `fix/hit-priority-icon-alpha`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
> Primary reference:
> [`docs/dev/architecture/viz-controls-and-interactions.md`](../../../docs/dev/architecture/viz-controls-and-interactions.md)
> (`## Interactive objects`, `### Active object handle controls`,
> `## Interaction surface`); renderer side:
> [`docs/dev/architecture/viz-architecture.md`](../../../docs/dev/architecture/viz-architecture.md).

## Goal

Two downstream bug reports, one release:

1. **Active handles lose to the body they control.** Clicking/dragging an
   `ActPoint` control handle that sits on a `PointPath` (or any coplanar body)
   sometimes grabs the path instead.  Picking currently has *no* priority: the
   frontend takes the first raycast hit, and screen-space markers are rendered
   on top (`polygonOffset` + `renderOrder`) but picked by raw distance, which
   ties them with the coplanar body.
2. **Icon points / point paths lose their transparency.** Any style or
   selection update (`viz.update(id, color=…)`) runs `applyOpacityUpdate` with
   the canonical `opacity: 1.0`, which clears `material.transparent` and
   re-enables `depthWrite` on a material whose alpha comes from a canvas glyph
   texture — the icon turns into an opaque quad.

Deliverables: an explicit, documented pick precedence driven by a new
`InteractionConfig.hit_priority`; `ActPoint` defaults to `10` (handles and bare
points) so they beat bodies; a `userData._alphaTexture` contract so texture
alpha survives every opacity writer (style updates *and* hover); tests, docs,
branch changelog, and the regenerated `js/tanga-viewer.js` bundle.

## Architecture (short)

- **Python model** — `InteractionConfig` (`_interaction.py`) gains
  `hit_priority: int = 0`.  `ActPoint` (`_active.py`) gains the kwarg
  `hit_priority: int = 10` and passes it into its `interaction_config`;
  composite handles inherit it for free (they are child `ActPoint`s spawned via
  `_spawn_handle`), composite bodies stay `0`.  `viz.set_interaction(id, …)`
  remains the per-entity escape hatch.
- **Frontend arbitration** — `_getInteractiveHits` (`templates/interaction.js`)
  still raycasts one mesh per entity, but now attaches `screenSpace` to each
  candidate and returns them ordered by a *pure* helper in
  `templates/hit-resolution.js`.  `resolveHitTarget` is unchanged: it still
  skips candidates whose triggers do not match, so a gesture a handle does not
  own falls through to the body underneath.
- **Alpha contract** — a material whose alpha comes from a texture tags itself
  `material.userData._alphaTexture = true`.  Every opacity writer derives
  `transparent`/`depthWrite` from `opacity < 1 || alphaTex` /
  `opacity >= 0.99 && !alphaTex`, exactly like the existing ShaderMaterial
  branch of `applyOpacityUpdate`.
- **Bundle** — `renderers/utils.js` and `renderers/icon_point.js` are listed in
  `_RENDERER_FILES` (`export/_bootstrap/_html.py`), so the committed
  `js/tanga-viewer.js` + manifest must be rebuilt.  `interaction.js` /
  `hit-resolution.js` are live-viewer ES modules and are **not** bundled.

### Fixed contract (do not change across phases)

1. **Wire format** — `InteractionConfig.to_dict()` always emits the field:

   ```json
   { "enabled": true, "triggers": [], "throttle_ms": 40, "hit_priority": 10 }
   ```

   Default `0`.  Purely additive and backward compatible: a frontend reading an
   older payload treats a missing field as `0`.

2. **Pick precedence** (frontend, highest first):

   1. `hit_priority` — descending;
   2. screen-space marker (`userData.isScreenSpace` on the intersected leaf)
      before a world-space body;
   3. `intersect.distance` — ascending;
   4. input (registration) order — deterministic tiebreak.

3. **JS helper API** (`templates/hit-resolution.js`):

   ```js
   hitPriority(config) -> number                       // missing/NaN => 0
   orderHitCandidates(candidates, getConfig) -> candidates
   // candidate = { objectId, intersect: { distance }, screenSpace: boolean }
   ```

4. **Alpha rule** — for any opacity writer:
   `transparent = opacity < 1 || alphaTexture`;
   `depthWrite = opacity >= 0.99 && !alphaTexture`.

## Decisions (confirmed)

- **Strict priority**, no depth tolerance: a hit handle wins wherever it is hit.
  Gestures it does not own still fall through (already handled by
  `resolveHitTarget`).
- **`hit_priority` defaults to `10` on *every* `ActPoint`** (handles and bare
  points), not only composite handles.
- **Screen-space marker tier is kept** on top of explicit priority: it makes
  picking agree with `polygonOffset`/`renderOrder` and fixes app-defined
  screen-space icons that are not library `ActPoint`s.  An explicit
  `hit_priority` still outranks it (priority is the primary key).
- **Both alpha paths fixed**: style/selection updates (`applyOpacityUpdate`) and
  hover (`_applyHover`).
- New branch + branch changelog; the `docs/changelog/index.md` entry is added at
  PR finalization, not now (see `dev/workflows/changelog.md`).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-interaction-config-hit-priority.md](./01-interaction-config-hit-priority.md) | `InteractionConfig.hit_priority` + `ActPoint(hit_priority=10)` + Python tests |
| 2 | [02-frontend-hit-precedence.md](./02-frontend-hit-precedence.md) | `hitPriority`/`orderHitCandidates` in `hit-resolution.js`, wired into `_getInteractiveHits`, `node --test` coverage |
| 3 | [03-icon-alpha-preservation.md](./03-icon-alpha-preservation.md) | `_alphaTexture` tag + `applyOpacityUpdate` + `_applyHover`, structural tests, bundle rebuild |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Architecture + user docs, branch changelog, full validation sweep |

## Testing as you go

```bash
uv run pytest py/tests/viz/test_interaction_config.py py/tests/viz/test_active.py -q   # phase 1
node --test js/dev/tests/hit-resolution.test.mjs && node js/dev/tests/check-syntax.mjs # phase 2
uv run pytest py/tests/viz/test_icon_point_alpha.py py/tests/viz/test_export_renderers.py -q
uv run python tools/build-viewer-js.py --force && uv run python tools/build-viewer-js.py --check # phase 3
uv run pytest py/tests/viz -q
uv run ruff check . && uv run ty check
uv run mkdocs build --strict                                                          # phase 4
```

## Non-goals

- No tolerance/depth-based arbitration, no screen-space epsilon heuristic.
- No `hit_priority` kwarg on `ActiveObject`/composites (use
  `viz.set_interaction`); only `ActPoint` opts in with `10`.
- No change to `LineSegments2`/`LineMaterial` raycast distances and no
  normalized-distance comparator.
- No new picking algorithm (BVH/GPU picking) and no change to the
  "background planes last" mesh sort beyond leaving it as the final tiebreak.
- No alpha rework for other textured renderers (image planes and surfaces keep
  their own `uOpacity`/`_alphaTexture` paths).
- No `_alphaTexture` handling in `_resetHover` (it already restores the saved
  `transparent`/`depthWrite`).
