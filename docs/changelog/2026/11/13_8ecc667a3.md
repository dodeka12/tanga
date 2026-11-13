# Changes since version 2.27.0 (2.28.0-rc2)

## Bug Fixes

- **PointPath segment colours clear in the browser** — a cleared path now
  serializes `segmentColors` as an empty list instead of omitting the key, so
  the frontend content merge can't inherit the stale, previously-coloured list.
  Clearing the last explicit segment colour reverts the path to its uniform
  colour.
