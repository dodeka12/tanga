# Changes since version 2.23.2

## New Features

- **Interactive shapes use the plane's pixel basis** — `ActRectangle2D`,
  `ActEllipse`, and `ActCircle` accept an explicit in-plane basis
  (`dir_u`/`dir_v`, validated orthonormal + right-handed) and expose it
  read-only.  `Act*.from_entity` and `LabelMeStore.to_act` provide one correct
  way to wrap an entity in an act without losing its frame.

- **`axis_directions()` on planar entities** — `Rectangle2D.axis_directions()`
  and `Ellipse.axis_directions()` return the effective in-plane axes
  (`dir_u`/`dir_v` rotated by `angle`), so code that reads `dir_u` alone no
  longer gets the wrong orientation.

## Bug Fixes

- **Labelme ellipse `angle` is in the pixel frame** — `LabelMeStore` writes the
  ellipse `angle` relative to image horizontal (previously the act's frame), and
  the ellipse axis fallback uses `_plane_basis(normal)`, so `load → Act → save`
  is pixel-exact on a rolled, tilted camera.
