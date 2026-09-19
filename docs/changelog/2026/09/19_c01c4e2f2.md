# Changes since version 2.8.1

## New Features

- **2D overlay coordinate system** — `CoordinateSystem(display_mode="overlay")`
  draws the coordinate axes as a fixed screen-space overlay frame at the image
  borders and the background grid as a scene-level underlay behind the data,
  with tick values + grid lines updating live as the data pans/zooms.  Works in
  the live viewer and in standalone HTML export (including the CDN viewer
  bundle).

- **Configurable pan/zoom limits and tick subdivision** — `CoordinateSystem`
  now accepts `pan_xlim`/`pan_ylim` (pan bounds, defaulting to `xlim`/`ylim`),
  `min_zoom`/`max_zoom` (zoom range, `max_zoom` auto-derived from the finest
  interval), `x_intervals`/`y_intervals` (allowed tick step values in absolute
  data units, auto-generated from 1/2/5 steps when omitted), and
  `min_tick_spacing_px` (minimum pixel spacing between ticks, from which the
  overlay tick count is derived per axis from the live viewport).
