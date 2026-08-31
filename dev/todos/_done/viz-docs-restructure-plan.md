# Viz docs restructure — implementation plan

**Created:** 2026-08-23 | **Branch:** `fix/viz` | **Status:** Done (Phases 0–9)

This is the implementation plan for the visualization docs restructure. It
supersedes the earlier analysis in `dev/todos/viz-docs-restructure.md` and
incorporates the decisions agreed with the maintainer.

## Goal

Restructure `docs/py/viz/` from a mostly-flat layout into six topic folders —
`scene-objects/`, `visualizer/`, `visualizerapp/`, `jupyter/`, `styles/`,
`export/` — add a compiled Jupyter notebook of entity visualizations, split the
VisualizerApp and Jupyter docs into focused pages, and rewire the `mkdocs.yml`
nav plus every cross-reference.

## Agreed decisions

1. **Folder names** — `scene-objects/` (entities), `visualizer/` (the
   `Visualizer` API), `styles/` (styling).
2. **`VisualizerApp` gets its own top-level folder** `visualizerapp/` next to
   `visualizer/`, and `interactive.md` is split into `controls.md` +
   `handlers.md` (it "deserves more docs").
3. **Jupyter docs get their own top-level folder** `jupyter/` next to
   `visualizer/` (not under the API).
4. **`point-path.md` lives under `scene-objects/`.**
5. **Entities get a compiled notebook** `scene-objects/entities.ipynb` — a
   per-entity style-parameter table plus embedded **static** HTML via
   `display_snapshot()`, compiled by `mkdocs-jupyter` with `execute: true`.
6. **Operators get a separate markdown page** `scene-objects/operators.md`.
7. **Static inline display is a notebook** (`jupyter/static.ipynb`); **live
   inline display is markdown** (`jupyter/live.md`). A live notebook would emit
   a dead `localhost` iframe in the static site and would fail the build if it
   used blocking calls (`run()`/`wait()`/`show()`/`animate()`).
8. **`object-interaction.md` goes under `visualizer/`** (it is the low-level
   `Visualizer` pointer-interaction API, not `VisualizerApp`).

## Target folder structure

```
docs/py/viz/
├── index.md                    stays
├── use-cases-scripts.md        stays
├── use-cases-notebooks.md      stays
│
├── scene-objects/              NEW (was "entities")
│   ├── index.md                NEW — entity/operator → style → page table
│   ├── entities.ipynb          NEW — compiled notebook (static HTML examples)
│   ├── operators.md            NEW — operators + style params
│   ├── axes-grid.md            moved
│   ├── point-path.md           moved
│   └── active-elements/        moved
│       ├── index.md
│       └── act-point.md
│
├── visualizer/                 NEW (was "api" — the Visualizer class)
│   ├── index.md                NEW — section overview
│   ├── visualizer.md           moved
│   ├── scene-graph.md          moved
│   ├── camera.md               moved
│   ├── animation.md            moved
│   └── object-interaction.md   moved
│
├── visualizerapp/              NEW — VisualizerApp
│   ├── index.md                NEW — overview + lifecycle routing
│   ├── app.md                  moved (quickstart)
│   ├── controls.md             NEW (split from interactive.md)
│   └── handlers.md             NEW (lifecycle + handler contract)
│
├── jupyter/                    NEW — Jupyter usage
│   ├── index.md                moved/split from jupyter.md
│   ├── live.md                 NEW — live inline (markdown, not executed)
│   └── static.ipynb            NEW — static inline (executed notebook)
│
├── styles/                     NEW (was "styling")
│   ├── index.md                NEW — section overview
│   ├── styles.md               moved
│   ├── labels.md               moved
│   ├── texture-labels.md       moved
│   └── title-annotation.md     moved
│
└── export/                     unchanged
    ├── index.md
    ├── html.md
    ├── gltf.md
    └── video-image.md
```

## Target nav

The Visualization section of `mkdocs.yml` `nav` becomes:

