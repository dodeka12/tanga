# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""MkDocs hook: inject TANGA_VERSION env var into config.extra.version."""

import os


def on_config(config):
    config.extra["version"] = os.environ.get("TANGA_VERSION", "dev")
