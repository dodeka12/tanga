# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Backward-compatible re-export of 2D conic-space (Q2) creation.

The Q2 creation logic lives in :mod:`pytanga.quadric._create`; this module keeps
the ``geometry`` import path working for the creation dispatcher.
"""

from pytanga.quadric._create import (
    create_circle,
    create_conic,
    create_ellipse,
    create_entity,
    create_hyperbola,
    create_line,
    create_line_pair,
    create_parabola,
    create_parallel_line_pair,
    create_point,
    create_rotor,
)

__all__ = [
    "create_circle",
    "create_conic",
    "create_ellipse",
    "create_entity",
    "create_hyperbola",
    "create_line",
    "create_line_pair",
    "create_parabola",
    "create_parallel_line_pair",
    "create_point",
    "create_rotor",
]
