# Tanga JS dev toolchain

Development tooling and tests for the Tanga frontend. The published CDN bundle
(`../tanga-viewer.js` + `../tanga-viewer.manifest.json`) lives one level up in
`js/` and must stay there — do not move it.

## Setup

Install Node.js (LTS) first:

- **Windows** — https://nodejs.org (LTS `.msi`), or
  `winget install OpenJS.NodeJS.LTS`, or nvm-windows
  (https://github.com/coreybutler/nvm-windows).
- **Linux** — nvm (`nvm install --lts`), or NodeSource
  (`curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs`),
  or your distro package.

Verify with `node --version` / `npm --version`.

Then install the JS deps (from this directory):

```bash
npm install
```

This fetches `esbuild` and the `playwright` *driver* (no browser download).
`node_modules/` is gitignored.

## Playwright

The headless smoke test uses Playwright's **bundled Chromium** (identical on
Linux and Windows). Install it once:

```bash
npx playwright install chromium
```

## Test commands

```bash
npm test          # node --test on tests/*.test.mjs (unit tests)
npm run check     # node syntax check over templates + tests
npm run smoke     # Playwright headless smoke (see below)
```

The reconciliation unit tests cover the pure `views/reconcile.js` module
(`py/pytanga/viz/templates/views/reconcile.js`) — the id/type reuse + orphan
accounting. DOM/WebGL behaviour is covered by the browser smoke.

## Headless browser smoke

1. Start a headless server (no browser opens):
   `uv run python js/dev/tests/serve-smoke.py`
2. In another terminal: `node js/dev/tests/reconcile-smoke.mjs <printed-url>`

The smoke asserts that a "Swap panes" re-push **reuses** the two scene-pane
canvases (reorders, doesn't recreate) and that a background-image swap leaves
them untouched.

## CI

JS tests, esbuild, and Playwright **never run in GitHub Actions**. They are
local-only: pre-commit (`js-test`, `js-syntax`) and the PR checklist
(`dev/workflows/pull-request.md`).
