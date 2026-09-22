# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The :class:`SpacerView` flexible filler pane."""

from __future__ import annotations

from ._base import View
from .._size import Size, SizeSpec


class SpacerView(View):
    """An empty, fully-flexible filler pane.

    A spacer grows to fill leftover space along a flow container's main axis:
    it defaults ``preferred_width``/``preferred_height`` to ``Size.fr(1)``,
    which the frontend maps to ``flex: 1 1 0``.  Inside a ``SplitView`` it is
    positioned absolutely, so the preferred size is inert there.
    """

    _node_type = "spacer"

    def __init__(
        self,
        *,
        size: SizeSpec = None,
        preferred_width: SizeSpec = Size.fr(1),
        preferred_height: SizeSpec = Size.fr(1),
        min_width: SizeSpec = None,
        min_height: SizeSpec = None,
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