```yaml
  - Visualization:
    - Overview: py/viz/index.md
    - Use cases - Scripts: py/viz/use-cases-scripts.md
    - Use cases - Jupyter: py/viz/use-cases-notebooks.md
    - Scene Objects:
      - Overview: py/viz/scene-objects/index.md
      - Entities: py/viz/scene-objects/entities.ipynb
      - Operators: py/viz/scene-objects/operators.md
      - Axes & Grid: py/viz/scene-objects/axes-grid.md
      - PointPath: py/viz/scene-objects/point-path.md
      - Active Elements:
        - Overview: py/viz/scene-objects/active-elements/index.md
        - ActPoint: py/viz/scene-objects/active-elements/act-point.md
    - Visualizer:
      - Overview: py/viz/visualizer/index.md
      - Visualizer: py/viz/visualizer/visualizer.md
      - Scene Graph & Transforms: py/viz/visualizer/scene-graph.md
      - Camera & Controls: py/viz/visualizer/camera.md
      - Animation: py/viz/visualizer/animation.md
      - Object Interaction: py/viz/visualizer/object-interaction.md
    - Visualizer App:
      - Overview: py/viz/visualizerapp/index.md
      - Quickstart: py/viz/visualizerapp/app.md
      - Controls: py/viz/visualizerapp/controls.md
      - Handlers & Lifecycle: py/viz/visualizerapp/handlers.md
    - Jupyter Notebooks:
      - Overview: py/viz/jupyter/index.md
      - Live inline display: py/viz/jupyter/live.md
      - Static inline display: py/viz/jupyter/static.ipynb
    - Styles:
      - Overview: py/viz/styles/index.md
      - Style System: py/viz/styles/styles.md
      - Labels: py/viz/styles/labels.md
      - Texture Labels: py/viz/styles/texture-labels.md
      - Title & Annotation: py/viz/styles/title-annotation.md
    - Export:
      - Overview: py/viz/export/index.md
      - Standalone HTML: py/viz/export/html.md
      - glTF export: py/viz/export/gltf.md
      - Video & Image: py/viz/export/video-image.md
```

This also fixes three pages currently missing from the nav: `texture-labels.md`,
`object-interaction.md`, and `active-elements/`.

## New pages — content specs

### scene-objects/index.md

Canonical table: entity/operator → style class → page, cross-referencing
`docs/py/geometry/entities.md` + `operators.md` and `demo_all_entities.py` +
`demo_operators.py`.

### scene-objects/entities.ipynb (compiled)

One section per entity: a markdown intro, a style-field table, then a code cell
ending in `viz.display_snapshot()` (or `viz.display_row(..., mode="static")`) so
the static Three.js viewer is embedded in the built page.

| Entity | Style | Fields |
|---|---|---|
| Point | PointStyle | color, opacity, size |
| Point (crosshair) | CrossHairPointStyle(PointStyle) | + arm_thickness |
| Direction | DirectionStyle | color, opacity, length |
| HPoint | HPointStyle | color, opacity, size |
| PointPair | PointPairStyle | color, opacity, point_size, line_thickness, wireframe* |
| Line | LineStyle | color, opacity, length, thickness, wireframe* |
| Line (cylinder) | CylinderLineStyle(LineStyle) | thickness (world units) |
| Plane | PlaneStyle | color, opacity, extent, wireframe*, texture_label, double_sided |
| Circle | CircleStyle | color, opacity, wireframe* |
| Sphere | SphereStyle | color, opacity, wireframe*, texture_label, double_sided |
| Space | SpaceStyle | color, opacity, extent |

`wireframe*` = `wireframe`, `wireframe_dash`, `wireframe_color`,
`wireframe_opacity`. Imaginary variants (`ImagCircle`/`ImagSphere`/
`ImagPointPair`) reuse the real style class with dotted-wireframe canonical
defaults — document them, don't duplicate.

Viz scene objects:

