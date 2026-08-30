# Docs GA/Viz Restructure — Overview

**Created:** 2026-08-30 | **Status:** Planned | **Branch:** `fix/docs`

## Goal

Reorganize `docs/py/` so the Python documentation mirrors the topic structure
of `py/examples/`: a top-level `ga/` folder for geometric-algebra reference
docs and a top-level `viz/` folder whose subfolders match the visualization
example topics. As part of this, author the missing reference page that
documents every declarative `xxxView` layout/control class in
`py/pytanga/viz/views.py`.

## Architecture (short)

Three pieces, implemented in dependency order:

1. **GA folder** — move the eight GA topic folders (`algebra`, `basis`,
   `blade-mask`, `matrix`, `solver`, `tensors`, `expression`, `geometry`)
   from `docs/py/<topic>/` to `docs/py/ga/<topic>/`. `docs/py/index.md`
   becomes a slim "pytanga" landing; the GA overview content moves to
   `docs/py/ga/index.md`. `docs/py/env/` stays top-level (shared setup).
2. **Viz folders** — reorganize `docs/py/viz/` into topic folders matching
   `py/examples/viz/`:
   - `visualizer/` stays (core `Visualizer` API) but loses
     `object-interaction.md`.
   - `visualizerapp/` → `app/`.
   - `scene-objects/` → split into `entities/` and `plotting/`.
   - `styles/` → split into `labels/` and `styling/`.
   - the two top-level SDF docs → new `sdf/`.
   - `interaction/` = panel controls + the new control-views reference +
     object interaction.
   - `export/` and `jupyter/` stay unchanged.
3. **Controls reference** — new `interaction/control-views.md` documenting all
   17 `xxxView` classes (layout containers + HTML control views) and their
   mapping to the panel `add_*` controls.

The target tree below is the fixed contract; every phase implements against it
and updates `mkdocs.yml` + internal links so the site keeps building.

## Decisions (confirmed)

- **GA split**: `docs/py/ga/` holds all GA reference docs; `docs/py/index.md`
  becomes a slim landing; `env/` stays top-level.
- **Viz naming**: use the example-aligned names `visualizer/`, `app/`,
  `entities/`, `plotting/`, `interaction/`, `labels/`, `styling/`, `sdf/`
  (plus unchanged `export/`, `jupyter/`). `visualizerapp/` is renamed `app/`.
- **`point-path.md` and `axes-grid.md`** live in `entities/` (drawable scene
  objects).
- **`coordinate-system.md` / `coordinate-system.ipynb`** live in `plotting/`.
- **`controls.md`** (panel `add_*` controls) moves from `visualizerapp/` to
  `interaction/`; `layouts.md` stays in `app/` (it is the app-level layout
  guide) and cross-links to the new `interaction/control-views.md`.
- **`control-views.md`** lives in `interaction/` and documents all 17
  `xxxView` classes: `View`, `SceneView`, `SpacerView`, `SplitView`,
  `StackView`, `GroupView`, `ControlView`, `SliderView`, `ButtonView`,
  `DropdownView`, `FileChooserView`, `TextFieldView`, `TextAreaView`,
  `ColorPickerView`, `CheckboxView`, `ValueEditView`, `TableView`.
- **No `.ipynb` → `.md` conversion**: notebooks move as-is.

## Target tree (fixed contract)

