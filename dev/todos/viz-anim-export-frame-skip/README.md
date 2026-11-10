# Viz animated-export frame skip and in-place updates — Overview

**Created:** 2026-11-10 | **Status:** Done | **Branch:** `fix/anim-export-frame-skip`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs
> (phase 6 does this — this plan **does** extend the documented update
> contract).

## Goal

An exported (offline/inline) animated Tanga HTML must do per-frame work
proportional to the entities that actually changed in that frame — the same
granularity the live viewer gets from its patch-based renderer — instead of
rebuilding the whole scene graph on every applied frame.  Driven by
`_input/pytanga-exported-animation-rebuilds-unchanged-entities-every-frame.md`.

Four outcomes:

1. **Unchanged entities are skipped entirely.**  An entity whose source frame
   object is identical to the one already applied is left untouched (no style
   pass, no transform re-apply, no dispose/recreate) — only `visible` is
   re-asserted.
2. **Frame application is serialized.**  At most one `_playFrame` runs at a
   time; a newer request supersedes a stale one instead of queueing, so fast
   playback/scrubbing never interleaves two reconciliations.
3. **`PointPath` updates in place.**  A changing path rewrites
   `LineSegmentsGeometry` positions/colours instead of disposing and recreating
   the mesh.
4. **`Axis` / `Axes2D` / `Axes3D` / `Grid` update in place.**  A changing axis
   or grid refills its existing group (new line + CSS2D value labels) or
   rewrites its segment positions, instead of rebuilding the entity — including
   its label DOM tree.

## Architecture (short)

- The animated bootstrap expands the delta recording (`_expandFrames`) into
  full `frames[]` **once at load**; the map-backed expander keeps the *same
  object instance* for every entity that did not change in a frame.  So
  "did this entity change?" is recoverable with `===` — the information exists
  today but `_reconcileFrame` throws it away by treating every entity as
  changed.
- `py/pytanga/viz/export/_bootstrap/_animation.py` → `js_reconcile_frame`
  emits `_reconcileFrame` (create / in-place update / rebuild / hide) and
  `_playFrame`; `js_animated_render_loop` emits `_figAnimate`.
- `templates/renderers/factory.js::updateEntityMesh` dispatches per kind;
  `utils.js::entityRequiresRebuild` is the flat field-list fallback.
  `point_path.js::updatePointPath` returns `false` unconditionally;
  `entityRequiresRebuild` returns `true` unconditionally for `PointPath`,
  `Axis`, `Axes2D`, `Axes3D` and `Grid` — those are the five rebuild sources.
- New pure module `templates/frame-pump.js` owns the serialization; it is
  registered in `_html.py::_SHARED_JS_FILES` (inline bundle, `export` stripped)
  and in `_scene.py::_TANGA_BRIDGE_SYMBOLS` (so the bootstrap can reach it),
  following the `views/reconcile.js` + `js/dev/tests/reconcile.test.mjs`
  precedent (pure module → `node --test` coverage).

### Fixed contract (do not change across phases)

**1. Applied-entity identity** — the last applied source object is remembered on
the *mesh* (self-clearing with the mesh, no new map, no new declarations):

```js
// inside _reconcileFrame, after the create branch, before `const prev = …`
if (mesh.userData._src === ent) {
    mesh.visible = true;          // a hidden frame in between must not stick
    continue;
}
```

`mesh.userData._src = ent` is assigned in **all four** apply paths (create,
in-place update, image rebuild, generic rebuild).  The hide loop is unchanged:
it only flips `visible`, so `_src` survives a hidden frame and a returning
entity is compared against the object it was last built from.

**2. Frame pump** — `createFramePump(apply, onError)` returns:

```text
{
    request(n) -> Promise<void>,  // fire-and-forget; resolves when the pump is
                                 // next idle (coalesced requests resolve too)
    get busy() -> boolean,
    idle() -> Promise<void>,      // resolves immediately when idle
}
```

Rules: exactly one `apply` in flight; a request made while running replaces the
pending target (newest wins, stale target dropped); `apply` must never be
re-entered from inside itself (a request issued by `apply` is queued, not
recursed); a rejecting `apply` is reported to `onError`, clears the pending
target and returns the pump to idle.  Callers: `_figAnimate` uses
`request()` (ignores the promise), `_onScrub` awaits it, `_togglePlay`'s
restart uses it.

