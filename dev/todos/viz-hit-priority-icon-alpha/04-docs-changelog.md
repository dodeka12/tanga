# Phase 4 — Docs, branch changelog, full validation

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
> Here the architecture doc is itself the deliverable — the pick precedence and
> the texture-alpha rule are new documented contracts.

## Goal

Document the two new contracts (pick precedence, texture alpha), expose
`hit_priority` in the user docs, write the branch changelog, and run the full
gate.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `docs/py/viz/interaction/object-interaction.md`
- Edit: `docs/py/viz/entities/active-elements/act-point.md`
- New: `docs/changelog/2026/11/13_fix-hit-priority-icon-alpha.md`
- Edit: `dev/todos/viz-hit-priority-icon-alpha/README.md` (status only)

## Steps

- [x] **4.1 — Architecture doc: two subsections in `## Interactive objects`**
  - Insert after the "Active object handle controls" section (before
    `## Interaction surface`, ~line 454):
    - `### Pick precedence` — the ordered keys, stated as a contract:
      `hit_priority` desc → screen-space marker before world-space body →
      `intersect.distance` asc → input order.  Note that
      `resolveHitTarget` walks candidates in that order and still skips ones
      whose triggers do not match, so an unowned gesture falls through to the
      body/surface.  Note that `ActPoint` defaults to `10` (handles *and* bare
      points) while bodies/composites stay `0`, and that
      `viz.set_interaction(id, InteractionConfig(..., hit_priority=…))` is the
      per-entity override.  Mention that `_getInteractiveHits` attaches
      `screenSpace` from `_screenSpaceLeaf`, keeping picking consistent with
      `polygonOffset`/`renderOrder`.
    - `### Texture alpha in style and hover updates` — the `_alphaTexture`
      contract: a material whose alpha comes from a texture tags
      `material.userData._alphaTexture`; every opacity writer (`applyOpacityUpdate`
      uniform **and** generic branch in `renderers/utils.js`, plus `_applyHover`
      in `interaction.js`) derives `transparent = opacity < 1 || alphaTexture`
      and `depthWrite = opacity >= 0.99 && !alphaTexture`.  State why: the
      canonical point style always carries `opacity: 1.0`, so an untagged icon
      quad becomes opaque on any style/selection update.  Cross-reference
      `viz-architecture.md` § "Surface material".

- [x] **4.2 — User doc: `InteractionConfig` (`object-interaction.md`)**
  - Add `hit_priority=0,` to the config snippet (after `throttle_ms`, before the
    hover fields) with the comment
    `# pick precedence; higher wins (ActPoint handles use 10)`.
  - After the hover-fields paragraph, add a short **Pick precedence** paragraph:
    higher `hit_priority` wins; ties break screen-space marker → nearest →
    registration order; `ActPoint` uses `10` so handles beat the geometry they
    sit on; `0` is the body default.

- [x] **4.3 — User doc: `ActPoint` (`act-point.md`)**
  - Constructor snippet: `hit_priority: int = 10,` after `on_click`.
  - Parameter table: row `| hit_priority | int | 10 | Pick precedence against other interactive entities; lower it to let the body underneath win |`.
  - `## Interaction Configuration`: add `hit_priority=10,` to both
    `InteractionConfig(...)` snippets and one sentence saying the default makes
    the point win over an `ActLine`/`ActPolygon`/`PointPath` body it sits on.
  - Properties table `interaction_config` row: mention `hit_priority=10`.

- [x] **4.4 — Branch changelog**
  - Create `docs/changelog/2026/11/13_fix-hit-priority-icon-alpha.md`
    (`DD_<branch-name>.md`, `/`→`-`; date = branch start).
  - Title from `uv run python tools/last-release.py` →
    `# Changes since version 2.26.1 (2.27.0-rc3)`.
  - `## New Features`:
    - **`InteractionConfig.hit_priority`** — new pick-precedence field (always
      serialized, default `0`), so an app can make one interactive entity win
      over a coplanar neighbour.
  - `## Bug Fixes`:
    - **Control points beat the bodies they edit** — `ActPoint` defaults to
      `hit_priority=10` and picking ties break toward screen-space markers,
      so dragging a handle on a `PointPath`/polygon no longer grabs the body.
    - **Icon points keep their transparency** — style/selection updates and
      hover no longer clear `transparent`/`depthWrite` on a glyph-textured
      point, so `IconPointStyle` markers stay cut-out.
  - Do **not** touch `docs/changelog/index.md` (added at PR finalization) and do
    not predict a release number.

- [x] **4.5 — Final gate + plan status**
  - Run the validation below; fix any fallout inside the owning phase instead of
    papering over it here.
  - Set `**Status:** Done` in
    `dev/todos/viz-hit-priority-icon-alpha/README.md` (and tick the phase
    checkboxes) as the last edit of the branch.

## Validation

```bash
uv run pytest py/tests -q && uv run ruff check . && uv run ty check && uv run python tools/build-viewer-js.py --check && uv run mkdocs build --strict
```

## Notes

- `mkdocs build --strict` fails on broken intra-doc links and on files missing
  from `nav`; the new changelog file is picked up by the existing glob — verify
  `docs/changelog/index.md`'s existing structure is unchanged.
- Keep the architecture wording normative ("must", "always"), matching the rest
  of `viz-controls-and-interactions.md`.
- After this phase the branch is PR-ready: squash + hash-rename + index entry
  follow `dev/workflows/pull-request.md`.
