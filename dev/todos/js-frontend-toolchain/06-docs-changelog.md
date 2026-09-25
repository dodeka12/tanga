# Phase 6 — README, install docs, coding-style policy + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Document the JS toolchain setup (incl. Node/Playwright install on Windows and
Linux), record the unit-test-first policy in the coding-style docs, and update
the changelog.

## Files

- New: `js/dev/README.md`
- New: `docs/dev/workflows/js-frontend-testing.md`
- New: `docs/dev/guides/js-coding-style-guide.md`
- Edit: `mkdocs.yml` (nav entries)
- Edit: `docs/changelog/2026/09/24_feat-ui-layout-update.md` (append)

## Steps

- [x] **6.1 — `js/dev/README.md`**
  - Setup: `cd js/dev && npm install` (esbuild + playwright drivers, **no
    browser download**).
  - Node install pointers (Windows: nodejs.org LTS `.msi` / `winget install
    OpenJS.NodeJS.LTS` / nvm-windows; Linux: nvm / NodeSource apt / distro pkg).
  - Playwright: uses system Chrome via `channel: 'chrome'` (no
    `npx playwright install`); optional `npx playwright install chromium`.
  - Test commands: `node --test tests/*.test.mjs`, `node tests/check-syntax.mjs`,
    `node tests/reconcile-smoke.mjs`.
  - Note `js/tanga-viewer.js` is the published CDN artifact — do not move it;
    `node_modules/` is gitignored.

- [x] **6.2 — `docs/dev/workflows/js-frontend-testing.md`**
  - Same setup + test commands as the README, plus the rule that
    **JS/esbuild/playwright never run in GitHub Actions** (pre-commit + PR
    checklist only).

- [x] **6.3 — `docs/dev/guides/js-coding-style-guide.md`**
  - Coding-style policy: **pure logic goes in DOM-free modules and must be
    unit-tested with `node --test`**; keep `three`/DOM imports in the thin
    view/bootstrap layer; add a unit test alongside any new pure module.
  - Point to the `views/reconcile.js` example (reconciliation/orphan-map) as
    the reference pattern.

- [x] **6.4 — `mkdocs.yml`**
  - Add under Developer Documentation → Workflows:
    `- JS frontend testing: dev/workflows/js-frontend-testing.md`.
  - Add under Developer Documentation → Guides:
    `- JS frontend coding style: dev/guides/js-coding-style-guide.md`.

- [x] **6.5 — Changelog**
  - Append a bullet to `docs/changelog/2026/09/24_feat-ui-layout-update.md`:
    JS toolchain consolidated under `js/dev/` with `node --test` unit tests
    (reconciliation/orphan-map) + a headless smoke, wired into pre-commit and
    the PR checklist (not CI); new JS coding-style guide.

- [x] **6.6 — Validate docs**
  - `mkdocs build --strict` (new pages reachable, links resolve).

## Validation

```
uv run mkdocs build --strict
uv run python tools/generate-example-docs.py --check
uv run python tools/build-viewer-js.py --check
uv run pytest py/tests/viz -q
```

## Notes

- The `docs/changelog/index.md` entry is finalized at PR time
  (`dev/workflows/pull-request.md`); this phase only appends to the branch
  changelog.
- The coding-style guide is the durable "unit-test-first" policy; the
  `js-frontend-testing.md` workflow page is the how-to (setup + commands).

