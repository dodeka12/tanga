# Phase 2 — Frontend pick precedence

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
> Reference: `docs/dev/architecture/viz-controls-and-interactions.md`
> (`## Interactive objects`, `## Interaction surface`).

## Goal

Make picking honour `hit_priority` and the screen-space marker tier.  The
ordering lives in a pure helper so it is unit-testable with `node --test`;
`InteractionController` only collects candidates and delegates.

## Files

- Edit: `py/pytanga/viz/templates/hit-resolution.js`
- Edit: `py/pytanga/viz/templates/interaction.js`
- Edit: `js/dev/tests/hit-resolution.test.mjs`

## Steps

- [x] **2.1 — Pure ordering helpers (`hit-resolution.js`)**
  - Extend the module header: candidates arrive **already ordered** by
    `orderHitCandidates`, and `resolveHitTarget` walks them in that order.
  - Add above `resolveHitTarget`:
    ```js
    // Pick precedence of one interaction config.  Missing/NaN => 0, so an
    // older backend payload (no `hit_priority`) keeps today's behaviour.
    export function hitPriority(config) {
        const value = config ? config.hit_priority : 0;
        return Number.isFinite(value) ? value : 0;
    }

    // Order candidates best-first: hit_priority desc → screen-space marker
    // before world-space body → distance asc → input order (stable).
    export function orderHitCandidates(candidates, getConfig) {
        return (candidates || [])
            .map((candidate, index) => ({ candidate, index }))
            .sort((a, b) => {
                const pa = hitPriority(getConfig(a.candidate.objectId));
                const pb = hitPriority(getConfig(b.candidate.objectId));
                if (pa !== pb) return pb - pa;
                const sa = a.candidate.screenSpace ? 1 : 0;
                const sb = b.candidate.screenSpace ? 1 : 0;
                if (sa !== sb) return sb - sa;
                const da = a.candidate.intersect?.distance ?? Infinity;
                const db = b.candidate.intersect?.distance ?? Infinity;
                if (da !== db) return da - db;
                return a.index - b.index;
            })
            .map((entry) => entry.candidate);
    }
    ```
  - Update `resolveHitTarget`'s comment: `candidates` is *ordered best-first*
    (not nearest-first) and comes from `orderHitCandidates`.

- [x] **2.2 — Wire it into `_getInteractiveHits` (`interaction.js`)**
  - Import the helper: `import { matchTriggers, orderHitCandidates, resolveHitTarget } from './hit-resolution.js';`
  - In the collect loop, keep the dedupe (`seen` on `objectId`, first/best
    intersect per entity) and add the tier flag:
    ```js
    hits.push({
        objectId,
        intersect,
        screenSpace: !!this._screenSpaceLeaf(intersect.object),
    });
    ```
  - Return `orderHitCandidates(hits, (id) => this._getObjectConfig(id))`
    instead of the raw array.  Keep the existing "background planes last" mesh
    sort untouched — it now only affects which intersect wins the per-entity
    dedupe.
  - `_getInteractiveHit` needs no change: `hits[0]` is now the best candidate.

- [x] **2.3 — `node --test` coverage (`js/dev/tests/hit-resolution.test.mjs`)**
  - Import `hitPriority` and `orderHitCandidates`; add a `configs` map helper
    `getConfig = (id) => configs.get(id) ?? null`.
  - Cover:
    1. `hitPriority` returns `0` for `null`, `{}`, and a non-numeric value.
    2. priority beats distance: `[{id:'body',distance:1},{id:'handle',distance:9}]`
       with `handle.hit_priority = 10` → `['handle', 'body']`.
    3. equal priority: screen-space beats a nearer world-space hit.
    4. equal priority + equal tier: nearest distance first.
    5. full tie → input order preserved (stable).
    6. integration: `resolveHitTarget(orderHitCandidates(...), null, getConfig, 'drag', 0, new Set())`
       returns the priority-10 handle, while a `ctrl+drag` gesture the handle
       does not declare falls through to the body underneath.

## Validation

```bash
node --test js/dev/tests/hit-resolution.test.mjs && node js/dev/tests/check-syntax.mjs
```

## Notes

- `hit-resolution.js` and `interaction.js` are **not** part of the export
  renderer bundle (`_RENDERER_FILES` / `_SHARED_JS_FILES` in
  `export/_bootstrap/_html.py`), so this phase creates no `js/tanga-viewer.js`
  drift.
- Keep `orderHitCandidates` allocation-light (one `map`/`sort`/`map`) — it runs
  on every pointer move per pane.
- Screen-space detection reuses `_screenSpaceLeaf`, which already exists for
  the hover path, so the two agree on what "the marker leaf" is.
- Priority is read through `getConfig` (not baked into the candidate) so a live
  `viz.set_interaction` update takes effect without re-registering meshes.
