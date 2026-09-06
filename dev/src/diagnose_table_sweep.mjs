// Fast single-page sweep of viewport size + CSS zoom to find where the last
// column/row of an embedded Tabulator table stops being editable.

import { spawn } from 'node:child_process';
import { chromium } from 'playwright';

const example = process.argv[2] || 'py/examples/viz/ui/controls/table_editing.py';

const child = spawn('uv', ['run', 'python', example], { stdio: ['ignore', 'pipe', 'ignore'] });
let url = null;
child.stdout.on('data', (d) => {
  const m = d.toString().match(/https?:\/\/[^\s"'<>]+/);
  if (m && !url) url = m[0];
});
const t0 = Date.now();
while (!url && Date.now() - t0 < 60000) await new Promise((r) => setTimeout(r, 200));
if (!url) { console.error('No URL found'); process.exit(1); }

let browser;
try { browser = await chromium.launch({ channel: 'chrome', headless: true }); }
catch { browser = await chromium.launch({ headless: true }); }

const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
const page = await ctx.newPage();
await page.goto(url);
await page.waitForSelector('.tabulator-cell', { timeout: 30000 });

async function measure() {
  await page.waitForTimeout(300);
  return page.evaluate(() => {
    const grid = document.querySelector('.tabulator');
    if (!grid) return { ready: false };
    const holder = grid.querySelector('.tabulator-tableholder');
    const cells = [...grid.querySelectorAll('.tabulator-cell')];
    const last = cells[cells.length - 1];
    const r = last.getBoundingClientRect();
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    const hit = document.elementFromPoint(cx, cy);
    const zoom = getComputedStyle(document.documentElement).zoom || '1';
    return {
      ready: true,
      hO: holder.scrollWidth - holder.clientWidth,
      vO: holder.scrollHeight - holder.clientHeight,
      cw: holder.clientWidth, sw: holder.scrollWidth,
      ch: holder.clientHeight, sh: holder.scrollHeight,
      lastW: r.width, lastH: r.height,
      hitLast: last === hit || last.contains(hit),
      zoom,
    };
  });
}

async function dblLast() {
  return page.evaluate(async () => {
    const cells = [...document.querySelectorAll('.tabulator-cell')];
    const last = cells[cells.length - 1];
    const r = last.getBoundingClientRect();
    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    hit.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true, view: window }));
    await new Promise((res) => setTimeout(res, 60));
    const e = document.querySelector('.tabulator-cell.tabulator-editing');
    return !!e;
  });
}

console.log('cells-before-loop', await page.evaluate(() => document.querySelectorAll('.tabulator-cell').length));
console.log('size\tzoom\thO\tvO\tcw/sw\tch/sh\tlastWxH\thitLast\tdbl');
for (const [w, h] of [[800,600],[900,700],[1000,700],[1100,700],[1280,720],[1280,800],[1366,768],[1440,900],[1600,900],[1920,1080]]) {
  await page.setViewportSize({ width: w, height: h });
  const m = await measure();
  if (!m.ready) { console.log(`${w}x${h}\tNOT-READY\t${JSON.stringify(m)}`); continue; }
  const d = await dblLast();
  console.log(`${w}x${h}\t${m.zoom}\t${m.hO}\t${m.vO}\t${m.cw}/${m.sw}\t${m.ch}/${m.sh}\t${m.lastW}x${m.lastH}\t${m.hitLast}\t${d}`);
}

for (const z of [0.9, 1.1, 1.2, 1.25, 1.33, 1.5]) {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.evaluate((v) => { document.documentElement.style.zoom = String(v); }, z);
  const m = await measure();
  if (!m.ready) continue;
  const d = await dblLast();
  console.log(`zoom${z}\t${m.zoom}\t${m.hO}\t${m.vO}\t${m.cw}/${m.sw}\t${m.ch}/${m.sh}\t${m.lastW}x${m.lastH}\t${m.hitLast}\t${d}`);
  await page.evaluate(() => { document.documentElement.style.zoom = ''; });
}

await browser.close();
child.kill('SIGINT');
