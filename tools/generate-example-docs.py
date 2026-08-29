# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Generate searchable doc pages (with embedded source) for every example.

Walk ``py/examples/`` and emit one Markdown page per example under
``docs/py/examples/``, plus per-topic index pages, a keyword index, and a nav
subtree (``_nav.json``) that the MkDocs hook injects into the site nav.

Usage::

    uv run python tools/generate-example-docs.py          # write pages
    uv run python tools/generate-example-docs.py --check  # fail on drift
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# Some example docstrings contain strings like "\p" that ast.parse warns about.
warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT / "py" / "examples"
DOCS_OUT = ROOT / "docs" / "py" / "examples"
NAV_REL = "_nav.json"
GITHUB_BASE = "https://github.com/dodeka12/tanga/blob/main"

TOPIC_TITLES = {
    "ga": "Geometric Algebra",
    "viz": "Visualization",
    "algebra": "Algebra",
    "basis": "Basis",
    "expression": "Expressions",
    "geometry": "Geometry",
    "jupyter": "Jupyter Notebooks",
    "numerics": "Numerics",
    "tensor": "Tensor",
    "animation": "Animation",
    "banners": "Banners",
    "camera": "Camera",
    "entities": "Entities",
    "export": "Export",
    "interaction": "Interaction",
    "labels": "Labels",
    "plotting": "Plotting",
    "scenes": "Scenes",
    "sdf": "SDF",
    "styling": "Styling",
}


@dataclass
class Example:
    rel: str  # e.g. "ga/algebra/algebra_demo.py"
    title: str
    description: str
    keywords: list[str]
    run_cmd: str | None
    source: str
    kind: str  # "py" | "ipynb"

    @property
    def stem(self) -> str:
        return Path(self.rel).stem

    @property
    def doc_rel(self) -> str:
        return Path(self.rel).with_suffix(".md").as_posix()


def _plain(text: str) -> str:
    """Strip RST roles and backticks for use in titles/nav labels."""
    text = re.sub(r":\w+:`([^`]+)`", r"\1", text)
    text = text.replace("``", "").replace("`", "")
    return text.strip()


def _to_markdown(text: str) -> str:
    """Convert the light RST used in docstrings to Markdown code spans."""
    text = re.sub(r":\w+:`([^`]+)`", r"`\1`", text)
    text = text.replace("``", "`")
    return text


def _md_escape(text: str) -> str:
    return text.replace("|", r"\|").replace("\n", " ")


def humanize(stem: str) -> str:
    return re.sub(r"[_-]+", " ", stem).strip().title()


def _fallback_keywords(name: str, title: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9]+", f"{Path(name).stem} {title}".lower())
    seen: list[str] = []
    for token in tokens:
        if token not in seen and len(token) > 2:
            seen.append(token)
    return seen[:6] or [Path(name).stem]


