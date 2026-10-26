# Changes since version 2.25.0

## Bug Fixes
- **Tiled-pyramid LOD oscillation** — the pyramid level no longer thrashes
  between two resolutions: level re-resolution is debounced on a stable view and
  uses a wider hysteresis dead-band, and re-pushing an unchanged tiled
  background keeps its resolved level instead of resetting it.
- **Tiled level fetch storm** — fetching a full pyramid level now requests tiles
  in small batches, so a large level-0 fetch completes instead of aborting under
  load.
