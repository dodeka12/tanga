// Diagnose why the last column/row of an embedded Tabulator table is not
// editable by double-click in an auto-sized overlay, while it works in a
// SplitView.  Spawns the example app, reads its URL from stdout, then reports
// geometry + hit-testing for every cell and performs a real double-click.

import { spawn } from 'node:child_process';
import { chromium } from 'playwright';

const example = process.argv[2] || 'py/examples/viz/ui/controls/table_editing.py';

// 1. Start the app and read its URL from stdout.
const child = spawn('uv', ['run', 'python', example], { stdio: ['ignore', 'pipe', 'pipe'] });
let url = null;
child.stdout.on('data', (d) => {
  const t = d.toString();
  process.stdout.write(t);
  const m = t.match(/https?:\/\/[^\s"'<>]+/);
  if (m && !url) url = m[0];
});
child.stderr.on('data', (d) => process.stderr.write(d));

const t0 = Date.now();
while (!url && Date.now() - t0 < 60000) await new Promise((r) => setTimeout(r, 200));
if (!url) { console.error('No URL found in app output'); process.exit(1); }
console.error('URL:', url);

// 2. Launch system Chrome (no download) with fallback to bundled chromium.
let browser;
try { browser = await chromium.launch({ channel: 'chrome', headless: true }); }
catch (e) { console.error('system chrome failed, using bundled chromium:', e.message); browser = await chromium.launch({ headless: true }); }

const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto(url);
await page.waitForSelector('.tabulator-cell', { timeout: 30000 });
await page.waitForTimeout(1500); // let ResizeObserver -> redraw settle

// 3. Geometry + hit-test report.
const report = await page.evaluate(() => {
  const grid = document.querySelector('.tabulator');
  const holder = grid.querySelector('.tabulator-tableholder');
  const rect = (el) => el ? (() => { const r = el.getBoundingClientRect(); return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height }; })() : null;

  const cells = [...grid.querySelectorAll('.tabulator-cell')].map((cell) => {
    const r = cell.getBoundingClientRect();
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    const hit = document.elementFromPoint(cx, cy);
    return {
      field: cell.getAttribute('tabulator-field'),
      text: cell.textContent,
      rect: rect(cell),
      center: { x: cx, y: cy },
      hitElement: hit ? (hit.className || hit.tagName) : null,
      hitIsCellOrChild: !!hit && (cell === hit || cell.contains(hit)),
    };
  });

  return {
    layers: {
      tanga_control_view: rect(grid.closest('.tanga-control-view')),
      tanga_table: rect(grid.closest('.tanga-table')),
      tabulator_container: rect(grid),
      tabulator_tableholder: rect(holder),
      tabulator_table: rect(holder.querySelector('.tabulator-table')),
    },
    tableholder: {
      clientWidth: holder.clientWidth, scrollWidth: holder.scrollWidth,
      clientHeight: holder.clientHeight, scrollHeight: holder.scrollHeight,
      hOverflowPx: holder.scrollWidth - holder.clientWidth,
      vOverflowPx: holder.scrollHeight - holder.clientHeight,
      overflowX: getComputedStyle(holder).overflowX,
      overflowY: getComputedStyle(holder).overflowY,
    },
    container: {
      clientWidth: grid.clientWidth, scrollWidth: grid.scrollWidth,
      clientHeight: grid.clientHeight, scrollHeight: grid.scrollHeight,
    },
    cells,
  };
});
console.log('=== GEOMETRY ===');
console.log(JSON.stringify(report, null, 2));

// 4. Real double-click at each cell center; check if an editor opened.
console.log('=== REAL DBLCLICK ===');
const results = [];
for (const cell of report.cells) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(120);
  await page.mouse.dblclick(cell.center.x, cell.center.y);
  await page.waitForTimeout(150);
  const state = await page.evaluate(() => {
    const e = document.querySelector('.tabulator-cell.tabulator-editing');
    return e ? { opened: true, field: e.getAttribute('tabulator-field') } : { opened: false };
  });
  results.push({ field: cell.field, text: cell.text, ...state });
}
console.log(JSON.stringify(results, null, 2));

await browser.close();
child.kill('SIGINT');
