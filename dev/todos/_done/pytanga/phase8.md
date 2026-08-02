# Phase 8 — Polish / Optional Extensions

**Overview plan:** [plan.md](plan.md)  
**Depends on:** Phase 6 (full facade), Phase 7 (tests pass)  
**Required by:** nothing — these are independent enhancements

Items within this phase are independent of each other and can be done in any
order or omitted entirely.

---

## 8.1 Named algebra convenience constructor

Add a class method `Algebra.from_name(name: str) -> Algebra` so users can
write `pytanga.Algebra.from_name("PGA3")` instead of remembering the `(dim,
sig)` tuple.

```python
# in pytanga/_algebra.py, inside class Algebra:

_NAMED_ALGEBRAS: dict[str, tuple[int, int]] = {
    "G2":   (2, 0b00),
    "G3":   (3, 0b000),
    # PGA2 / PGA3 are modelled via the null‑vector embedding
    # (see docs/py/pga_null_embedding.md). Two extra basis vectors are
    # added: one with +1, one with -1 metric.
    "PGA2": (4, 0b1000),    # dim=4, e4 squares to -1; null vector = e3 + e4
    "PGA3": (5, 0b10000),   # dim=5, e5 squares to -1; null vector = e4 + e5
    "CGA3": (5, 0b10000),   # conformal 3D: e5 squares to -1
    "STA":  (4, 0b1110),    # spacetime algebra: e2, e3, e4 square to -1
}

@classmethod
def from_name(cls, name: str, dtype: str = "float64", **kwargs) -> "Algebra":
    if name not in cls._NAMED_ALGEBRAS:
        known = ", ".join(cls._NAMED_ALGEBRAS)
        raise ValueError(f"Unknown algebra name {name!r}. Known: {known}")
    dim, sig = cls._NAMED_ALGEBRAS[name]
    return cls(dim, sig, dtype, **kwargs)
```

> **Note on null vectors:** TanGA's signature bitmask uses `1` for basis
> vectors that square to `-1`. It has no native null‑vector marker. Algebras
> like PGA that require a null vector are modelled by increasing the
> dimension by 1 and adding two extra basis vectors – one with signature
> +1, one with −1. The desired null vector is then constructed as their sum
> (see `docs/py/pga_null_embedding.md`). The table above therefore uses
> dimensions that are one larger than the usual PGA definitions, with a
> single negative‑signature bit for the additional ‑1 vector.

---

## 8.2 Batch precompile

Useful for build-time prewarming of a known set of algebras.

```python
# in pytanga/__init__.py or pytanga/_cache.py

def precompile(
    algebras: list[tuple[int, int, str]],
    *,
    max_workers: int | None = None,
    verbose: bool = False,
) -> None:
    """
    Compile a list of (dim, sig, dtype) tuples in parallel.

    Example
    -------
    pytanga.precompile([
        (3, 0, "float64"),
        (4, 0b1000, "float64"),
        (5, 0b10000, "float64"),
    ])
    """
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from pytanga._cache import get_or_build

    def _build_one(args):
        dim, sig, dtype = args
        get_or_build(dim, sig, dtype, verbose=verbose)
        return (dim, sig, dtype)

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_build_one, a): a for a in algebras}
        for future in as_completed(futures):
            dim, sig, dtype = futures[future]
            try:
                future.result()
                print(f"  compiled G({dim},{sig:#b}) dtype={dtype}")
            except Exception as exc:
                print(f"  FAILED G({dim},{sig:#b}) dtype={dtype}: {exc}")
```

> **Windows note:** `ProcessPoolExecutor` on Windows uses spawn, so all
> `pytanga` imports must be inside the worker function (already the case above
> since `get_or_build` is imported inside `_build_one`). Guard the call site
> with `if __name__ == "__main__":` when running as a script.

---

## 8.3 `SubspaceMV` — fixed-grade dense multivector

For users who know their objects live in a specific subspace (e.g., only grade-2
blades), wrapping `_CSubspaceMultivector` avoids the `std::map` overhead.

This requires a more complex binding template because the subspace dimension
`t_uSubspaceDimension` is a third template parameter.

Steps:
1. Add a `{SUBSPACE_DIM}` placeholder to a new `_template_subspace.cpp`.
2. Extend `_codegen.py` with `generate_subspace(dim, sig, dtype, subspace_dim, out_path)`.
3. Expose a `SubspaceMV` class in the generated module.
4. Add `Algebra.subspace_multivector(grade, coeffs)` factory to the facade.

Defer until the basic API is validated in production use.

---

## 8.4 Jupyter `_repr_html_` for `MV`

Adds colour-coded grade display when working in a notebook.

```python
# Add to class MV in pytanga/__init__.py:

_GRADE_COLOURS = {
    0: "#888",     # scalar — grey
    1: "#2196F3",  # grade-1 — blue
    2: "#4CAF50",  # grade-2 — green
    3: "#FF9800",  # grade-3 — orange
    4: "#9C27B0",  # grade-4 — purple
}

def _repr_html_(self) -> str:
    from pytanga._blade_names import blade_name, grade as _grade
    coeffs = self._impl.to_dict()
    if not coeffs:
        return "<span style='color:#888'>0</span>"
    parts = []
    for blade_id in sorted(coeffs, key=lambda b: (bin(b).count('1'), b)):
        val   = coeffs[blade_id]
        name  = blade_name(blade_id, self._alg.dim)
        g     = _grade(blade_id)
        colour = _GRADE_COLOURS.get(g, "#333")
        parts.append(
            f"<span style='color:{colour}'>{val}&middot;{name}</span>"
        )
    return " + ".join(parts)
```

---

## 8.5 `cppimport` alternative build path

`cppimport` (https://github.com/tbenthompson/cppimport) can handle compilation
and caching with minimal code by reading a metadata comment block from the
generated `.cpp`.

If `cppimport` is installed, an alternative workflow becomes available:

```python
# Append this block to the generated .cpp by _codegen.py when cppimport is detected:
# /*
# <%
# setup_pybind11(cfg)
# cfg['sources'] = [
#     'Tan.Math/ValuePrecision.cpp',
#     'Tan.Core/ValueFormatString.cpp',
#     'Tan.Math/Matrix.Enum.cpp',
# ]
# cfg['include_dirs'] += ['<TANGA_SOURCE>']
# cfg['compiler_args'] += ['-msse4.1', '-mpopcnt']
# %>
# */
```

Then the user can do:
```python
import cppimport
mod = cppimport.imp("binding_dim3_sig0_f64")
```

This is an optional fast-path for users who already have `cppimport` installed
and are comfortable with the cppimport workflow. The primary path (Phases 2–5)
remains independent of it.

---

## Completion check (per item)

- [x] 8.1 `Algebra.from_name("G3")` constructs correctly
- [x] 8.1 `Algebra.from_name("UNKNOWN")` raises `ValueError` with a helpful message
- [x] 8.2 `precompile([(3,0,"float64"), (4,0,"float64")])` compiles both in parallel
- [ ] 8.3 `SubspaceMV` template and codegen extension implemented (if pursued)
- [ ] 8.4 Jupyter `_repr_html_` renders colour-coded output in a notebook cell
- [ ] 8.5 `cppimport` path appended to generated `.cpp` when library is available
