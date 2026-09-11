## Proposed `docs/py/viz` restructure

The current flat files plus the two existing subfolders (`export/`, `active-elements/`) map cleanly onto four topic areas. I recommend three new topic folders alongside the existing `export/`, with `index.md` + the two use-case files staying at the top level as you suggested.

### Folder structure

```
docs/py/viz/
├── index.md                    (top level — stays)
├── use-cases-scripts.md        (top level — stays)
├── use-cases-notebooks.md      (top level — stays)
│
├── entities/                   NEW — visualizable entities & operators
│   ├── index.md                NEW (reference table of viz-able entities/operators)
│   ├── axes-grid.md            moved
│   ├── point-path.md           moved
│   └── active-elements/        moved (the "active entities")
│       ├── index.md
│       └── act-point.md
│
├── api/                        NEW — the Visualizer API & app
│   ├── index.md                NEW (overview)
│   ├── visualizer.md           moved
│   ├── app.md                  moved
│   ├── interactive.md          moved
│   ├── scene-graph.md          moved
│   ├── camera.md               moved
│   ├── animation.md            moved
│   ├── jupyter.md              moved
│   └── object-interaction.md   moved
│
├── styling/                    NEW — style classes & annotation
│   ├── index.md                NEW (overview)
│   ├── styles.md               moved
│   ├── labels.md               moved
│   ├── texture-labels.md       moved
│   └── title-annotation.md     moved
│
└── export/                     (existing — unchanged)
    ├── index.md
    ├── html.md
    ├── gltf.md
    └── video-image.md
```

### Suggested mkdocs TOC (Visualization section)

```yaml
  - Visualization:
    - Overview: py/viz/index.md
    - Use cases - Scripts: py/viz/use-cases-scripts.md
    - Use cases - Jupyter: py/viz/use-cases-notebooks.md
    - Entities & Operators:
      - Overview: py/viz/entities/index.md
      - Axes & Grid: py/viz/entities/axes-grid.md
      - PointPath: py/viz/entities/point-path.md
      - Active Elements:
        - Overview: py/viz/entities/active-elements/index.md
        - ActPoint: py/viz/entities/active-elements/act-point.md
    - Visualizer API:
      - Overview: py/viz/api/index.md
      - Visualizer: py/viz/api/visualizer.md
      - Visualizer App: py/viz/api/app.md
      - Interactive Controls: py/viz/api/interactive.md
      - Scene Graph & Transforms: py/viz/api/scene-graph.md
      - Camera & Controls: py/viz/api/camera.md
      - Animation: py/viz/api/animation.md
      - Jupyter Notebooks: py/viz/api/jupyter.md
      - Object Interaction: py/viz/api/object-interaction.md
    - Styling & Annotation:
      - Overview: py/viz/styling/index.md
      - Style System: py/viz/styling/styles.md
      - Labels: py/viz/styling/labels.md
      - Texture Labels: py/viz/styling/texture-labels.md
      - Title & Annotation: py/viz/styling/title-annotation.md
    - Export:
      - Overview: py/viz/export/index.md
      - Standalone HTML: py/viz/export/html.md
      - glTF export: py/viz/export/gltf.md
      - Video & Image: py/viz/export/video-image.md
```

### Notes & observations

1. **Three pages currently missing from the nav** — `texture-labels.md`, `object-interaction.md`, and the whole `active-elements/` folder are on disk but absent from `nav`. The proposed TOC adds them. This is a fix worth highlighting in the changelog.

2. **New index pages to author** — `entities/index.md`, `api/index.md`, and `styling/index.md` don't exist yet. The first is the substantive one: a canonical table of which geometric entities and operators can be `add()`ed to a scene, cross-referencing `docs/py/geometry/entities.md` / `operators.md` and the `demo_all_entities.py` / `demo_operators.py` examples. The other two would be short section-overview pages (matching the `export/index.md` pattern).

3. **`app.md` ↔ `interactive.md` overlap** — both cover `VisualizerApp` and controls. They already cross-reference each other (app = quickstart, interactive = full reference), so I recommend keeping both under `api/` rather than merging, to avoid churn.

4. **Cross-reference updates** — moving files breaks every internal relative link. Example: `visualizer.md` links to `camera.md`, `axes-grid.md`, `animation.md`, and `jupyter.md`; `active-elements/index.md` links to `../object-interaction.md`; `camera.md` links to `export/video-image.md`. These all need rewriting to the new paths (e.g. `[Camera](camera.md)` → `[Camera](../api/camera.md)`, and the top-level `index.md` "Topics" + "Use Cases" routing tables to the new locations). I'll do a full pass.

### Two decisions I'd like your input on before implementing

- **Folder naming** — I used `entities/`, `api/`, `styling/`. Alternatives: `scene-objects/`, `visualizer/`, `styles/`. Any preference?
- **`point-path.md` placement** — I placed it under `entities/` (it's a drawable scene object/trail), but it could also fit `styling/` (it has its own `PointPathStyle`) or `api/`. My recommendation is `entities/`.

Once you confirm the naming and the two open questions, I'll implement: create the folders, move the files, author the three new index pages, rewrite all cross-references, and update `mkdocs.yml` plus the changelog.