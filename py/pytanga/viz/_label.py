# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Label dataclass for the Tanga 3D viewer.

Labels are first-class viz objects that exist independently of entities.
They can be positioned at absolute world coordinates or attached to an
entity via ``parent_id``.

The label anchor position is computed by ``_label_anchor.compute_label_anchor``
/ ``_label_frame.compute_label_position``.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._styles import LabelStyle


@dataclass
class Label:
    """A text annotation positioned in 3D space.

    Can be added to the scene independently, or created automatically
    by ``Visualizer.add()`` when a ``label`` string is provided.
    """

    text: str
    position: tuple[float, float, float]
    parent_id: str | None = None
    style: LabelStyle | None = None
