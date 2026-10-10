"""Read-only memory audit: every check of `cimble check` plus staleness and duplicated lines,
over one project or over every project under a parent directory. Changes nothing."""
from __future__ import annotations

import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .check import (
    check_all_sections,
    check_backlinks,
    check_missing_links,
    check_orphans,
    check_thresholds,
    check_wikilinks,
    find_claude_md_files,
    find_memory_files,
)
from .config import resolve_config

DEFAULT_STALE_DAYS = 60
MIN_DUPLICATE_CHARS = 60
_SKIP_DIRS = {".git", ".claude", "node_modules", ".venv", "venv", "__pycache__"}


@dataclass
class ProjectAudit:
    path: Path
    over_files: list[tuple[Path, int, int]] = field(default_factory=list)
    over_sections: list[tuple[Path, str, int, int]] = field(default_factory=list)
    backlinks: list[tuple[Path, str]] = field(default_factory=list)
    wikilinks: list[tuple[Path, str]] = field(default_factory=list)
    missing_links: list[tuple[Path, str]] = field(default_factory=list)
    orphans: list[Path] = field(default_factory=list)
    stale: list[tuple[Path, int]] = field(default_factory=list)
    duplicates: list[tuple[str, list[Path]]] = field(default_factory=list)
    memory_files: int = 0

    @property
    def issue_count(self) -> int:
        return sum(
            len(x)
            for x in (
                self.over_files, self.over_sections, self.backlinks, self.wikilinks,
                self.missing_links, self.orphans, self.stale, self.duplicates,
            )
        )


def find_projects(path: Path, each: bool = False, exclude: tuple[str, ...] = ()) -> list[Path]:
    """`path` itself if it has a CLAUDE.md (unless `each`), else its direct subfolders that do."""
    path = Path(path)
    if not each and (path / "CLAUDE.md").is_file():
        return [path]
    return sorted(
        p for p in path.iterdir()
        if p.is_dir() and p.name not in _SKIP_DIRS and p.name not in exclude
        and not p.name.startswith(".") and (p / "CLAUDE.md").is_file()
    )


def _live(files: list[Path]) -> list[Path]:
    """Drop tool noise: git worktrees and plugin caches live under `.claude/`."""
    return [f for f in files if not _SKIP_DIRS.intersection(f.parts)]


def _norm(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip().lower())


def _duplicates(files: list[Path]) -> list[tuple[str, list[Path]]]:
    seen: dict[str, set[Path]] = defaultdict(set)
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            n = _norm(line)
            if len(n) >= MIN_DUPLICATE_CHARS and not n.startswith(("|", "---", "```", "↑")):
                seen[n].add(path)
    return sorted(
        ((line, sorted(paths)) for line, paths in seen.items() if len(paths) > 1),
        key=lambda item: -len(item[0]),
    )


def audit_project(project: Path, stale_days: int = DEFAULT_STALE_DAYS) -> ProjectAudit:
    project = Path(project)
    config = resolve_config(project)
    result = ProjectAudit(project)

    live = set(_live(find_memory_files(project) + find_claude_md_files(project)))
    result.over_files = [
        (f.path, f.lines, f.threshold) for f in check_thresholds(project, config.file_threshold)
        if f.status == "over" and f.path in live
    ]
    result.over_sections = [
        (s.path, s.heading, s.lines, s.threshold)
        for s in check_all_sections(project, config.section_threshold) if s.status == "over" and s.path in live
    ]
    result.backlinks = [(b.path, b.status) for b in check_backlinks(project) if b.status != "ok" and b.path in live]
    if (project / "memory").is_dir():
        result.wikilinks = [(w.source, w.target) for w in check_wikilinks(project / "memory") if not w.resolved]
    result.missing_links = [(m.path, m.target_slug) for m in check_missing_links(project)]
    result.orphans = [o.path for o in check_orphans(project)]

    memory = _live(find_memory_files(project))
    result.memory_files = len(memory)
    now = time.time()
    for path in memory + _live(find_claude_md_files(project)):
        age = int((now - path.stat().st_mtime) / 86400)
        if age >= stale_days:
            result.stale.append((path, age))
    result.stale.sort(key=lambda item: -item[1])
    result.duplicates = _duplicates(memory + [project / "CLAUDE.md"])
    return result


def render_markdown(audits: list[ProjectAudit], root: Path, stale_days: int = DEFAULT_STALE_DAYS) -> str:
    def rel(p: Path) -> str:
        try:
            return str(p.relative_to(root))
        except ValueError:
            return str(p)

    out = ["# cimble audit", "", "| project | memory files | issues |", "|---|---|---|"]
    out += [f"| {rel(a.path)} | {a.memory_files} | {a.issue_count} |" for a in audits]
    for a in audits:
        if not a.issue_count:
            continue
        out += ["", f"## {rel(a.path)}"]
        out += [f"- OVER file: {rel(p)} — {n} / {t} lines" for p, n, t in a.over_files]
        out += [f"- OVER section: {rel(p)} `## {h}` — {n} / {t} lines" for p, h, n, t in a.over_sections]
        out += [f"- backlink {s}: {rel(p)}" for p, s in a.backlinks]
        out += [f"- broken wikilink: {rel(p)} -> [[{t}]]" for p, t in a.wikilinks]
        out += [f"- not linked: {rel(p)} mentions `{s}`" for p, s in a.missing_links]
        out += [f"- orphan: {rel(p)}" for p in a.orphans]
        out += [f"- stale ({age} d >= {stale_days}): {rel(p)}" for p, age in a.stale]
        for line, paths in a.duplicates[:10]:
            out.append(f"- duplicate line in {', '.join(rel(p) for p in paths)}: \"{line[:100]}\"")
        if len(a.duplicates) > 10:
            out.append(f"- ... and {len(a.duplicates) - 10} more duplicate lines")
    return "\n".join(out) + "\n"
