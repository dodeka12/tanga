# Phase 2 — `pinhole-framing.js` (frustum + letterbox math)

## Goal

Replace `pinhole-projection.js` with a single pure module that computes, for a
given pane aspect and `fit` policy, both the off-center frustum bounds and the
background quad's letterbox half-extents. One source of truth for aspect.

## Files

- New: `py/pytanga/viz/templates/pinhole-framing.js`
- Edit: `py/tests/viz/test_pinhole_math.py`
- (Phase 3 deletes `py/pytanga/viz/templates/pinhole-projection.js` after `view_mode.js` is rewired)

## Steps

- [x] **2.1 — `pinholeFraming(fx, fy, cx, cy, width, height, near, far, paneAspect, fit)`**
  - Compute the base frustum (`left=-cx·near/fx`, `right=(W-cx)·near/fx`,
    `top=cy·near/fy`, `bottom=-(H-cy)·near/fy`).
  - `fit === "fill"` → `{hx: 1, hy: 1}` and the base frustum unchanged.
  - `fit === "fit"` (default) → `A = W/H`, `a = paneAspect`; expand the
    letterboxed axis so the image aspect is preserved: if `a > A` expand
    horizontally by `a/A` around the horizontal centre, else expand vertically
    by `A/a` around the vertical centre; return `{hx: min(1, A/a), hy: min(1, a/A)}`.
  - Return `{ left, right, top, bottom, hx, hy }`.

- [x] **2.2 — Node tests**
  - Extend `test_pinhole_math.py`: `fit="fill"` reproduces the old
    `pinholeFrustum` bounds; `fit="fit"` letterboxes (project a known point and
    check the pixel, and check `hx/hy`).

## Validation

`uv run pytest py/tests/viz/test_pinhole_math.py -q && node --check py/pytanga/viz/templates/pinhole-framing.js`

## Notes

- Keep it `three`/DOM-free so Node can import it (mirror `camera-fit.js`).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
