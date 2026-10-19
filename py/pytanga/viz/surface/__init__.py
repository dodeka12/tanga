# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Surface material model and standard surface shaders.

This subpackage holds the Python side of surface texture mapping and custom
surface shaders.  The frontend assets live alongside under
``templates/renderers/surface-shader.js`` / ``surface-material.js``.
"""

from __future__ import annotations

from .material import SurfaceMaterial, SurfaceShader, SurfaceTexture, surface_material
from .standard import checkerboard, gradient, grid, sphere_coloring

__all__ = [
    "SurfaceMaterial",
    "SurfaceShader",
    "SurfaceTexture",
    "checkerboard",
    "gradient",
    "grid",
    "sphere_coloring",
    "surface_material",
]