def _split_keywords(text: str) -> list[str]:
    """Split on commas but keep commas nested in parentheses (e.g. G(3,0))."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in text:
        if char in "([":
            depth += 1
        elif char in ")]":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current).strip())
    return [p for p in parts if p]


def _clean_description(lines: list[str]) -> str:
    """Keep prose lines and drop metadata (title/keywords/run-command)."""
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^Keywords:", stripped):
            continue
        if re.match(r"^Run with:", stripped) or stripped == "Run":
            continue
        if re.match(r"^-{3,}$", stripped):
            continue
        if stripped.startswith(".. "):
            continue
        if re.match(r"^uv run python\b", stripped):
            continue
        out.append(line.rstrip())
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out)


def parse_py(name: str, source: str) -> tuple[str, str, list[str], str | None]:
    """Return (title, description, keywords, run_cmd) from a .py docstring."""
    doc = (ast.get_docstring(ast.parse(source)) or "").strip()
    lines = doc.splitlines() if doc else []
    title = ""
    body = lines
    if lines:
        first = lines[0].strip()
        match = re.match(r"^(?:[\w./-]+\.py)\s*[—-]\s*(.*)$", first)
        title = match.group(1) if match else first
        body = lines[1:]
    title = _plain(title).rstrip(".").strip()

    keywords: list[str] = []
    for line in lines:
        match = re.match(r"^Keywords:\s*(.*)$", line.strip())
        if match:
            keywords = _split_keywords(match.group(1))
            break
    if not keywords:
        keywords = _fallback_keywords(name, title)

    run_cmd: str | None = None
    for line in lines:
        match = re.search(r"uv run python\s+\S+", line)
        if match:
            run_cmd = match.group(0)
            break

    return title, _clean_description(body), keywords, run_cmd


def parse_ipynb(data: dict) -> tuple[str, str, list[str]]:
    """Return (title, description, keywords) from the first markdown cell."""
    first_md = ""
    for cell in data.get("cells", []):
        if cell.get("cell_type") == "markdown":
            first_md = "".join(cell.get("source", []))
            break
    lines = first_md.splitlines()
    title = ""
    body: list[str] = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            body = lines[idx + 1 :]
            break
        if stripped:
            title = stripped
            body = lines[idx + 1 :]
            break
    title = _plain(title).rstrip(".").strip()

    keywords: list[str] = []
    for line in lines:
        match = re.match(r"^Keywords:\s*(.*)$", line.strip())
        if match:
            keywords = _split_keywords(match.group(1))
            break

    return title, _clean_description(body), keywords


def extract_notebook_code(data: dict) -> str:
    parts: list[str] = []
    for cell in data.get("cells", []):
        if cell.get("cell_type") == "code":
            source = "".join(cell.get("source", []))
            parts.append(source.rstrip("\n"))
    return "\n\n\n".join(parts)


def collect_examples() -> list[Example]:
    examples: list[Example] = []
    for path in sorted(EXAMPLES_DIR.rglob("*")):
        if "__pycache__" in path.parts or path.name.endswith(".pyc"):
            continue
        if path.suffix == ".py":
            source = path.read_text(encoding="utf-8")
            title, description, keywords, run_cmd = parse_py(path.name, source)
            examples.append(
                Example(
                    rel=path.relative_to(EXAMPLES_DIR).as_posix(),
                    title=title,
                    description=description,
                    keywords=keywords,
                    run_cmd=run_cmd,
                    source=source,
                    kind="py",
                )
            )
        elif path.suffix == ".ipynb":
            data = json.loads(path.read_text(encoding="utf-8"))
            title, description, keywords = parse_ipynb(data)
            examples.append(
                Example(
                    rel=path.relative_to(EXAMPLES_DIR).as_posix(),
                    title=title,
                    description=description,
                    keywords=keywords,
                    run_cmd=None,
                    source=extract_notebook_code(data),
                    kind="ipynb",
                )
            )
    return examples


def build_dirs(examples: list[Example]) -> dict[str, dict]:
    """Group examples by directory (key "" is the examples root)."""
    dirs: dict[str, dict] = {}
    for ex in examples:
        parts = Path(ex.rel).parts
        rel = "" if len(parts) == 1 else "/".join(parts[:-1])
        info = dirs.setdefault(rel, {"items": [], "subdirs": []})
        info["items"].append(ex)
        cur = ""
        for part in parts[:-1]:
            parent = cur
            cur = f"{cur}/{part}" if cur else part
            dirs.setdefault(cur, {"items": [], "subdirs": []})
            if parent and part not in dirs[parent]["subdirs"]:
                dirs[parent]["subdirs"].append(part)
    for info in dirs.values():
        info["items"].sort(key=lambda e: e.rel)
        info["subdirs"].sort()
    return dirs


def topic_title(dir_rel: str) -> str:
    name = Path(dir_rel).name if dir_rel else "Examples"
    return TOPIC_TITLES.get(name, name.title())


def _code_fence(source: str, lang: str = "python") -> str:
    fence = "````"
    return f"{fence}{lang}\n{source.rstrip()}\n{fence}"


def render_example_page(ex: Example) -> str:
    parts = [f"# {ex.title}", ""]
    parts.append("**Keywords:** " + " · ".join(ex.keywords))
    parts.append("")
    if ex.description:
        parts.append(_to_markdown(ex.description))
        parts.append("")
    if ex.kind == "py" and ex.run_cmd:
        parts += ["## Run", "", "```bash", ex.run_cmd, "```", ""]
    parts += ["## Source", "", f"[`{ex.rel}`]({GITHUB_BASE}/py/examples/{ex.rel})", ""]
    parts += ["## Code", ""]
    parts.append(_code_fence(ex.source))
    parts.append("")
    return "\n".join(parts)


def render_topic_index(dir_rel: str, info: dict) -> str:
    title = topic_title(dir_rel)
    parts = [f"# {title} Examples", ""]
    if info["items"]:
        parts += [
            "| Example | Keywords | Description |",
            "|---------|----------|-------------|",
        ]
        for ex in info["items"]:
            name = humanize(ex.stem)
            link = f"{ex.stem}.md"
            kws = _md_escape(", ".join(ex.keywords))
            desc = _md_escape(ex.title)
            parts.append(f"| [{name}]({link}) | {kws} | {desc} |")
        parts.append("")
    if info["subdirs"]:
        parts += ["## Sub-topics", ""]
        for sub in info["subdirs"]:
            parts.append(f"- [{topic_title(sub)}]({sub}/index.md)")
        parts.append("")
    agg = sorted({kw for ex in info["items"] for kw in ex.keywords})
    if agg:
        parts += ["## Keywords", "", " · ".join(agg), ""]
    return "\n".join(parts)


def render_root_index(examples: list[Example]) -> str:
    parts = ["# Examples", ""]
    parts.append(
        "Runnable examples grouped by topic and searchable by keyword. Run any "
        "script with:"
    )
    parts.append("")
    parts += ["```bash", "uv run python py/examples/<path>.py", "```", ""]

    kw_map: dict[str, list[Example]] = defaultdict(list)
    for ex in examples:
        for kw in ex.keywords:
            kw_map[kw].append(ex)
    parts += ["## Keyword index", ""]
    for kw in sorted(kw_map, key=str.lower):
        links = ", ".join(
            f"[{_md_escape(ex.title)}]({ex.doc_rel})" for ex in kw_map[kw]
        )
        parts.append(f"- **{kw}** — {links}")
        parts.append("")

    parts += [
        "## Topics",
        "",
        "- [Geometric Algebra](ga/index.md)",
        "- [Visualization](viz/index.md)",
        "",
    ]
    return "\n".join(parts)


class _NavNode:
    def __init__(self, name: str = "") -> None:
        self.name = name
        self.children: dict[str, "_NavNode"] = {}
        self.examples: list[Example] = []

    def child(self, name: str) -> "_NavNode":
        node = self.children.get(name)
        if node is None:
            node = _NavNode(name)
            self.children[name] = node
        return node

    def render(self, dir_rel: str) -> list:
        overview = (
            "py/examples/index.md"
            if dir_rel == ""
            else f"py/examples/{dir_rel}/index.md"
        )
        entries: list = [{"Overview": overview}]
        for ex in self.examples:
            entries.append({humanize(ex.stem): f"py/examples/{ex.doc_rel}"})
        for name in sorted(self.children):
            child_dir = f"{dir_rel}/{name}" if dir_rel else name
            entries.append({topic_title(name): self.children[name].render(child_dir)})
        return entries


def build_nav(examples: list[Example]) -> list:
    root = _NavNode()
    for ex in examples:
        node = root
        for part in Path(ex.rel).parts[:-1]:
            node = node.child(part)
        node.examples.append(ex)
    return root.render("")


def generate() -> dict[str, str]:
    examples = collect_examples()
    dirs = build_dirs(examples)
    files: dict[str, str] = {}
    for ex in examples:
        files[ex.doc_rel] = render_example_page(ex)
    for dir_rel, info in dirs.items():
        if dir_rel == "":
            continue
        files[f"{dir_rel}/index.md"] = render_topic_index(dir_rel, info)
    files["index.md"] = render_root_index(examples)
    files[NAV_REL] = json.dumps(build_nav(examples), indent=2) + "\n"
    return files


def _write(files: dict[str, str]) -> None:
    DOCS_OUT.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        path = DOCS_OUT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8"))


def _check(files: dict[str, str]) -> int:
    expected = {rel: content.encode("utf-8") for rel, content in files.items()}
    on_disk: dict[str, bytes] = {}
    if DOCS_OUT.exists():
        for path in DOCS_OUT.rglob("*"):
            if path.is_file():
                raw = path.read_bytes().replace(b"\r\n", b"\n")
                on_disk[path.relative_to(DOCS_OUT).as_posix()] = raw
    if expected == on_disk:
        print("up to date")
        return 0
    missing = sorted(set(expected) - set(on_disk))
    extra = sorted(set(on_disk) - set(expected))
    changed = sorted(
        rel for rel in set(expected) & set(on_disk) if expected[rel] != on_disk[rel]
    )
    for rel in missing:
        print(f"missing: {rel}")
    for rel in extra:
        print(f"extra: {rel}")
    for rel in changed:
        print(f"changed: {rel}")
    print("drift detected — run: uv run python tools/generate-example-docs.py")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if generated output differs from disk",
    )
    args = parser.parse_args(argv)
    files = generate()
    if args.check:
        return _check(files)
    _write(files)
    print(f"Wrote {len(files)} files to {DOCS_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
