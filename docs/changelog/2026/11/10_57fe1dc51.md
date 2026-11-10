# Changes since version 2.25.1 (2.26.0-rc1)

## Bug Fixes
- **Exported animations no longer rebuild unchanged entities** — the animated
  bootstrap skips any entity whose source frame object is identical to the one
  already applied, so static geometry, labels and axes stop being disposed and
  recreated on every frame.
- **`PointPath` updates in place** — a changing path rewrites its fat-segment
  positions/colours instead of reallocating the mesh, keeping long traces cheap
  to animate in exported HTML and the live viewer alike.
- **Axes and grids update in place** — `Axis`, `Axes2D`, `Axes3D` and `Grid`
  refill their existing group (or rewrite their segment positions) instead of
  rebuilding the entity, so changing tick labels no longer recreates the CSS2D
  label DOM every frame.
- **Frame application is serialized** — a new `frame-pump.js` allows one frame
  apply in flight and lets the newest target win, so fast playback or scrubbing
  can no longer interleave two reconciliations.

## Refactor
- **`update<Kind>` may rewrite geometry in place** — the documented renderer
  update contract now allows an updater to rebuild geometry and return `true`;
  `false` is reserved for a changing representation or a genuinely cheaper
  rebuild.
