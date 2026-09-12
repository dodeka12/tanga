# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Backward-compatible re-export of 3D quadric-space (Q3) creation.

The Q3 creation logic lives in :mod:`pytanga.quadric._create`; this module keeps
the ``geometry`` import path working for the creation dispatcher.
"""

from pytanga.quadric._create import (
    create_cone,
    create_cylinder,
    create_ellipsoid,
    create_entity,
    create_plane,
    create_point,
    create_quadric,
    create_rotor,
    create_sphere,
)

__all__ = [
    "create_cone",
    "create_cylinder",
    "create_ellipsoid",
    "create_entity",
    "create_plane",
    "create_point",
    "create_quadric",
    "create_rotor",
    "create_sphere",
]
