# Viz keyboard shortcuts (sketch)

**Created:** 2026-09-14 | **Status:** Planned | **Branch:** `feat/image-view`

## Goal

Register keyboard-shortcut handlers **per scene**, so a backend callback fires
when the user presses a key while that scene has focus.  Use cases: toggle a
draw mode with ``R``, cancel with ``Esc``, switch tools with ``1..9``.

This is a **sketch** — not implemented, and not yet a step list.

## Sketch

### Frontend

- One global ``keydown`` listener per ``ThreeJsView`` pane (attached to the
  pane's DOM element so focus is implicit; mirror the per-pane
  ``InteractionController`` in ``templates/interaction.js``).
- The pane forwards only the keys its scene registered, over the established
  interaction path:
  ``{ type: "interaction:key", scene: "<name>", key: "<value>",
     modifiers: [...], browser_id }``.

### Backend

- ``InteractionConfig`` (or ``SceneConfig``) gains a ``keyboard`` field listing
  the registered shortcuts, so the frontend knows which keys to forward.
- ``Visualizer.on_key(scene_name, key, handler)`` / ``VizSceneHandle.on_key(...)``
  register an ``InteractionHandler`` under ``(key, "key")`` in the existing
  ``ControlHandlerRegistry`` — same ``(id, event)`` registry, routed by
  ``InteractionHost._dispatch_interaction_event`` like ``interaction:*`` today.
- Convenience on ``ImageCanvas``: ``on_key(key, handler)``.

### Open questions

- Focus model: per-pane focus (DOM element) vs scene-wide (any pane showing the
  scene)?
- Key matching: a bare key string, or a ``KeyChord(key, *modifiers)`` dataclass
  like ``DragBinding``?
- Do shortcuts need a visible hint (e.g. a ``⌘/Ctrl`` label in the toolbar
  tooltip)?

## Notes

- Until this lands, examples stay mouse-only (e.g. ``rectangle_labeling.py``
  toggles its draw mode via a toolbar button, not a key).
