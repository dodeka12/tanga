# Changes since version 2.25.0 (2.25.1-rc2)

## Bug Fixes
- **Tiled-pyramid initial level** — the background image now picks its initial
  pyramid level from the actual pane size instead of a hardcoded 2048 budget, so
  a large image no longer loads the full-resolution level on startup.
