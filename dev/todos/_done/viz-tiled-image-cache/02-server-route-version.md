# Phase 2 — Versioned tile route + no-store

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Change the tile route to `/image/{image_id}/{version}/{level}/{x}/{y}`, parse
(and ignore) the version, and stop browser-caching tiles.

## Files

- Edit: `py/pytanga/viz/server.py`
- Edit: `py/tests/viz/test_image_pyramid.py`

## Steps

- [x] **2.1 — Route path (`server.py` around line 818)**
  - Change `"/image/{image_id}/{level}/{x}/{y}"` to
    `"/image/{image_id}/{version}/{level}/{x}/{y}"`.

- [x] **2.2 — Handler (`server.py` `_image_tile_handler`, lines 833-860)**
  - Read `version = request.match_info.get("version", "0")` (do not use it to
    reject; keep serving by `image_id`). Update the docstring to mention the
    version segment.
  - Change the response header from `Cache-Control: public, max-age=3600` to
    `Cache-Control: no-store`.

- [x] **2.3 — Route tests (`test_image_pyramid.py` `TestServerRoute`)**
  - Add `"version"` to the `match_info` of the three existing requests.
  - Add an assertion that the 200 response carries `Cache-Control: no-store`.
  - Add a test that a request with a non-zero `version` still serves the tile
    (proving the version is ignored for routing).

## Validation

```bash
uv run pytest py/tests/viz/test_image_pyramid.py -q
uv run pytest py/tests/viz -q
```

## Notes

- The `/{name:.*}` catch-all is registered after the image route, so the extra
  segment stays more specific and does not change route precedence.
