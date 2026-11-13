# Changes since version 2.27.0 (2.28.0-rc1)

## Bug Fixes

- **PointPath segment colours clear in the browser** — clearing the last
  explicit segment colour now resets the path to its uniform colour.  Previously
  the stale coloured segment stayed on screen because the cleared content update
  omitted `segmentColors` and the frontend merge kept the old list.
