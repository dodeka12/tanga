# Changes since version 2.22.0 (2.23.0-rc3)

## Bug Fixes

- **Screen-space point markers stay concentric at pixel zoom** — flat
  screen-space markers (circle/icon) no longer lift themselves by a fixed
  world-space `z` offset (which slid relative to the standard point under a
  pinhole camera); they now layer above coplanar bodies with `renderOrder` +
  `polygonOffset`.

- **Hover scaling no longer compounds** — the hover scale is stored as a
  multiplier on the screen-space marker leaf (`userData._hoverScale`) and folded
  into the per-frame screen-space scale, instead of mutating `scale` directly
  and leaking its restore state across re-hovers.  Hover is also reset when an
  interactive object is unregistered or all interactives are cleared.

## Refactor

- **Screen-space marker contract** — the screen-space tag and layering are
  centralized in `renderers/utils.js::tagScreenSpaceMarker`; the marker leaf
  owns its `scale` and hover multiplier while the wrapper group keeps only the
  entity transform.
