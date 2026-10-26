# Changes since version 2.25.0 (2.25.1-rc1)

## Bug Fixes
- **Tiled-pyramid level-0 startup load** — the frontend no longer falls back to
  the full-resolution level while the viewport is still initializing: a
  non-finite on-screen size now skips LOD re-resolution (and is guarded in the
  initial level pick) instead of selecting level 0.
