# Changes since version 2.4.0

## Bug Fixes
- **Left-mouse 3D view rotation silently stopped working** — `configureControls`
  mapped mouse buttons with `ACTION[...] || null`, and because
  `THREE.MOUSE.ROTATE` is `0` (falsy), the left button was coerced to `null`
  (disabled) in every 3D scene; it now uses `?? null` so `0` is preserved and
  left-drag orbits again.