**3. Updater contract (`update<Kind>(mesh, ent, prev)`)** — extended (this is
the documented-architecture change, written up in phase 6):

- a kind-specific updater may now **rewrite geometry in place** and return
  `true` — not only restyle an already-correct mesh;
- an updater must not return `false` for a content change it can apply;
  `false` means "rebuild is genuinely cheaper or the representation changes"
  (e.g. a thick-line ↔ cylinder style switch, a coloured ↔ uniform path);
- `styleNeedsRebuild(ent, prev)` stays the style gate everywhere;
- `entityRequiresRebuild` keeps its flat field list for the kinds that have no
  updater, and loses the blanket `PointPath` / `Axis` / `Axes2D` / `Axes3D` /
  `Grid` short-circuits because those kinds now own that decision.

## Decisions (confirmed)

- **Scope**: full incremental rendering — core fixes (phases 2–3) **plus**
  in-place `PointPath` and `Axis/Axes2D/Axes3D/Grid` updates (phases 4–5).  The
  user explicitly approved extending the documented `update<Kind>` contract.
- **Identity on `mesh.userData._src`**, not a side `Map` keyed by id: it dies
  with the mesh, needs no new bootstrap declarations, and works for both the
  scene and overlay branches.
- **Frame pump extracted to a pure module** and unit-tested with `node --test`
  (no DOM, no three.js) instead of inlining it in the bootstrap string.
- **No production instrumentation** for measurement: the smoke wraps
  `window.__tanga` via `page.addInitScript` *before* the adapter destructures
  it, so the export carries no counters.
- **Legacy full-`frames` recordings keep today's behaviour** (no object
  identity ⇒ no skip).  Adding a content hash for that encoding is out of
  scope.
- **Smoke harness is the behavioural gate** for phases 2/4/5; node unit tests
  cover only DOM-free modules, Python tests cover the emitted-JS structure
  (three.js is not installed in `js/dev/node_modules`, so renderer modules
  cannot be imported by `node --test`).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-export-anim-smoke.md](./01-export-anim-smoke.md) | Animated-export smoke generator + Playwright harness; capture the rebuild baseline |
| 2 | [02-reconcile-applied-skip.md](./02-reconcile-applied-skip.md) | Skip entities whose source object is unchanged (`mesh.userData._src`) |
| 3 | [03-frame-pump-serialization.md](./03-frame-pump-serialization.md) | `frame-pump.js` + `frame-pump.test.mjs`; serialize playback/scrub |
| 4 | [04-in-place-point-path.md](./04-in-place-point-path.md) | `updatePointPath` rewrites fat-segment geometry in place |
| 5 | [05-in-place-axis-grid.md](./05-in-place-axis-grid.md) | In-place `Axis` / `Axes2D` / `Axes3D` / `Grid` updates; narrow `entityRequiresRebuild` |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Architecture doc (`expand → reconcile` + extended updater recipe) + branch changelog |

## Testing as you go

Every phase ends with its own `## Validation` command.  The full fan-out:

```bash
uv run pytest py/tests/viz -q                  # Python (export bootstrap + tests)
cd js/dev && npm test                          # node --test (pure modules)
cd js/dev && npm run check                     # syntax check, live frontend + tests
uv run python js/dev/tests/serve-anim-export-smoke.py   # terminal 1 (exported HTML)
node js/dev/tests/anim-export-smoke.mjs <url>           # terminal 2 (Playwright)
uv run mkdocs build --strict                   # docs (phase 6)
```

The smoke needs network access for the `three` addon imports (CDN) — like any
`delivery="inline"` export; the tanga library itself is inlined.

## Non-goals

- Changing the delta wire format, or adding a content hash so *legacy*
  full-`frames` recordings also skip unchanged entities.
- The live viewer's render loop / `views/three-view.js` patch path (it already
  patches granularly; only `updatePointPath` / axis-grid updaters are shared).
- The `image` entity rebuild path (pixel content is per-frame by design).
- Reducing the *stored* size of `deltas` further (static entities are already
  stored once).
- Introducing a WebGL resource pool / mesh cache beyond what the rebuild paths
  already do.

