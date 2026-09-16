# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shared scene-graph id generation.

``generate_id()`` is the single id convention used by the scene-graph node
classes (``_nodes.py``) and the ``Scene`` registry (``scene.py``).
"""

from uuid import uuid4


def generate_id() -> str:
    """Return a fresh 8-hex-digit node id (``uuid4().hex[:8]``)."""
    return uuid4().hex[:8]
