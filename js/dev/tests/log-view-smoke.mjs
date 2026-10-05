// Tanga — headless Playwright smoke for LogView re-push reconciliation (manual).
// Run `uv run python js/dev/tests/serve-log-smoke.py` first, then:
//   node js/dev/tests/log-view-smoke.mjs <base-url>
import { chromium } from 'playwright';

const base = process.argv[2] || process.env.SMOKE_URL;
if (!base) {
    console.error('usage: node log-view-smoke.mjs <base-url>');
    process.exit(2);
}

const browser = await chromium.launch({
    headless: true,
    args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'],
});

const consoleErrors = [];
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
page.on('pageerror', (e) => consoleErrors.push(String(e)));

await page.goto(`${base}/?view=demo`, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('.tanga-message-view', { timeout: 15000 });

const groupCollapsed = () => page.evaluate(() => {
    const content = document.querySelector('.tanga-group-content');
    return content ? content.style.display === 'none' : null;
});

// The group starts collapsed.
if ((await groupCollapsed()) !== true) {
    throw new Error('expected the group to start collapsed');
}

// Re-push the same stable log id + log a line.
await page.click('button:has-text("Re-push + log")');
await page.waitForTimeout(500);

// The new line must render in the (reused) message view.
const logText = await page.evaluate(() => {
    const view = document.querySelector('.tanga-message-view');
    return view ? view.textContent : '';
});
if (!logText.includes('after re-push')) {
    throw new Error(`expected "after re-push" in log view, got: ${JSON.stringify(logText)}`);
}

// The group must still be collapsed after the re-push.
if ((await groupCollapsed()) !== true) {
    throw new Error('expected the group to stay collapsed after re-push');
}

await browser.close();

if (consoleErrors.length) {
    console.error('console errors:', consoleErrors);
    process.exit(1);
}
console.log('log-view-smoke ok: log line rendered and group stayed collapsed across re-push');
