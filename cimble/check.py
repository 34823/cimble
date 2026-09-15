"""Growth checks for CLAUDE.md / memory/*.md: whole-file backstop, per-section threshold,
backlink integrity, and (optionally) wikilinks."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .config import DEFAULT_FILE_THRESHOLD, DEFAULT_SECTION_THRESHOLD

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FRONTMATTER_NAME_RE = re.compile(r"^name:\s*(\S+)", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
# Accepts both a bare path (`↑ ../CLAUDE.md`) and a markdown link (`↑ [../CLAUDE.md](../CLAUDE.md)`),
# so a file's backlink can render as a clickable link without failing the check.
BACKLINK_RE = re.compile(r"^↑\s+(?:\[[^\]]*\]\(([^)]+)\)|(\S+))\s*$")

_MAX_CHAIN_DEPTH = 10


def _count_lines(path: Path) -> int:
    with path.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


def _first_nonempty_line(text: str) -> str | None:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return None


def _strip_frontmatter(text: str) -> str:
    """Drop a leading `---\\n...\\n---\\n` YAML block, if present, before backlink lookup."""
    return FRONTMATTER_RE.sub("", text, count=1)


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
    text = _strip_frontmatter(path.read_text(encoding="utf-8"))
    line = _first_nonempty_line(text)
    if not line:
        return None
    match = BACKLINK_RE.match(line)
    if not match:
        return None
    return match.group(1) or match.group(2)


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


# --- missing links ----------------------------------------------------------


def _canonical_slugs(memory_root: Path) -> dict[Path, str]:
    """One slug per file: its frontmatter `name:` if present, else the filename stem."""
    result: dict[Path, str] = {}
    for path in memory_root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_NAME_RE.search(text)
        result[path] = match.group(1) if match else path.stem
    return result


def _slug_words(slug: str) -> list[str]:
    return [w for w in re.split(r"[-_]+", slug) if w]


def _slug_pattern(slug: str) -> re.Pattern[str]:
    """Match a slug as prose too: `project-gnsh` also matches `project gnsh`/`project_gnsh`."""
    words = _slug_words(slug)
    return re.compile(r"\b" + r"[-_ ]+".join(re.escape(w) for w in words) + r"\b", re.IGNORECASE)


def _linked_targets(path: Path, canonical: dict[Path, str]) -> set[Path]:
    """Files `path` points to, via `[[wikilink]]` (resolved by slug) or `[markdown](link)` (resolved by path)."""
    text = path.read_text(encoding="utf-8")
    body = _strip_frontmatter(text)
    slug_to_path = {slug: p for p, slug in canonical.items()}
    targets: set[Path] = set()
    for m in WIKILINK_RE.finditer(body):
        slug = m.group(1).strip()
        if slug in slug_to_path:
            targets.add(slug_to_path[slug])
    for m in MARKDOWN_LINK_RE.finditer(body):
        link = m.group(1).strip()
        if link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        candidate = (path.parent / link).resolve()
        if candidate in canonical:
            targets.add(candidate)
    return targets


@dataclass
class MissingLinkFinding:
    path: Path
    target_slug: str
    target_path: Path

    @property
    def hint(self) -> str:
        return f"mentions [[{self.target_slug}]] as plain text but doesn't link it — add `[[{self.target_slug}]]`"


def check_missing_links(root: Path) -> list[MissingLinkFinding]:
    """Flag a file that mentions another memory topic by name/slug in prose without linking it
    (neither `[[wikilink]]` nor a markdown `[text](path)` link to that file).

    Single-word slugs (e.g. an index file named `MEMORY`) are skipped as targets — a common
    word matches too much prose to be a useful signal.
    """
    root = Path(root)
    memory_root = root / "memory"
    if not memory_root.is_dir():
        return []

    canonical = {p.resolve(): slug for p, slug in _canonical_slugs(memory_root).items()}
    findings: list[MissingLinkFinding] = []
    for path, _own_slug in canonical.items():
        text = path.read_text(encoding="utf-8")
        body = _strip_frontmatter(text)
        linked = _linked_targets(path, canonical)
        body_without_links = MARKDOWN_LINK_RE.sub("", WIKILINK_RE.sub("", body))

        for target_path, target_slug in canonical.items():
            if target_path == path or target_path in linked:
                continue
            if len(_slug_words(target_slug)) < 2:
                continue
            if _slug_pattern(target_slug).search(body_without_links):
                findings.append(MissingLinkFinding(path, target_slug, target_path))
    return findings


# --- orphans ------------------------------------------------------------------


@dataclass
class OrphanFinding:
    path: Path
    slug: str

    @property
    def hint(self) -> str:
        return "no other memory file links here and no CLAUDE.md mentions it — unreachable from a future session"


def check_orphans(root: Path) -> list[OrphanFinding]:
    """Flag a memory file that nothing else points back to: no incoming `[[wikilink]]` or
    markdown link from another memory file or a CLAUDE.md index/dispatch table, and its slug
    isn't even mentioned there as plain text."""
    root = Path(root)
    memory_root = root / "memory"
    if not memory_root.is_dir():
        return []

    canonical = {p.resolve(): slug for p, slug in _canonical_slugs(memory_root).items()}
    other_files = find_memory_files(root) + find_claude_md_files(root)

    incoming: set[Path] = set()
    for other in other_files:
        incoming |= _linked_targets(other, canonical)

    findings: list[OrphanFinding] = []
    for path, slug in canonical.items():
        if path in incoming:
            continue
        pattern = _slug_pattern(slug)
        mentioned = any(
            pattern.search(other.read_text(encoding="utf-8"))
            for other in other_files
            if other.resolve() != path
        )
        if not mentioned:
            findings.append(OrphanFinding(path, slug))
    return findings
