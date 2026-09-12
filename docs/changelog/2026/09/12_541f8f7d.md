# Changes since version 2.2.0

## Bug Fixes

- **`display_snapshot()` / `display_row(mode="static")` no longer depend on a
  published CDN bundle** — the serverless inline display now defaults to
  `delivery="inline"`, which inlines the Tanga viewer library from the local
  templates instead of loading `js/tanga-viewer.js` from jsDelivr at the current
  git ref.  Running from an unpublished branch previously produced a 404 and a
  "Failed to load the viewer" banner in the notebook.  File exports
  (`export_snapshot` / `export_figure`) keep the `"cdn"` default.

- **`HDirection(x, y, z)` construction** — `HDirection` can now be built from
  three components (matching `Direction` / `Point`), in addition to a
  `Direction` or a multivector; its multivector constructor now routes through
  `analyze_hdirection` instead of analyzing the blade as a plain direction.
- **`MV` / `Expression` operator return types** — arithmetic operators no
  longer advertise `NotImplementedType`, so the type checker no longer reports
  `^`, `|`, `*`, `+`, `-`, and `/` results as potentially `NotImplemented`;
  runtime reflected dispatch (`mv * variable`, etc.) is unchanged.
- **`AffineExpression` counting-axis reduction, broadcast, and linear solve** —
  a `DataArray`-introduced counting axis can now be reduced at the
  `AffineExpression` top level (terms that don't carry the axis broadcast as
  constants, scaled by the summed weights), and `.lstsq()` / `.svd()` /
  `.inv()` work whenever the sum reduces to a single linear map in one
  remaining variable.
