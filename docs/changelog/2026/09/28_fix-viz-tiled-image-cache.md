# Changes since version 2.12.0

## Bug Fixes
- **Tiled background images no longer show the previous image after a same-id
  swap** — tile URLs now carry a per-`image_id` `version` that increments on
  re-registration, and tile responses use `Cache-Control: no-store`, so a
  runtime `set_background_image` on an auto-tiled photo fetches fresh tiles
  instead of stale browser-cached ones.
