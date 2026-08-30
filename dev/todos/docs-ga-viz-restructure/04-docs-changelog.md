# Phase 4 — Final Validation + Changelog

## Goal

Run the full validation pass, confirm no stale paths or orphaned pages remain,
record the change in the branch changelog, and supersede the stale planning
note.

## Files

- New: `docs/changelog/2026-08-30_fix-docs.md` (branch changelog)
- Edit: `dev/todos/docs-ga-viz-restructure/README.md` (Status → Done)
- Move/annotate: `dev/todos/viz-docs-restructure.md` (supersede)

## Steps

- [ ] **4.1 — Full stale-path grep**
  - Search `docs/` and `mkdocs.yml` for every old path segment and confirm zero
    matches: `py/algebra/`, `py/basis/`, `py/blade-mask/`, `py/matrix/`,
    `py/solver/`, `py/tensors/`, `py/expression/`, `py/geometry/`,
    `scene-objects/`, `visualizerapp/`, `styles/`.

- [ ] **4.2 — Build + orphan check**
  - `uv run mkdocs build --strict` must pass with no warnings.
  - Confirm every `.md`/`.ipynb` under `docs/py/ga` and `docs/py/viz` is
    reachable from the nav (mkdocs strict mode flags unreferenced pages).

- [ ] **4.3 — Examples drift gate**
  - `uv run python tools/generate-example-docs.py --check` (unchanged, but guards
    against accidental drift).

- [ ] **4.4 — Branch changelog**
  - Follow `dev/workflows/changelog.md`:
    - Create `docs/changelog/2026-08-30_fix-docs.md`.
    - Title: run `uv run python tools/last-release.py` and use
      `# Changes since version <result>`.
    - Add a `## Refactor` bullet (or `## New Features` for the controls page):
      **Docs GA/Viz restructure** — and the new `xxxView` control-views reference.
  - Do not update `docs/changelog/index.md` yet (that happens at PR time).

- [ ] **4.5 — Supersede the stale plan**
  - Move `dev/todos/viz-docs-restructure.md` to `dev/todos/_done/` (or prepend a
    one-line `Superseded by docs-ga-viz-restructure` note) so it is no longer
    read as an active plan.

- [ ] **4.6 — Mark plan done**
  - Set `Status: Done` in `dev/todos/docs-ga-viz-restructure/README.md`.

## Validation

```powershell
uv run mkdocs build --strict
uv run python tools/generate-example-docs.py --check
```

## Notes

- `dev/workflows/mkdocs-publishing.md` is referenced by `mkdocs.yml` nav but does
  not exist on disk — flag it in review, but fixing it is out of scope here.
