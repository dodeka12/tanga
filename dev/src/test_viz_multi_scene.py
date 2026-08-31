#!/usr/bin/env python3
"""Multi-scene visualizer smoke test — runs a blocking server with three named scenes.

Start with::

    python dev/src/test_viz_multi_scene.py

Open matching browser tabs:

    http://localhost:8765/       — main scene (empty)
    http://localhost:8765/one    — 1 red sphere
    http://localhost:8765/two    — 2 spheres (blue + green)
    http://localhost:8765/three  — 3 spheres (red + blue + green)

Press Ctrl+C to stop.
"""

import signal

from pytanga.geometry import Point, Sphere
from pytanga.viz import Visualizer


def main() -> None:
    viz = Visualizer(title="Multi-Scene Smoke Test")
    viz.start_server(port=8765)

    # Scene "one" — 1 sphere
    one = viz.scene("one")
    one.set_title("One Sphere")
    one.add(Sphere(Point(0, 0, 0), 1.0), color="#ff4444", opacity=0.6)
    one.flush()
    print(f"[smoke] scene 'one' ready → {one.url}")

    # Scene "two" — 2 spheres
    two = viz.scene("two")
    two.set_title("Two Spheres")
    two.add(Sphere(Point(-0.5, 0, 0), 0.8), color="#44aaff", opacity=0.6)
    two.add(Sphere(Point(0.5, 0, 0), 0.8), color="#44ff44", opacity=0.6)
    two.flush()
    print(f"[smoke] scene 'two' ready → {two.url}")

    # Scene "three" — 3 spheres
    three = viz.scene("three")
    three.set_title("Three Spheres")
    three.add(Sphere(Point(0, 0.5, 0), 0.6), color="#ff4444", opacity=0.6)
    three.add(Sphere(Point(-0.5, -0.4, 0), 0.6), color="#44aaff", opacity=0.6)
    three.add(Sphere(Point(0.5, -0.4, 0), 0.6), color="#44ff44", opacity=0.6)
    three.flush()
    print(f"[smoke] scene 'three' ready → {three.url}")

    print(f"\n[smoke] Scenes: {viz.list_scenes()}")
    print("[smoke] Open these URLs in your browser:")
    print(f"        {viz.url}/     (main)")
    print(f"        {viz.url}/one   (1 sphere)")
    print(f"        {viz.url}/two   (2 spheres)")
    print(f"        {viz.url}/three (3 spheres)")
    print("[smoke] Press Ctrl+C to stop.\n")

    # Block until Ctrl+C
    import threading

    stop_event = threading.Event()
    signal.signal(signal.SIGINT, lambda sig, frame: stop_event.set())
    signal.signal(signal.SIGTERM, lambda sig, frame: stop_event.set())
    stop_event.wait()

    print("\n[smoke] Shutting down …")
    viz.stop_server()
    print("[smoke] Done.")


if __name__ == "__main__":
    main()
