# Phase 3 — Rotor analysis for Q2 + Q3

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Add MV → `Rotor(angle, axis)` analysis for the Q2/Q3 quadric spaces and route
`geometry.analysis.analyze_operator` to it.

## Files

- Edit: `py/pytanga/quadric/_analysis.py`
- Edit: `py/pytanga/quadric/__init__.py`
- Edit: `py/pytanga/geometry/analysis.py`
- Edit: `py/pytanga/geometry/analysis_q2.py`, `py/pytanga/geometry/analysis_q3.py`
- Edit: `py/tests/geometry/test_conic_analysis.py`

## Steps

- [x] **3.1 — `quadric/_analysis.py`: add `analyze_rotor` / `analyze_operator`**
  - `analyze_rotor(mv)`: sandwich the linear basis blades (`b₁,b₂` for dim 6;
    `b₁,b₂,b₃` for dim 10) and read coefficients into a rotation matrix, then
    extract `(angle, axis)`:
    - Q2: `angle = atan2(m₁₀, m₀₀)`, `axis = Dir(0, 0, 1)`.
    - Q3: `angle = acos(clip((tr−1)/2))`, `axis = normalized dual of the skew part`
      (fall back to `Dir(0,0,1)` when the skew part is ~0; sign is ±, a
      convention).
  - `analyze_operator(mv)`: reject zero/scalar/non-versor MVs (raise `ValueError`
    or return `None` consistent with the other `analyze_operator`s); otherwise
    return `analyze_rotor(mv)`.
  - Import `Rotor`/`Direction` **lazily inside the function** (from
    `pytanga.geometry.operators` / `pytanga.entity`) — preserve the
    `quadric ↔ geometry` layering (no module-level `geometry` import).
- [x] **3.2 — Export from `quadric/__init__.py`**
  - Add `analyze_rotor` / `analyze_operator` to the `_analysis` imports and `__all__`.
- [x] **3.3 — Wire the `geometry` dispatcher + shims**
  - `geometry/analysis.py::analyze_operator`: add `elif alg_type == "q2": return
    analysis_q2.analyze_operator(mv)` and the same for `"q3"`.
  - `analysis_q2.py` / `analysis_q3.py`: re-export `analyze_operator` (and
    `analyze_rotor`) from `quadric._analysis`, add to `__all__`.
- [x] **3.4 — Tests**
  - Round-trip: `create_rotor(basis, Rotor(θ, axis))` → `analyze_operator` →
    `Rotor` with matching angle and axis (up to ± axis sign for Q3; exact for Q2).
  - `analyze()` (the combined fallback) returns the `Rotor` for a rotor MV (mixed
    grades → entity analysis raises → operator path).
  - A non-rotor MV (e.g. a plain quadric) does not misclassify as a rotor.

## Validation

`uv run pytest py/tests/geometry/test_conic_analysis.py -q`

## Notes

- `Rotor` is in `geometry.operators` (above `quadric` in the layering DAG), so the
  lazy import is required.
- The `analyze_operator` dispatcher already returns `None` (implicit) for q2/q3 —
  adding the `elif` branches is the only dispatcher change.
