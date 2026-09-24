// Tanga — node-only syntax gate over the live frontend JS (no DOM/three run).
// Walks py/pytanga/viz/templates/**/*.js (ESM) and js/dev/tests/*.mjs and runs
// `node --check` on each. Node 22+ auto-detects ES-module syntax in `.js` files,
// so no `--input-type` flag is needed (it is not allowed with file `--check`).

import { spawnSync } from 'node:child_process';
import { readdirSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('../../..', import.meta.url));

function walk(dir, out = []) {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const path = join(dir, entry.name);
        if (entry.isDirectory()) walk(path, out);
        else if (entry.name.endsWith('.js') || entry.name.endsWith('.mjs')) out.push(path);
    }
    return out;
}

const targets = [
    ...walk(join(ROOT, 'py', 'pytanga', 'viz', 'templates')),
    ...walk(join(ROOT, 'js', 'dev', 'tests')),
];

let failed = false;
for (const file of targets) {
    // Node 22+ auto-detects ES-module syntax in `.js` files, so a plain
    // `--check` works for both the ESM templates and the `.mjs` test files.
    const result = spawnSync(process.execPath, ['--check', file], { stdio: 'inherit' });
    if (result.status !== 0) failed = true;
}

if (failed) {
    console.error('[check-syntax] one or more files failed to parse');
    process.exit(1);
}
console.log(`[check-syntax] ok (${targets.length} files)`);
