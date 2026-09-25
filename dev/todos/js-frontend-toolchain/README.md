# JS frontend toolchain — Overview

**Created:** 2026-09-24 | **Status:** Done | **Branch:** `feat/ui-layout-update`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Consolidate the JS development toolchain under `js/dev/` (package.json, unit
tests, headless smoke, README) while leaving the published CDN artifact
untouched at `js/` top level. Repoint the offline-export esbuild discovery, make
the frontend logic **unit-testable without a browser** (with `node --test` unit
tests for the reconciliation/orphan-map), wire JS validation into the local
pre-commit hooks and the PR checklist, and document the setup — **without ever
running JS tests / esbuild / Playwright in GitHub Actions**.

## Architecture (short)

- **`js/` = published artifact only.** `tanga-viewer.js` +
  `tanga-viewer.manifest.json` are load-bearing (`tools/build-viewer-js.py`
  writes them; `py/pytanga/viz/export/_cdn.py` serves `js/tanga-viewer.js` via
  jsDelivr for `delivery="cdn"`). They stay at `js/` top level and are never moved.
- **`js/dev/` = the JS toolchain.** `package.json` (esbuild + playwright),
  `tests/` (`.test.mjs` unit tests + headless smoke), `README.md`, and a
  gitignored `node_modules/`.
- **Pure logic is separated from the DOM.** The reconciliation/orphan-map
  accounting lives in a DOM-free module (`templates/views/reconcile.js`),
  unit-tested with `node --test`; the DOM/WebGL layers (`build.js`, `viewer.js`,
  `three-view.js`) are thin and validated by the Playwright smoke.
- **esbuild discovery.** `py/pytanga/viz/export/_offline.py::find_esbuild()`
  resolves `TANGA_ESBUILD` → `shutil.which("esbuild")` → repo
  `js/dev/node_modules/esbuild/bin/esbuild` (used only for `delivery="offline"`).
- **JS validation is local-only.** `node --test` (unit) + `node --check`
  (syntax) run in pre-commit and the PR checklist; the Playwright smoke is a
  manual script. **GitHub Actions run no JS tooling.**

## Decisions (confirmed)

- **Folder = `js/dev/`** (published artifact stays at `js/` top; no new
  `frontend/` top-level folder).
- **No JS / esbuild / Playwright in GitHub Actions** — CI stays Python-only;
  `ci.yml` (pytest, `build-viewer-js.py --check`, ruff, ty) is unchanged.
- **Unit-test-first frontend policy.** Pure logic (reconciliation, sizing,
  shaders, …) is extracted into DOM-free modules and covered by `node --test`;
  only DOM/WebGL glue is left to the browser smoke.
- **Pre-commit runs `node --test` + `node --check`** (local, node required);
  the Playwright smoke is manual.
- **esbuild/playwright remain devDependencies** in `js/dev/package.json`
  (esbuild is required by `delivery="offline"`; playwright by the manual smoke).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-consolidate-toolchain.md](./01-consolidate-toolchain.md) | Move package.json/package-lock.json to `js/dev/`, gitignore `node_modules/` |
| 2 | [02-repoint-esbuild.md](./02-repoint-esbuild.md) | Repoint `find_esbuild()` + `test_export_delivery.py` to `js/dev/node_modules` |
| 3 | [03-extract-reconciliation-core.md](./03-extract-reconciliation-core.md) | Extract the pure reconciliation/orphan-map module; refactor `build.js` |
| 4 | [04-js-tests.md](./04-js-tests.md) | `node --test` unit tests + syntax check + Playwright smoke |
| 5 | [05-pre-commit-and-pr.md](./05-pre-commit-and-pr.md) | Pre-commit runs unit + syntax (local); update PR checklist; no CI |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | README, install docs, coding-style policy, developer docs + changelog |

## Testing as you go

```bash
uv run pytest py/tests/viz -q                     # Python gate
uv run python tools/build-viewer-js.py --check    # bundle/manifest still intact
uv run mkdocs build --strict                      # docs
# JS (run in the node-equipped clone only — never in CI):
node --test js/dev/tests/*.test.mjs               # unit tests
node js/dev/tests/check-syntax.mjs                # syntax gate
node js/dev/tests/reconcile-smoke.mjs             # Playwright smoke (manual)
```

## Non-goals

- **No JS tests, esbuild, or Playwright in GitHub Actions** — `.github/workflows/*`
  is left untouched.
- **No change to `js/tanga-viewer.js` / `js/tanga-viewer.manifest.json`.**
- **No jsdom/happy-dom harness** — pure logic is extracted into DOM-free modules
  (unit-tested) and DOM/WebGL behaviour is covered by the Playwright smoke.
- **No Playwright-bundled browser download** — the smoke uses system Chrome via
  `channel: 'chrome'`.