```
docs/py/
├── index.md                     # slim "pytanga" landing (rewritten)
├── env/                         # unchanged
├── ga/                          # NEW — all GA reference docs
│   ├── index.md                 # NEW (GA overview, from old py/index.md)
│   ├── algebra/
│   ├── basis/
│   ├── blade-mask/
│   ├── matrix/
│   ├── solver/
│   ├── tensors/
│   ├── expression/
│   └── geometry/
├── viz/
│   ├── index.md                 # overview (stays)
│   ├── use-cases-scripts.md     # stays top-level
│   ├── use-cases-notebooks.md   # stays top-level
│   ├── visualizer/              # core Visualizer API (stays, minus 1 file)
│   │   ├── index.md
│   │   ├── visualizer.md
│   │   ├── camera.md
│   │   ├── animation.md
│   │   ├── multi-scene.md
│   │   ├── split-views.md
│   │   └── scene-graph.md
│   ├── app/                     # renamed from visualizerapp/
│   │   ├── index.md
│   │   ├── app.md
│   │   ├── layouts.md
│   │   ├── handlers.md
│   │   ├── banners.md
│   │   └── file-chooser.md
│   ├── entities/                # NEW — replaces scene-objects/ (entities part)
│   │   ├── index.md             # NEW (reference table)
│   │   ├── entities.ipynb       # moved
│   │   ├── operators.ipynb      # moved
│   │   ├── motor-decomposition.md
│   │   ├── axes-grid.md
│   │   ├── point-path.md
│   │   └── active-elements/
│   │       ├── index.md
│   │       └── act-point.md
│   ├── plotting/                # NEW — replaces scene-objects/ (plotting part)
│   │   ├── index.md             # NEW
│   │   ├── coordinate-system.md
│   │   └── coordinate-system.ipynb
│   ├── interaction/             # NEW — controls + object interaction
│   │   ├── index.md             # NEW
│   │   ├── controls.md          # moved from visualizerapp/
│   │   ├── control-views.md     # NEW (Phase 3 — all xxxView classes)
│   │   └── object-interaction.md
│   ├── labels/                  # NEW — split from styles/
│   │   ├── index.md             # NEW
│   │   ├── labels.md
│   │   ├── texture-labels.md
│   │   └── title-annotation.md
│   ├── styling/                 # NEW — split from styles/
│   │   ├── index.md             # NEW
│   │   └── styles.md
│   ├── sdf/                     # NEW
│   │   ├── index.md             # NEW
│   │   ├── sdf-viewer.md
│   │   └── sdf-objects.md
│   ├── export/                  # unchanged
│   │   ├── index.md
│   │   ├── html.md
│   │   ├── gltf.md
│   │   └── video-image.md
│   └── jupyter/                 # unchanged
│       ├── index.md
│       ├── live.md
│       └── static.ipynb
└── examples/                    # auto-generated — unchanged
    ├── ga/
    └── viz/
```

## Target nav (fixed contract)

`mkdocs.yml` — Python sections only (Environment and Examples unchanged):

