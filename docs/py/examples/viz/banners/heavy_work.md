# Slider that triggers a blocking computation on release

**Keywords:** banner · modal · slider · on_release · heavy work · VisualizerApp

## Run

```bash
uv run python py/examples/viz/banners/heavy_work.py
```

## Source

[`viz/banners/heavy_work.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/banners/heavy_work.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""heavy_work.py — Slider that triggers a blocking computation on release.

Run with:  uv run python py/examples/viz/banners/heavy_work.py

Keywords: banner, modal, slider, on_release, heavy work, VisualizerApp
"""

from __future__ import annotations

import asyncio
import time

from pytanga.geometry import Point, Sphere
from pytanga.viz import ControlEvent, VisualizerApp


class HeavyWorkApp(VisualizerApp):
    """A slider whose release starts a 3 s "computation".

    While the computation runs a modal banner is shown; a one-shot ``done``
    callback (on the user loop) updates the scene and removes the banner.
    """

    def __init__(self) -> None:
        super().__init__(title="Heavy work on release")
        self._sphere_id = "sphere"

    async def init(self) -> None:
        self.viz.add(
            Sphere(Point(0, 0, 0), radius=1.0),
            entity_id=self._sphere_id,
            color="#4488ff",
            opacity=0.4,
        )
        self.viz.add_slider(
            "radius",
            label="Radius",
            min=0.2,
            max=3.0,
            step=0.05,
            value=1.0,
            on_release=self.on_release,
        )
        self.viz.add_control_group(
            "controls", title="", controls=["radius"], position="bottom-right"
        )
        self.viz.flush()

    async def on_release(self, value: float, _event: ControlEvent) -> None:
        bid = await self.viz.show_banner_async(
            "## Calculating…\n\nPlease wait.",
            title="Busy",
            dismissable=False,
        )

        async def _work() -> float:
            await asyncio.to_thread(time.sleep, 3)  # simulate blocking compute
            return value

        def _done(result: float) -> None:
            self.viz.update_entity(
                self._sphere_id, Sphere(Point(0, 0, 0), radius=result)
            )
            self.viz.remove_banner(bid)
            self.viz.flush()

        self.submit_user(_work, done=_done)


if __name__ == "__main__":
    HeavyWorkApp().run()
````
