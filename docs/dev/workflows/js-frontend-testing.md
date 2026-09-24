# JS frontend testing

How to set up and run the JavaScript frontend toolchain (`js/dev/`). The
published CDN bundle (`js/tanga-viewer.js`) lives next to this toolchain but is
a build artifact — see `tools/build-viewer-js.py`.

## Install Node.js

- **Windows** — nodejs.org LTS `.msi`; `winget install OpenJS.NodeJS.LTS`; or
  nvm-windows (https://github.com/coreybutler/nvm-windows).
- **Linux** — nvm (`nvm install --lts`); NodeSource
  (`curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs`);
  or the distro package.

Verify with `node --version` / `npm --version`.

## Install the JS deps

```bash
cd js/dev
npm install                        # esbuild + playwright driver
npx playwright install chromium    # the browser (once)
```

`node_modules/` is gitignored.

## Run the checks

```bash
cd js/dev
npm test             # node --test unit tests (reconciliation/orphan map, …)
npm run check        # node syntax check over the live frontend + tests
```

For layout/frontend changes, also run the manual browser smoke:

```bash
uv run python js/dev/tests/serve-smoke.py        # terminal 1 (headless server)
node js/dev/tests/reconcile-smoke.mjs <url>      # terminal 2 (system Chrome)
```

The smoke uses Playwright's bundled Chromium (headless, SwiftShader flags for
software WebGL) — the same browser on Linux and Windows.

## GitHub Actions

JS tests, esbuild, and Playwright **do not run in GitHub Actions** (CI is
Python-only). They run locally via pre-commit (`js-test`, `js-syntax`) and the
PR checklist (`dev/workflows/pull-request.md`).

## Coding style

Pure frontend logic must live in DOM-free modules and be unit-tested with
`node --test` — see
[JS frontend coding style](../guides/js-coding-style-guide.md).
