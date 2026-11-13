# Changes since version 2.26.1 (2.27.0-rc3)

## New Features
- **`InteractionConfig.hit_priority`** — new pick-precedence field (always
  serialized, default `0`) so an app can make one interactive entity win over a
  coplanar neighbour instead of relying on raycast distance.

## Bug Fixes
- **Control points beat the bodies they edit** — `ActPoint` now defaults to
  `hit_priority=10` and pick ties break toward screen-space markers, so
  dragging a handle on a `PointPath`, polygon or line no longer grabs the body
  underneath, while an unowned gesture (e.g. a modifier the handle does not
  declare) still falls through to that body.
- **Icon points keep their transparency** — style/selection updates and hover
  no longer clear `transparent`/`depthWrite` on a glyph-textured point, so
  `IconPointStyle` markers stay cut-out instead of turning into filled squares.