| Object | Style | Fields |
|---|---|---|
| Axes2D | Axes2DStyle | u, v (AxisStyle) |
| Axes3D | Axes3DStyle | u, v, w (AxisStyle) |
| Axis | AxisStyle | color, opacity, line_thickness, label_style, value_style |
| Grid | GridStyle | color, opacity, line_thickness |
| PointPath | PointPathStyle | color, opacity, line_thickness |

### scene-objects/operators.md

| Operator | Style | Fields |
|---|---|---|
| ReflectionPlane | ReflectionPlaneStyle | color, opacity, extent |
| ReflectionLine | ReflectionLineStyle | color, opacity, length, thickness |
| ReflectionPoint | ReflectionPointStyle | color, opacity, extent (defined but not in `__all__`) |
| Inversion | InversionStyle | color, opacity |
| Rotor | RotorStyle | color, opacity, disc_radius |
| Translator | TranslatorStyle | color, opacity, length |
| Dilator | DilatorStyle | color, opacity, ring_count, max_radius |
| Motor | MotorStyle | color, opacity |
| GeneralRotor | GeneralRotorStyle | color, opacity |

### visualizer/index.md, styles/index.md, jupyter/index.md, visualizerapp/index.md

Short section-overview pages (match `export/index.md`).

### visualizerapp/controls.md + handlers.md

Split `interactive.md`: `controls.md` = `add_slider`/`add_dropdown`/
`add_button`/`add_group`/`remove_control`/`remove_group`/`clear_controls` +
scene-scoped controls; `handlers.md` = lifecycle (`run` → `init` → wait →
`cleanup` → stop), handler contract, `ControlEvent`, async patterns.

### jupyter/index.md, live.md, static.ipynb

Split `jupyter.md`:

- `index.md` — auto-detection, "how it works", limitations, live-vs-static
  routing table.
- `live.md` — `start_server()`/`flush()`/`_repr_html_()`, idempotent
  `show()`/`display()`, `display_row(mode="live")`, `VizSceneHandle.display()`,
  animation loop (markdown code blocks — not executed).
- `static.ipynb` — `display_snapshot()`, `display_row(mode="static")`,
  multi-scene (executed, embedded static HTML).

## File moves (use `git mv`)

| From | To |
|---|---|
| axes-grid.md | scene-objects/axes-grid.md |
| point-path.md | scene-objects/point-path.md |
| active-elements/ | scene-objects/active-elements/ |
| visualizer.md | visualizer/visualizer.md |
| scene-graph.md | visualizer/scene-graph.md |
| camera.md | visualizer/camera.md |
| animation.md | visualizer/animation.md |
| object-interaction.md | visualizer/object-interaction.md |
| app.md | visualizerapp/app.md |
| interactive.md | (split) visualizerapp/controls.md + handlers.md |
| jupyter.md | (split) jupyter/index.md + live.md |
| styles.md | styles/styles.md |
| labels.md | styles/labels.md |
| texture-labels.md | styles/texture-labels.md |
| title-annotation.md | styles/title-annotation.md |

## Cross-reference rewrites

Full pass over every moved file plus the top-level `index.md` Topics + Use-Cases
routing. Key breakages:

- `visualizer.md` → camera.md, axes-grid.md, animation.md, jupyter.md, export.
- `active-elements/index.md` → `../object-interaction.md` becomes
  `../../visualizer/object-interaction.md`.
- `camera.md` → `export/video-image.md` becomes `../export/video-image.md`.
- `styles.md` → `texture-labels.md`, `labels.md`, `title-annotation.md`.
- `index.md` → Topics/Use-Cases routing and the Jupyter examples link.
- `use-cases-notebooks.md` → `jupyter.md` becomes `jupyter/index.md`.

## Config changes

1. `mkdocs.yml` — add the plugin and the new nav:

```yaml
plugins:
  - search
  - mkdocs-jupyter:
      execute: true
      ignore_h1_titles: true
      include_source: true
      kernel_name: python3
```

2. `pyproject.toml` — add to `[dependency-groups] dev`:

```toml
"mkdocs-jupyter>=0.25",
```

