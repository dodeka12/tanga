# Phase 3 — Nav integration (hook + `mkdocs.yml`)

## Goal

Make every generated page discoverable: with an explicit `nav`, MkDocs only
builds (and indexes) pages listed in `nav`, so inject the Examples subtree at
build time.

## Steps

- [x] **3.1 — Hook (`docs/_hooks/examples_nav.py`)**
  - Add an `on_config` hook that reads `docs/py/examples/_nav.json` and injects
    a top-level **Examples** section (right after **Home**) into
    `config["nav"]`.
  - If `_nav.json` is missing, warn and leave nav unchanged (build still
    succeeds).

- [x] **3.2 — Wire `mkdocs.yml`**
  - Add a `hooks:` entry pointing at `docs/_hooks/examples_nav.py`.

- [x] **3.3 — Smoke**
  - Build and confirm the Examples section appears in the sidebar and search
    indexes the generated pages.

## Validation

```
uv run mkdocs build --strict
```
