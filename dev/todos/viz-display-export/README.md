# Viz Display & Export Consolidation — Overview

**Created:** 2026-08-18 | **Status:** Planned

## Target

Fix the `display_static()` Jupyter crash and consolidate the visualizer's
display / export / serving surface into one coherent verb×noun model.

Two concerns become explicit:

- **Describe** the scene (`Visualizer`, `viz.add`, `viz.scene(name)`) — no
  server, no network.
- **Serve / view / export** it — an explicit action.

New surface:

- **Live serve/view:** `show()`, `wait()`, `open_browser()`,
  `start_server()`/`stop_server()`, `animate()`.
- **Static snapshot (serverless):** `export_snapshot()`, `open_snapshot()`,
  `display_snapshot()`.
- **Figure (sized embed snippet) + glTF:** `export_figure()`, `export_glb()`.
- **Recording:** `start_animation_recording()` → `AnimationRecording`,
  consumed via `export_snapshot(..., animation=rec)` /
  `export_figure(..., animation=rec)`.

All old names remain as `DeprecationWarning` aliases so existing code keeps
running.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-fix-display-static.md](./01-fix-display-static.md) | Fix `display_static` inline rendering via `<iframe srcdoc>` |
| 2 | [02-serve-primitives.md](./02-serve-primitives.md) | `start_server`/`stop_server`/`open_browser`; move `host`/`port` out of the constructor |
| 3 | [03-show-wait.md](./03-show-wait.md) | `show()` = serve+open; `wait()` blocks until Ctrl+C |
| 4 | [04-snapshot-family.md](./04-snapshot-family.md) | `export_snapshot`/`open_snapshot`/`display_snapshot`/`render_snapshot` |
| 5 | [05-figure-glb-export.md](./05-figure-glb-export.md) | `export_figure(path=None)`, `export_glb`, `render_figure`, `build_glb` |
| 6 | [06-animation-export.md](./06-animation-export.md) | `animation=` keyword; move recording factory to `Visualizer`/handle |
| 7 | [07-display-row.md](./07-display-row.md) | `display()` on `Visualizer`+handle; `display_row` mixes live + static |
| 8 | [08-scene-exporter-aliases.md](./08-scene-exporter-aliases.md) | Demote `SceneExporter` to a deprecated alias wrapper |
| 9 | [09-migrate-callsites.md](./09-migrate-callsites.md) | Migrate tests/examples/dev scripts to new names |
| 10 | [10-docs.md](./10-docs.md) | Update docs |
| 11 | [11-changelog.md](./11-changelog.md) | Changelog entry per `dev/workflows/changelog.md` |

## Guiding decisions

- **"snapshot"** is the noun for the static, full-page, serverless HTML view of
  the current scene state. It avoids colliding with the existing `Scene` /
  `viz.scene(name)` data concept. **"figure"** is reserved for the sized,
  embeddable presentation snippet; **"glb"** for the glTF binary.
- **Serving is Visualizer-level** (one server, many scenes):
  `start_server`/`stop_server`/`wait` live on `Visualizer`.
- **Scene-level operations** (`show`, `open_browser`, `display`,
  `display_snapshot`, `export_snapshot`, `export_figure`, `export_glb`,
  `start_animation_recording`) live on both `Visualizer` (main scene) and
  `VizSceneHandle` (per scene), delegating with the scene name/path.
- **Every rename ships with a deprecated alias in the same step** (using
  `warnings.warn(..., DeprecationWarning, stacklevel=2)`), so existing code
  never breaks mid-refactor.
- **`AnimationRecording` is unchanged** — it is the frame store. Only its
  factory moves from `SceneExporter` to `Visualizer`/`VizSceneHandle`.
- **Recording and export are serverless**; `show()`/`animate()` are only needed
  to also watch the live view while recording.
