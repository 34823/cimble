"""Growth-threshold and wikilink checks for CLAUDE.md / constitution.md files."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .config import DEFAULT_CLAUDE_MD_THRESHOLD, DEFAULT_CONSTITUTION_THRESHOLD

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
FRONTMATTER_NAME_RE = re.compile(r"^name:\s*(\S+)", re.MULTILINE)


@dataclass
class ThresholdFinding:
    path: Path
    kind: Literal["claude_md", "constitution"]
    lines: int
    threshold: int

    @property
    def status(self) -> Literal["ok", "over"]:
        return "over" if self.lines > self.threshold else "ok"

    @property
    def hint(self) -> str:
        if self.status == "ok":
            return ""
        if self.kind == "claude_md":
            return "split into memory/constitution.md (stage 2)"
        return "split into memory/<topic>/ (stage 3)"


def _count_lines(path: Path) -> int:
    with path.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


def _is_constitution(path: Path) -> bool:
    return path.name == "constitution.md" and "memory" in path.parts


def find_claude_md_files(root: Path) -> list[Path]:
    return sorted(root.rglob("CLAUDE.md"))


def find_constitution_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("constitution.md") if _is_constitution(p))


def check_thresholds(
    root: Path,
    claude_md_threshold: int = DEFAULT_CLAUDE_MD_THRESHOLD,
    constitution_threshold: int = DEFAULT_CONSTITUTION_THRESHOLD,
) -> list[ThresholdFinding]:
    root = Path(root)
    findings = [
        ThresholdFinding(path, "claude_md", _count_lines(path), claude_md_threshold)
        for path in find_claude_md_files(root)
    ]
    findings += [
        ThresholdFinding(path, "constitution", _count_lines(path), constitution_threshold)
        for path in find_constitution_files(root)
    ]
    return findings


def check_file(
    path: Path,
    claude_md_threshold: int = DEFAULT_CLAUDE_MD_THRESHOLD,
    constitution_threshold: int = DEFAULT_CONSTITUTION_THRESHOLD,
) -> ThresholdFinding | None:
    path = Path(path)
    if not path.is_file():
        return None
    if path.name == "CLAUDE.md":
        return ThresholdFinding(path, "claude_md", _count_lines(path), claude_md_threshold)
    if _is_constitution(path):
        return ThresholdFinding(path, "constitution", _count_lines(path), constitution_threshold)
    return None


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
