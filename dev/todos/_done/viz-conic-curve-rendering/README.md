# Conic Curve Rendering Fixes — Overview

**Created:** 2026-09-12 | **Status:** Done | **Branch:** `feat/quadric-space`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs. Relevant
> today: `docs/dev/architecture/viz-architecture.md` ("New entity kind" recipe —
> frontend renderer + factory dispatch), and the existing per-kind `update*`
> pattern in `templates/renderers/*.js`.

## Goal

Fix the live-editing and rendering of the 2D conic curves in the viewer:

1. **Hyperbolas/parabolas stop updating** after the first occurrence — the
   rebuild decision is a flat, kind-agnostic field list that doesn't know the
   conic curve fields (`a`/`b`/`dir1`/`dir2`, `vertex`/`p`).
2. **Curves drawn "to infinity"** — the renderers clip the *parameter* `t`, not
   the spatial extent, and the extent default is hardcoded in JS rather than
   backend-driven.
3. **Only one hyperbola branch** is drawn.
4. **The origin case renders as two half-rays**, not two crossing lines (line
   pairs aren't centered).

## Architecture (short)

- **Frontend renderers** are module-per-kind (`templates/renderers/<kind>.js`)
  with `create<Kind>` and, for kinds that update in place, `update<Kind>`
  (`line.js`, `arc.js`, `cylinder.js`, …).  The factory
  (`factory.js::createEntityMesh` / `updateEntityMesh`) dispatches on
  `ent.kind`.  `utils.js::entityRequiresRebuild` is currently a flat,
  kind-agnostic field list used by the generic update path.
- **Backend styles** (`_styles/__init__.py::_DEFAULT_STYLE_FOR_KIND`) carry the
  canonical per-kind defaults; the frontend reads them via `styleParam`.
  `Line` already sets its infinite length here (`LineStyle.length = 20.0`).
- **Serializers** (`serializer.py`) emit the wire dicts; `_serialize_line`
  centers infinite lines (shifts the origin back by `length/2`), but
  `_serialize_line_pair` / `_serialize_parallel_line_pair` do not.

## Wire contract (fixed up front)

- Hyperbola: `{"kind":"Hyperbola","center","dir1","dir2","a","b"}` + style
  `{"style_type":"HyperbolaStyle","extent":5.0,…}` where `extent` is a
  **spatial half-size**.
- Parabola: `{"kind":"Parabola","vertex","direction","p"}` + style
  `{"style_type":"ParabolaStyle","extent":5.0,…}`.
- LinePair / ParallelLinePair: each member line emitted **centered**, as
  `{"origin":<shifted by -length/2·dir>,"direction","length"}` so the frontend
  draws `±length/2` through the line's point (default `length = 20.0`).

## Decisions (confirmed)

- Rebuild detection becomes **object-oriented**: each renderer module owns an
  `update<Kind>(mesh, ent, prev)` that checks *its own* geometry fields and
  returns `false` (rebuild) when they change; `entityRequiresRebuild` shrinks to
  the shared kind/style checks.
- `extent` (hyperbola/parabola) is a **spatial half-size** with a backend default
  of `5.0` (matching the demo's ±5 axes/grid), set in `_DEFAULT_STYLE_FOR_KIND`
  — the same mechanism `LineStyle.length` uses.
- The hyperbola draws **both** branches, clipped spatially.
- Line-pair member lines are centered like standalone `Line`s.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-style-defaults-line-pair-centering.md](./01-python-style-defaults-line-pair-centering.md) | Backend extent defaults + centered line pairs |
| 2 | [02-frontend-oo-rebuild.md](./02-frontend-oo-rebuild.md) | Per-kind `update*` + factory dispatch |
| 3 | [03-frontend-spatial-clip-branches.md](./03-frontend-spatial-clip-branches.md) | Spatial clipping + both hyperbola branches |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Docs + changelog + regression |

## Testing as you go

- Python: `uv run pytest py/tests/geometry py/tests/viz -q` (then full
  `uv run pytest -q`).
- JS: `node --check py/pytanga/viz/templates/renderers/<file>` per touched
  renderer; `uv run pytest py/tests/viz/test_export_renderers.py -q` keeps the
  export bundle in lockstep.
- Docs: `uv run mkdocs build --strict`.

## Non-goals

- Dimension-aware 2D/3D default styles (separate idea, `dev/notes/`).
- General 3D quadric intersection analysis.
- SDF fallback for the conic curves.
