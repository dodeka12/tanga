# Changes since version 1.10.0

## Bug Fixes
- **HTML export drops KaTeX math texture labels** — standalone HTML snapshots
  and figures did not load `html2canvas`, so `$...$` / `$$...$$` texture labels
  silently failed to render (plain-text labels still worked). The export
  templates now load `html2canvas` alongside KaTeX, and `createTextureLabel()`
  falls back to plain text when `html2canvas` is unavailable instead of
  dropping the label.

## Refactor
- **Default 3D camera moved closer to the origin** — the default perspective
  camera position changed from `(8, 6, 10)` to `(6, 4.5, 7.5)` (three-quarters
  of the original distance), applied to both the live viewer and HTML exports.
- **Standalone HTML export no longer auto-fits the camera** — removed the
  bounding-box auto-fit from `export_snapshot` so the standalone export shows
  the same initial camera as the live viewer (which only fits on an explicit
  `flush(fit_camera=True)`), instead of pushing the scene back out.
