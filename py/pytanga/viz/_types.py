# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Type aliases for the Tanga 3D viewer."""

from __future__ import annotations

from typing import Any, TypeAlias, Union

from pytanga.geometry.entities import Entity as GeoEntity
from pytanga.geometry.operators import Operator as GeoOperator

# Any type that can be passed to Visualizer.add()
# Note: "Any" covers the MV case — _resolve() uses duck-typing via
# pytanga.geometry.analyze() rather than isinstance checks.
VizInputType: TypeAlias = Union[GeoEntity, GeoOperator, Any]