3. `.gitignore` — add `.cache/` (mkdocs-jupyter default cache dir is
   `.cache/mkdocs-jupyter`).

## Phases

### Phase 0 — Preflight

- [x] Confirm this is docs/config-only (no `py/pytanga/` code changes).
- [x] Confirm `uv run python -c "import pytanga.viz"` works (needed to execute
      the notebooks at build time).

### Phase 1 — Folders + moves

- [x] `git mv` each file per the move table.
- [x] Create empty folders `scene-objects/`, `visualizer/`, `visualizerapp/`,
      `jupyter/`, `styles/`.

### Phase 2 — Overview pages

- [x] `scene-objects/index.md`
- [x] `visualizer/index.md`
- [x] `styles/index.md`
- [x] `visualizerapp/index.md`
- [x] `jupyter/index.md`

### Phase 3 — Scene objects

- [x] `scene-objects/entities.ipynb` (per-entity sections + `display_snapshot()`
      cells)
- [x] `scene-objects/operators.md`

### Phase 4 — VisualizerApp split

- [x] `visualizerapp/controls.md`
- [x] `visualizerapp/handlers.md`
- [x] Remove `interactive.md` (content migrated)

### Phase 5 — Jupyter split

- [x] `jupyter/live.md`
- [x] `jupyter/static.ipynb`
- [x] Remove `jupyter.md` (content migrated)

### Phase 6 — Cross-references

- [x] Rewrite links in all moved files per the table above.
- [x] Update top-level `index.md` Topics + Use-Cases routing.

### Phase 7 — Config

- [x] `mkdocs.yml` nav + `mkdocs-jupyter` plugin.
- [x] `pyproject.toml` dev dependency.
- [x] `.gitignore` `.cache/`.

### Phase 8 — Changelog

- [x] Append a Refactor bullet plus a Bug Fix bullet (three missing nav entries)
      to `docs/changelog/2026-08-22_fix-viz.md`.

### Phase 9 — Validation

- [x] `uv run mkdocs build --strict`
- [x] `uv run mkdocs serve` and spot-check Entities + Static-display pages render
      their embedded viewers
- [x] Grep built HTML to confirm no stray `localhost:8765` iframes

Validation notes: `mkdocs build --strict` passes cleanly (exit 0). Both
notebooks execute (`entities.ipynb` embeds 10 static viewers, `static.ipynb`
embeds 2) and no live `localhost` iframes remain. Four pre-existing
`_geometry.py` link warnings in `py/geometry/*.md` were also fixed (links now
point at the GitHub source file).

## Validation

- `uv run mkdocs build --strict` — catches broken links and confirms both
  `.ipynb` files compile and execute.
- `uv run mkdocs serve` — visually confirm `entities.ipynb` and `static.ipynb`
  render their embedded static Three.js viewers.
- Confirm the three previously-missing pages now appear in the nav.

## Notes / edge cases

- **mkdocs-jupyter × Material admonitions** — notebook markdown runs through
  nbconvert, so Material admonitions (`!!! note`) are not rendered; use raw HTML
  in notebook markdown cells for callouts.
- **Static ≠ offline** — `display_snapshot()` output loads Three.js/KaTeX from
  CDN, exactly like the rest of the docs; "static" means "serverless", not
  "no internet".
- **Execution timeout** — nbclient's default is 30 s/cell. The two executed
  notebooks must only call non-blocking serverless methods
  (`display_snapshot`, `display_row(mode="static")`), never
  `run()`/`wait()`/`show()`/`animate()`.
- **Caching** — mkdocs-jupyter caches executed outputs in
  `.cache/mkdocs-jupyter` (hence the `.gitignore` entry); unchanged notebooks
  are not re-executed.
- **`ReflectionPointStyle`** — defined in `_operator_styles.py` but not exported
  from `pytanga.viz.__all__`; reflect that in `operators.md`.

## Out of scope

- No `py/pytanga/` code changes.
- No changes to `py/examples/jupyter/*` (linked externally, not compiled).
- No changes to `docs/dev/` publishing-workflow docs.
