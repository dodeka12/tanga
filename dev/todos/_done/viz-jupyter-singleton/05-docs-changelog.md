# Phase 5 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture.  If this work introduces or changes architecture, update the
> developer docs.

## Goal

Document the new Jupyter re-run behaviour — clarifying the main notebook use
cases and their caveats in the use-case overview and the Jupyter docs — and add
the branch changelog.

## Files

- Edit: `docs/py/viz/index.md` — "Use Cases → Jupyter notebook" routing block
- Edit: `docs/py/viz/use-cases-notebooks.md` — notebook use cases + caveats
- Edit: `docs/py/viz/jupyter/index.md` — Jupyter overview + limitations
- Edit: `docs/py/viz/jupyter/live.md` — live inline display workflow
- New: `docs/changelog/YYYY-MM-DD_feat-jupyter-visualizer.md` (branch form)

## Steps

- [x] **5.1 — Update the use-case overview (`docs/py/viz/index.md`)**
  - In the "Use Cases → Jupyter notebook" block, keep the routing links intact
    and clarify the main use cases: **re-run safety** (re-constructing
    `Visualizer()` in a cell is safe — it returns the same instance and clears
    the default scene), **one-off demo** (`with viz:`), **animation**
    (`animate(auto_clear=True)` / pre-create + `.entity` in place), and
    **static snapshot** (`display_snapshot()`).
  - Add a one-line caveat pointer to `use-cases-notebooks.md` for the full
    re-run / reset semantics (do not duplicate the explanation here).

- [x] **5.2 — Rewrite the notebook use cases (`docs/py/viz/use-cases-notebooks.md`)**
  - Replace the "Don't recreate the `Visualizer` in the cell you re-run"
    `!!! warning` block with the new behaviour: under Jupyter, `Visualizer()` is
    a singleton; re-running a construction cell clears the default scene and
    re-adds axes/grid per `add_default_axes` / `add_default_grid`.
  - Document the main use cases: **iterating in one cell** (`viz.add` + `show()`
    is idempotent), **full reset on re-run** (`with viz:` or `viz.clear()`),
    and **multiple scenes** (`viz.scene(name)` — created on first call, cleared
    on a same-cell re-run, get-or-create across different cells).
  - Add a **Caveats** subsection covering: singleton is Jupyter-only
    (scripts/apps/tests unchanged); constructor config other than axes/grid is
    first-call-wins; `stop_server()` stops the shared server for the whole
    kernel; port 8765 can still conflict across kernels.

- [x] **5.3 — Update the Jupyter docs (`jupyter/index.md`, `jupyter/live.md`)**
  - In `index.md`, update the auto-detection / re-run guidance to the singleton
    + re-run reset semantics (the "don't recreate" advice becomes unnecessary);
    keep the live-vs-static table and the Limitations section.
  - In `live.md`, state that `scene(name)` clears on a same-cell re-run but is
    get-or-create across different cells; keep `with viz:` / `viz.clear()` as
    the explicit reset idiom; note the first-call-wins caveat for `camera` /
    `title` / `space_dim`.

- [x] **5.4 — Add the branch changelog**
  - Create `docs/changelog/<today>_feat-jupyter-visualizer.md` per
    `dev/workflows/changelog.md`: title from `uv run python tools/last-release.py`;
    add a **New Features** bullet for the Jupyter-scoped singleton + re-run
    reset, and a **Bug Fixes** bullet for the "port already in use on cell
    re-run" failure.
  - Do **not** touch `docs/changelog/index.md` yet — it is updated at PR time
    (hash rename) per `dev/workflows/pull-request.md`.

## Validation

`uv run mkdocs build --strict` and `uv run python tools/last-release.py`

## Notes

- The changelog filename uses the branch name `feat/jupyter-visualizer` now;
  rename to the short commit hash at PR time.
