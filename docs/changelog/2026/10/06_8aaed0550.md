# Changes since version 2.16.1

## New Features
- **Unified `ActiveObject` handle API** — `_ActWithHandles` is now the public
  `ActiveObject` base, and `ActPoint` is a subclass of it; every active object
  (a bare point and each composite) exposes `set_handles_enabled(enabled)`,
  `set_handles_visible(visible)`, and `set_drag_modifiers(*modifiers)` so a host
  can gate editing uniformly without duck-typing.
- **Active-point content vs handle styling** — a bare `ActPoint` now takes a
  `handle_style` (the active/draggable control-point appearance, e.g. a square
  marker) and a `style` (the content `Point` appearance, e.g. a round marker);
  `set_handles_enabled` swaps between them, keeping the point visible but inert
  when disabled.
- **New shapes are selected on creation** — a drag-drawn or click-placed shape
  becomes the active selection as soon as it is created, so it is highlighted
  and ready to edit without an extra click.

## Bug Fixes
- **Right-button panning no longer blocked by a draw mode** — navigation now
  yields to an interaction surface only for the button+modifier combinations it
  registers (`InteractionController.surfaceClaimsPointer`), so a left-only draw
  binding leaves right-button panning free.
- **Selection highlight no longer sticks** — deselecting now restores an
  explicit color instead of a `None` color (which `to_dict()`/the frontend
  drop), so selecting a second shape clears the first.
- **Click no longer creates a degenerate shape** — drag-to-create now discards a
  press+release with negligible movement, and a non-finite world delta is
  dropped, so a click with the line tool can't produce a "very long line".
- **Rotate handle keeps a fixed screen-space offset** — the rotate handle sits a
  constant screen distance from the shape edge rather than a size-proportional
  distance, so it no longer drifts far from small shapes.
- **Rotate handle appears correctly when a shape is created** — the calibrated
  pixel scale is applied before handles are spawned, so a freshly drawn ellipse
  shows its rotate handle at the right distance instead of only after a nudge.