```yaml
  - Python (pytanga):
    - Overview: py/index.md

  - Geometric Algebra:
    - Overview: py/ga/index.md
    - Algebra:
      - Overview: py/ga/algebra/index.md
      - Algebra class: py/ga/algebra/algebra.md
      - MV class: py/ga/algebra/mv.md
      - Duals: py/ga/algebra/duals.md
      - Modulus arithmetic: py/ga/algebra/modulus.md
    - Basis Classes:
      - Overview: py/ga/basis/index.md
      - Bases (E3, P3, N3, PGA3): py/ga/basis/bases.md
      - Null-vector embedding: py/ga/basis/pga_null_embedding.md
      - BasisPGA3: py/ga/basis/basis_pga3.md
    - BladeMask:
      - Overview: py/ga/blade-mask/index.md
      - Construction: py/ga/blade-mask/construction.md
      - Properties & operations: py/ga/blade-mask/properties-and-ops.md
      - Usage in pipelines: py/ga/blade-mask/usage.md
      - Inverse blade mask: py/ga/blade-mask/inverse-blade-mask.md
    - Matrix Operations:
      - Overview: py/ga/matrix/index.md
      - MVMatrix: py/ga/matrix/mvmatrix.md
      - MVProductMatrix: py/ga/matrix/mvproductmatrix.md
    - Equation Solving:
      - Overview: py/ga/solver/index.md
      - Solvers: py/ga/solver/solve.md
      - Blade mask pipeline: py/ga/solver/blade-mask-pipeline.md
      - Matrix primitives: py/ga/solver/matrix-primitives.md
      - Enums & coercion: py/ga/solver/enums.md
    - Tensor Operations:
      - Overview: py/ga/tensors/index.md
      - MVTensor: py/ga/tensors/mvtensor.md
      - Labeled tensors: py/ga/tensors/labeled-tensor.md
      - Label iterator: py/ga/tensors/iterator.md
      - Product tensor: py/ga/tensors/product-tensor.md
    - Expressions:
      - Overview: py/ga/expression/index.md
      - Usage: py/ga/expression/usage.md
    - Geometry:
      - Overview: py/ga/geometry/index.md
      - Entities: py/ga/geometry/entities.md
      - MV-accepting constructors: py/ga/geometry/mv-constructors.md
      - Operators: py/ga/geometry/operators.md
      - Analysis pipeline: py/ga/geometry/analysis.md
      - Creation pipeline: py/ga/geometry/create.md
      - Variables & blade masks: py/ga/geometry/variables.md
      - Random generation: py/ga/geometry/random.md
      - Round-trip examples: py/ga/geometry/round-trip.md

  - Visualization:
    - Overview: py/viz/index.md
    - Use cases - Scripts: py/viz/use-cases-scripts.md
    - Use cases - Jupyter: py/viz/use-cases-notebooks.md
    - Visualizer:
      - Overview: py/viz/visualizer/index.md
      - Visualizer: py/viz/visualizer/visualizer.md
      - Camera & Controls: py/viz/visualizer/camera.md
      - Animation: py/viz/visualizer/animation.md
      - Multi-Scene: py/viz/visualizer/multi-scene.md
      - Split Views: py/viz/visualizer/split-views.md
      - Scene Graph & Transforms: py/viz/visualizer/scene-graph.md
    - Visualizer App:
      - Overview: py/viz/app/index.md
      - Quickstart: py/viz/app/app.md
      - Layouts (Split Views & Controls): py/viz/app/layouts.md
      - Handlers & Lifecycle: py/viz/app/handlers.md
      - Banners & Dialogs: py/viz/app/banners.md
      - File Chooser: py/viz/app/file-chooser.md
    - Entities & Operators:
      - Overview: py/viz/entities/index.md
      - Entities: py/viz/entities/entities.ipynb
      - Operators: py/viz/entities/operators.ipynb
      - Motor decomposition: py/viz/entities/motor-decomposition.md
      - Axes & Grid: py/viz/entities/axes-grid.md
      - PointPath: py/viz/entities/point-path.md
      - Active Elements:
        - Overview: py/viz/entities/active-elements/index.md
        - ActPoint: py/viz/entities/active-elements/act-point.md
    - Plotting:
      - Overview: py/viz/plotting/index.md
      - Coordinate System: py/viz/plotting/coordinate-system.md
      - Coordinate System (examples): py/viz/plotting/coordinate-system.ipynb
    - Interaction & Controls:
      - Overview: py/viz/interaction/index.md
      - Panel Controls: py/viz/interaction/controls.md
      - Control Views (xxxView): py/viz/interaction/control-views.md
      - Object Interaction: py/viz/interaction/object-interaction.md
    - Labels & Annotation:
      - Overview: py/viz/labels/index.md
      - Labels: py/viz/labels/labels.md
      - Texture Labels: py/viz/labels/texture-labels.md
      - Title & Annotation: py/viz/labels/title-annotation.md
    - Styling:
      - Overview: py/viz/styling/index.md
      - Style System: py/viz/styling/styles.md
    - SDF Viewer:
      - Overview: py/viz/sdf/index.md
      - SDF Viewer: py/viz/sdf/sdf-viewer.md
      - SDF Objects in the Standard Viewer: py/viz/sdf/sdf-objects.md
    - Jupyter Notebooks:
      - Overview: py/viz/jupyter/index.md
      - Live: py/viz/jupyter/live.md
      - Static: py/viz/jupyter/static.ipynb
    - Export:
      - Overview: py/viz/export/index.md
      - Standalone HTML: py/viz/export/html.md
      - glTF export: py/viz/export/gltf.md
      - Video & Image: py/viz/export/video-image.md
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-ga-folder-restructure.md](./01-ga-folder-restructure.md) | Move GA topics under `ga/`, author `ga/index.md`, slim `py/index.md`, update GA nav |
| 2 | [02-viz-topic-folders.md](./02-viz-topic-folders.md) | Reorganize `viz/` into topic folders, author new index pages, update viz nav |
| 3 | [03-controls-reference.md](./03-controls-reference.md) | Author `interaction/control-views.md` (all `xxxView` classes) |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Final link/nav validation, changelog, supersede stale plan |

## Testing as you go

- `uv run mkdocs build --strict` — the primary gate; run after every phase.
- Grep for stale paths after each move, e.g.:

  ```powershell
  Get-ChildItem docs/py -Recurse -Include *.md |
    Select-String -Pattern 'scene-objects/|visualizerapp/|styles/|py/algebra/|py/basis/|py/blade-mask/|py/matrix/|py/solver/|py/tensors/|py/expression/|py/geometry/'
  ```

- `uv run python tools/generate-example-docs.py --check` — the auto-generated
  `examples/` docs are untouched, but this guards against drift.

## Non-goals

- No changes to `py/examples/` or the `docs/py/examples/` generator/hook.
- No content rewrites of GA/viz pages beyond what the move + cross-reference
  fixes require (`control-views.md` is new content, not a rewrite).
- No changes to C++, developer, or changelog sections beyond the new branch
  changelog.

