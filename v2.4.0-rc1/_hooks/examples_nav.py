# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""MkDocs hook: inject the generated Examples section into the site nav.

Reads ``docs/py/examples/_nav.json`` (produced by
``tools/generate-example-docs.py``) and inserts a top-level "Examples" section
right after "Home" so every generated page is built and indexed by search.
"""

import json
import logging
from pathlib import Path

log = logging.getLogger("mkdocs")

_NAV_JSON = Path(__file__).resolve().parent.parent / "py" / "examples" / "_nav.json"


def on_config(config, **kwargs) -> None:
    if not _NAV_JSON.exists():
        log.warning("Examples nav missing (%s); skipping Examples section", _NAV_JSON)
        return
    subtree = json.loads(_NAV_JSON.read_text(encoding="utf-8"))
    nav = config.get("nav") or []
    if any(isinstance(entry, dict) and "Examples" in entry for entry in nav):
        return
    nav.insert(1, {"Examples": subtree})
