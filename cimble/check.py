"""Growth checks for CLAUDE.md / memory/*.md: whole-file backstop, per-section threshold,
backlink integrity, and (optionally) wikilinks."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .config import DEFAULT_FILE_THRESHOLD, DEFAULT_SECTION_THRESHOLD

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
FRONTMATTER_NAME_RE = re.compile(r"^name:\s*(\S+)", re.MULTILINE)
BACKLINK_RE = re.compile(r"^↑\s+(\S+)\s*$")

_MAX_CHAIN_DEPTH = 10


def _count_lines(path: Path) -> int:
    with path.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


def _first_nonempty_line(text: str) -> str | None:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return None


def find_claude_md_files(root: Path) -> list[Path]:
    return sorted(root.rglob("CLAUDE.md"))


def find_memory_files(root: Path) -> list[Path]:
    memory_root = Path(root) / "memory"
    if not memory_root.is_dir():
        return []
    return sorted(memory_root.rglob("*.md"))


# --- whole-file backstop ----------------------------------------------------


@dataclass
class ThresholdFinding:
    path: Path
    kind: Literal["claude_md", "memory"]
    lines: int
    threshold: int

    @property
    def status(self) -> Literal["ok", "over"]:
        return "over" if self.lines > self.threshold else "ok"

    @property
    def hint(self) -> str:
        if self.status == "ok":
            return ""
        return "over the whole-file backstop — carve an oversized section into memory/<topic>.md (see docs/methodology.md)"


def check_thresholds(
    root: Path,
    file_threshold: int = DEFAULT_FILE_THRESHOLD,
) -> list[ThresholdFinding]:
    root = Path(root)
    findings = [
        ThresholdFinding(path, "claude_md", _count_lines(path), file_threshold)
        for path in find_claude_md_files(root)
    ]
    findings += [
        ThresholdFinding(path, "memory", _count_lines(path), file_threshold)
        for path in find_memory_files(root)
    ]
    return findings


def check_file(
    path: Path,
    file_threshold: int = DEFAULT_FILE_THRESHOLD,
) -> ThresholdFinding | None:
    path = Path(path)
    if not path.is_file():
        return None
    if path.name == "CLAUDE.md":
        return ThresholdFinding(path, "claude_md", _count_lines(path), file_threshold)
    if "memory" in path.parts and path.suffix == ".md":
        return ThresholdFinding(path, "memory", _count_lines(path), file_threshold)
    return None


# --- per-section threshold ---------------------------------------------------


@dataclass
class SectionFinding:
    path: Path
    heading: str
    lines: int
    threshold: int

    @property
    def status(self) -> Literal["ok", "over"]:
        return "over" if self.lines > self.threshold else "ok"

    @property
    def hint(self) -> str:
        if self.status == "ok":
            return ""
        return (
            "this section is long enough to carve into its own memory/<topic>.md — unless it's "
            "frequently-used operational content (see the frequency exception in docs/methodology.md)"
        )


def _sections(text: str) -> list[tuple[str, int]]:
    heading: str | None = None
    count = 0
    out: list[tuple[str, int]] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if heading is not None:
                out.append((heading, count))
            heading = line[3:].strip()
            count = 0
        elif heading is not None:
            count += 1
    if heading is not None:
        out.append((heading, count))
    return out


def check_sections(path: Path, section_threshold: int = DEFAULT_SECTION_THRESHOLD) -> list[SectionFinding]:
    path = Path(path)
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    return [
        SectionFinding(path, heading, lines, section_threshold)
        for heading, lines in _sections(text)
    ]


def check_all_sections(root: Path, section_threshold: int = DEFAULT_SECTION_THRESHOLD) -> list[SectionFinding]:
    root = Path(root)
    findings: list[SectionFinding] = []
    for path in find_claude_md_files(root) + find_memory_files(root):
        findings += check_sections(path, section_threshold)
    return findings


# --- backlinks ----------------------------------------------------------------


@dataclass
class BacklinkFinding:
    path: Path
    target: str | None
    status: Literal["ok", "missing", "broken", "cyclic"]

    @property
    def hint(self) -> str:
        if self.status == "missing":
            return "first non-empty line must be `↑ <path to parent>` — see docs/methodology.md"
        if self.status == "broken":
            return f"backlink target does not resolve to a file: {self.target}"
        if self.status == "cyclic":
            return "backlink chain cycles or exceeds depth 10 — check for a copy-paste loop"
        return ""


def _backlink_target(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    line = _first_nonempty_line(text)
    if not line:
        return None
    match = BACKLINK_RE.match(line)
    return match.group(1) if match else None


def check_backlinks(root: Path) -> list[BacklinkFinding]:
    root = Path(root)
    findings: list[BacklinkFinding] = []
    for path in find_memory_files(root):
        target = _backlink_target(path)
        if target is None:
            findings.append(BacklinkFinding(path, None, "missing"))
            continue

        resolved = (path.parent / target).resolve()
        if not resolved.is_file():
            findings.append(BacklinkFinding(path, target, "broken"))
            continue

        visited = {path.resolve()}
        current = resolved
        cyclic = True
        for _ in range(_MAX_CHAIN_DEPTH):
            if current in visited:
                break
            if current.name == "CLAUDE.md":
                cyclic = False
                break
            visited.add(current)
            if not current.is_file():
                cyclic = False
                break
            next_target = _backlink_target(current)
            if next_target is None:
                cyclic = False
                break
            current = (current.parent / next_target).resolve()
        findings.append(BacklinkFinding(path, target, "cyclic" if cyclic else "ok"))
    return findings


# --- wikilinks ------------------------------------------------------------


@dataclass
class WikilinkFinding:
    source: Path
    target: str
    resolved: bool


def _slug_index(memory_root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in memory_root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_NAME_RE.search(text)
        slug = match.group(1) if match else path.stem
        index.setdefault(slug, path)
        index.setdefault(path.stem, path)
    return index


def check_wikilinks(memory_root: Path) -> list[WikilinkFinding]:
    memory_root = Path(memory_root)
    index = _slug_index(memory_root)
    findings = []
    for path in memory_root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for match in WIKILINK_RE.finditer(text):
            target = match.group(1).strip()
            findings.append(WikilinkFinding(path, target, target in index))
    return findings
