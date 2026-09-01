# Phase 6 — Object interactions onto the unified dispatcher

## Goal

Route `interaction:*` through the same registry/dispatcher as controls, keeping
the per-pane `InteractionController` capture/throttle transport and the
drag-move coalescing.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_interaction.py`
- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/templates/interaction.js`, `viewer.js`, `three-view.js`
- Edit: tests

## Steps

- [x] **6.1 — Register interaction handlers on the shared registry**
  - `on_interaction(object_id, event_type, handler)` registers
    `(object_id, event_type.value)` on the unified registry (replacing
    `InteractionHandlerRegistry`).

- [x] **6.2 — Dispatch interactions through `_dispatch_event`**
  > Interaction handlers take a single `event` arg (vs. control handlers'
  > `(value, event)`), so dispatch stays in `InteractionHandlerRegistry.dispatch`
  > (which now reads handlers from the shared `(id, event)` registry via
  > delegation) rather than the two-arg `Visualizer._dispatch_event`.
  - `_dispatch_interaction_event` parses the payload and calls
    `_dispatch_event(object_id, event_type, scene, data)` with a per-event
    **coalescing policy** (`drag_move` coalesces to latest; others run).

- [x] **6.3 — Keep coalescing**
  - Port `InteractionHandlerRegistry.dispatch` drag-move coalescing into the
    policy layer; keep `_send_drag_anchor` as an `event_reply` back-channel.

- [x] **6.4 — Frontend**
  > No frontend change needed — the wire envelope is unchanged (see deferred 4.3);
  > `interaction.js` keeps sending `interaction:*` and capture is untouched.
  - `interaction.js` keeps sending `interaction:*` (alias of the envelope); no
    capture changes. `three-view.js` handles `event_reply`.

- [x] **6.5 — Tests**
  - `test_interaction_registry.py` / `test_interaction_config.py` migrate to the
    unified registry; add coalescing-policy coverage.

## Validation

`uv run pytest py/tests/viz/ -q`
