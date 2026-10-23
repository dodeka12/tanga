# viz-view-visibility — Overview

**Created:** 2026-10-20 | **Status:** Done | **Branch:** feat/info

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make per-pane entity visibility a runtime concern, and let callers declare at
add time which views an entity should be constructed in — so large entities such
as `DepthImage` are never built in panes that will never show them.

Deliverables:
- Remove the static `SceneView(hide=…, show=…)` constructor filter.
- `SceneView.set_visible(entity_id, visible)` — per-pane, runtime, granular.
- `Scene.set_visible(object_id, visible)` — global (already exists).
- `visible_in=` kwarg on the scene add path — static per-view scope, default all
  views.

## Architecture (short)

Three independent visibility conditions compose per pane `V` for entity `E`:

| Mechanism | Source | Build | Visible |
|-----------|--------|-------|---------|
| `visible_in` scope | entity field (add time) | don't build when `V` not in scope | — |
| global `visible` | entity `visible` flag | always build (in scope) | `E.visible !== false` |
| per-view toggle | `SceneView._hide` (runtime) | always build (in scope) | `!V._hide.has(E.id)` |

Frontend composition:
`entry.obj.visible = (entry.data.visible !== false) && !this._hide.has(id)`.

## Decisions (confirmed)

- Use `visible_in` (whitelist; `None`/empty = all views). No `views=` alias.
- Only `set_visible()` on `SceneView` and `Scene`; no `hide`/`show`/`show_entity`
  methods (`VizSceneHandle.show` stays reserved for serve/displays).
- Remove `SceneView(hide=…, show=…)` entirely (breaking change; call sites updated).
- Runtime `SceneView.set_visible` = build-but-toggle (fast, reversible); static
  `visible_in` = don't-build (avoids constructing large entities).

## Wire contract (fixed)

- `view_visibility` message (idempotent, full state):
  `{"type": "view_visibility", "view_id": "<SceneView.id>", "hide": ["<entity_id>", …]}`
  (`hide` sorted; no `show`).
- Entity full content gains `"visible_in": ["<view_id>", …]` when non-empty.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-scene-view-set-visible.md](./01-scene-view-set-visible.md) | `SceneView.set_visible` model + remove static filter + migrate callers |
| 2 | [02-server-view-visibility-message.md](./02-server-view-visibility-message.md) | inject push callback; send `view_visibility` |
| 3 | [03-visible-in-scope.md](./03-visible-in-scope.md) | `visible_in` kwarg + serialization |
| 4 | [04-frontend-dispatch-and-composition.md](./04-frontend-dispatch-and-composition.md) | dispatch + build gate + visibility composition |
| 5 | [05-integration-tests-and-full-gate.md](./05-integration-tests-and-full-gate.md) | integration coverage + full validation gate |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | developer docs + example docs + changelog |

## Testing as you go

- Python: `uv run pytest py/tests/viz -q` (phase-scoped subsets listed per phase)
- JS: `node --test 'js/dev/tests/*.test.mjs'` and `node js/dev/tests/check-syntax.mjs`
- Bundle drift: `uv run python tools/build-viewer-js.py --check` (expect unchanged)
- Docs: `uv run python tools/generate-example-docs.py --check` and
  `uv run mkdocs build --strict`

## Non-goals

- No `SceneView.add(entity, …)` view-centric add (deferred; `visible_in` covers it).
- No runtime mutation of `visible_in` (re-add to change scope).
- No change to the export/CDN bundle (`js/tanga-viewer.js`); live viewer only.
