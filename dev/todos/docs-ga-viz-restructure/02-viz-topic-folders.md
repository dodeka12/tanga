# Phase 2 — Viz Topic Folders

## Goal

Reorganize `docs/py/viz/` into topic folders matching `py/examples/viz/`, author
the new section index pages, and update `mkdocs.yml` + cross-references.

## Files

- New: `docs/py/viz/entities/index.md`, `plotting/index.md`,
  `interaction/index.md`, `labels/index.md`, `styling/index.md`, `sdf/index.md`
- Move: all files listed in the steps below
- Delete (superseded): `docs/py/viz/scene-objects/index.md`,
  `docs/py/viz/styles/index.md`
- Edit: `mkdocs.yml`, `docs/py/viz/index.md`, and any moved file with stale
  relative links

## Steps

- [ ] **2.1 — Create the new topic folders**
  - Create `docs/py/viz/{app,entities,plotting,interaction,labels,styling,sdf}`.
  - `visualizer/`, `export/`, `jupyter/` already exist.

- [ ] **2.2 — Move the files (`git mv` each)**
  - `visualizerapp/` → `app/`: `app.md`, `layouts.md`, `handlers.md`,
    `banners.md`, `file-chooser.md`, `index.md`.
  - `visualizerapp/controls.md` → `interaction/controls.md` (not into `app/`).
  - `visualizer/object-interaction.md` → `interaction/object-interaction.md`.
  - `scene-objects/entities.ipynb` → `entities/entities.ipynb`.
  - `scene-objects/operators.ipynb` → `entities/operators.ipynb`.
  - `scene-objects/motor-decomposition.md` → `entities/motor-decomposition.md`.
  - `scene-objects/axes-grid.md` → `entities/axes-grid.md`.
  - `scene-objects/point-path.md` → `entities/point-path.md`.
  - `scene-objects/active-elements/` → `entities/active-elements/` (folder).
  - `scene-objects/coordinate-system.md` → `plotting/coordinate-system.md`.
  - `scene-objects/coordinate-system.ipynb` → `plotting/coordinate-system.ipynb`.
  - `styles/labels.md` → `labels/labels.md`.
  - `styles/texture-labels.md` → `labels/texture-labels.md`.
  - `styles/title-annotation.md` → `labels/title-annotation.md`.
  - `styles/styles.md` → `styling/styles.md`.
  - `sdf-viewer.md` → `sdf/sdf-viewer.md`.
  - `sdf-objects.md` → `sdf/sdf-objects.md`.
  - Delete the now-empty `visualizerapp/`, `scene-objects/`, `styles/` folders.

- [ ] **2.3 — Fold superseded index pages**
  - Delete `scene-objects/index.md` and `styles/index.md`; fold any still-useful
    prose (entity/operator lists, style overview) into the new index pages in
    2.4 rather than discarding it.

- [ ] **2.4 — Author the new section index pages**
  - `entities/index.md` — canonical table of which geometry entities/operators
    can be `add()`ed, linking `entities.ipynb`, `operators.ipynb`,
    `motor-decomposition.md`, `axes-grid.md`, `point-path.md`, `active-elements/`,
    and cross-referencing `../ga/geometry/entities.md` and `operators.md`.
  - `plotting/index.md` — CoordinateSystem plotting helper; link
    `coordinate-system.md` / `coordinate-system.ipynb`.
  - `interaction/index.md` — overview of the three control/interaction surfaces
    (panel controls, control views, object interaction); link `controls.md` and
    `object-interaction.md` (and note `control-views.md` arrives in Phase 3).
  - `labels/index.md` — labels, texture labels, title & annotation; link the
    three moved pages.
  - `styling/index.md` — style system; link `styles.md`.
  - `sdf/index.md` — SDF viewer overview; link `sdf-viewer.md`, `sdf-objects.md`.

- [ ] **2.5 — Update `mkdocs.yml` Visualization nav**
  - Replace the `Scene Objects`, `Visualizer App`, and old `styles`/SDF entries
    with the target nav in `README.md` (`Visualizer`, `Visualizer App`,
    `Entities & Operators`, `Plotting`, `Interaction & Controls`, `Labels &
    Annotation`, `Styling`, `SDF Viewer`, `Jupyter Notebooks`, `Export`).
  - `Interaction & Controls` lists `controls.md` and `object-interaction.md`
    now; `control-views.md` is added in Phase 3.

- [ ] **2.6 — Fix cross-references**
  - Rewrite `docs/py/viz/index.md` "Topics" + "Use Cases" routing tables to the
    new paths.
  - Fix links inside moved pages (e.g. `scene-objects/` → `entities/` or
    `plotting/`, `styles/` → `labels/` or `styling/`, `visualizerapp/` → `app/`,
    `controls.md` now at `../interaction/controls.md`).
  - `active-elements/index.md` → `../../interaction/object-interaction.md`.
  - `app/layouts.md` → `../visualizer/split-views.md` and
    `../interaction/controls.md`.

## Validation

```powershell
uv run mkdocs build --strict
Get-ChildItem docs/py/viz -Recurse -Include *.md |
  Select-String -Pattern 'scene-objects/|visualizerapp/|styles/'
```

The second command must return no matches.

## Notes

- This is the largest phase; keep it as one atomic move + nav + link change so
  the site never points at a missing path.
- Keep `visualizer/` intact except for moving `object-interaction.md` out.
