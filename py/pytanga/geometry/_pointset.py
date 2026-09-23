# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Backward-compatible re-export of the quadric point-set analysis.

The point-recovery helpers now live in :mod:`pytanga.quadric._pointset`; this
module keeps the ``geometry`` import path working.
"""

from pytanga.quadric._pointset import (
    point_from_embedding,
    pointset_from_blade,
)

__all__ = ["point_from_embedding", "pointset_from_blade"]
