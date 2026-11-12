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

const groupLayout = () => page.evaluate(() => {
    const title = [...document.querySelectorAll('.tanga-group-title')]
        .find((el) => el.textContent === 'Layout probe');
    const group = title ? title.closest('.tanga-group') : null;
    const content = group
        ? group.querySelector(':scope > .tanga-group-content')
        : null;
    if (!content) return null;
    const children = [...content.children];
    const first = children[0] ? children[0].getBoundingClientRect() : null;
    const second = children[1] ? children[1].getBoundingClientRect() : null;
    return {
        display: getComputedStyle(content).display,
        gap: first && second ? second.top - first.bottom : null,
    };
});

const assertProbeLayout = async (phase) => {
    const layout = await groupLayout();
    if (!layout) {
        throw new Error(`expected the "Layout probe" group to exist ${phase}`);
    }
    if (layout.display !== 'flex') {
        throw new Error(
            `expected the expanded group content to use display:flex ${phase}, got ${layout.display}`
        );
    }
    if (layout.gap == null || Math.abs(layout.gap - 12) > 1) {
        throw new Error(
            `expected a 12px gap between the probe buttons ${phase}, got ${layout.gap}`
        );
    }
};

// The group starts collapsed and the probe starts expanded.
if ((await groupCollapsed()) !== true) {
    throw new Error('expected the group to start collapsed');
}
await assertProbeLayout('on initial load');

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

// The group must still be collapsed after the re-push, and the expanded probe
// must keep its flex layout (the collapse helper must not clear it).
if ((await groupCollapsed()) !== true) {
    throw new Error('expected the group to stay collapsed after re-push');
}
await assertProbeLayout('after re-push');

await browser.close();

if (consoleErrors.length) {
    console.error('console errors:', consoleErrors);
    process.exit(1);
}
console.log(
    'log-view-smoke ok: log line rendered, group stayed collapsed, and probe group kept flex layout across re-push'
);
