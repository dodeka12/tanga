# Unified controls, layouts, scenes & interactions — Overview

**Created:** 2026-08-31 | **Status:** In progress | **Branch:** `fix/file-chooser-bug`

## Goal

Replace the three parallel, hand-wired interaction mechanisms in `pytanga.viz`
(panel controls, layout `ControlView`s, and object `interaction:*`) with one
unified model: **one control model, one id namespace, one event→handler
registry, one dispatcher**. This removes the seams that produced the
`FileChooserView` select-path bug, the `controls_define` registry-reset bug, and
the duplicated value/interaction plumbing.

## Architecture (short)

Three orthogonal concerns, clearly separated:

- **Scene** — a world of entities (incl. interactive objects) + camera + scene
  chrome.
- **Layout** — a tree arranging *scene panes* (`SceneView`) and *widgets*
  (`ControlView`) in split/stack/overlay views (global, one per page).
- **Control** — one model `id + kind + value + handlers`, *placed* in a panel,
  attached to a 3D object, in a layout pane, or in a banner.
- **Interaction** — a sibling of `Control` under the same event model; differs
  only in payload richness and frequency (coalescing).

### Fixed contract (decided up front)

1. **Single global id namespace.** Every control and interactive object has a
   globally unique `id` (the existing de-facto contract, now enforced). `scene`
   is a routing hint, not part of the storage key.
2. **Unified event envelope (client → server):**
   `{ "type": "event", "target": "<id>", "event": "<name>", "scene": "<name|\"\">", "data": {…} }`.
   The legacy `control:*` / `interaction:*` prefixes are accepted aliases during
   migration; they route through the same dispatcher.
3. **Registry key `(target_id, event_name)`.** Replaces the bare-id
   `ControlHandlerRegistry` and the magic `__row_add__`/`__press__`/`__group__`
   keys.
4. **Dispatch policy per event.** `change/click/…` run normally; `drag_move`
   coalesces to the latest (existing server-side coalescing is generalized).
   `interaction:drag_anchor` becomes an `event_reply`.
5. **Value update stays `control_update`** `{ type, scene, id, value }` applied
   by id regardless of placement; the frontend applies it to the single
   (owner-tagged) registry.

## Decisions (confirmed)

- Fold the two tactical fixes (select-path write-back + panel push; registry
  reset) in as Phases 1–2 rather than landing them separately. This supersedes
  `dev/todos/viz-file-chooser-path-fix.md`.
- Keep the `view_layout` wire shape stable through the `ControlView`→`Control`
  merge (Phase 5): the node `type`/`kind` fields do not change; only the Python
  model and serializer *source* of those fields do.
- Interactions keep their own per-pane capture/transport (Phase 6) but share the
  dispatcher/registry; they are not moved onto the `control:*` prefix.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-unified-control-resolution.md](./01-unified-control-resolution.md) | Backend `resolve(id)` + universal `set/get` value APIs; fix select-path, navigate-root, panel push. |
| 2 | [02-frontend-scoped-registry.md](./02-frontend-scoped-registry.md) | Owner-tagged frontend registry; scoped `_destroyAll`; fixes registry-reset. |
| 3 | [03-event-keyed-handler-registry.md](./03-event-keyed-handler-registry.md) | `(id, event)` registry; drop magic keys; dispatch by event. |
| 4 | [04-unified-event-dispatcher.md](./04-unified-event-dispatcher.md) | One `event` envelope + dispatcher; fold banner/editor/file-browser. |
| 5 | [05-control-view-embeds-control.md](./05-control-view-embeds-control.md) | `ControlView` wraps `Control`; single serializer & value API. |
| 6 | [06-interactions-on-unified-dispatcher.md](./06-interactions-on-unified-dispatcher.md) | `interaction:*` onto the unified dispatcher with coalescing policy. |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Docs + changelog + full validation. |

## Testing as you go

- Python: `uv run pytest py/tests/viz/ -q`
- Frontend unit: `node --test dev/src/js-tests/*.test.mjs`
- Frontend smoke: open `dev/src/js-tests/*-smoke.html` in a browser (manual)
- Docs: `uv run mkdocs build --strict` (final phase)

## Non-goals

- No standalone-export (`export_snapshot` / glTF) changes; exports stay
  single-scene.
- No change to the per-pane `InteractionController` capture/throttle internals.
- No removal of the downstream `seating-plan` workaround in this plan.
