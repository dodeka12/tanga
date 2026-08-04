# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""MkDocs hook: resolve tanga-py version and inject into config.extra.version.

Priority:
  1. TANGA_VERSION env var (set by CI)
  2. importlib.metadata (editable install / installed wheel)
  3. "dev" fallback
"""

import importlib.metadata
import os


def on_config(config):
    version = os.environ.get("TANGA_VERSION") or _resolve_version()
    # Preserve existing version config (e.g. provider: mike) and only set the version string
    if isinstance(config.extra.get("version"), dict):
        config.extra["version"]["version"] = version
    else:
        config.extra["version"] = version


def _resolve_version() -> str:
    try:
        return importlib.metadata.version("tanga-py")
    except importlib.metadata.PackageNotFoundError:
        return "dev"
