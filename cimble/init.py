"""Scaffolding: `cimble init` / `cimble create-memory`."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

TEMPLATES_DIR = Path(__file__).parent / "templates"

_CLAUDE_MD_MARKER = "<!-- cimble:stage1:v1 -->"
_MEMORY_INDEX_MARKER = "<!-- cimble:memory-index:v1 -->"
_MEMORY_TOPIC_MARKER = "<!-- cimble:memory-topic:v1 -->"

ActionKind = Literal["created", "skipped-exists", "skipped-dry-run"]


@dataclass
class InitAction:
    path: Path
    action: ActionKind


def _render(template_name: str, substitutions: dict[str, str]) -> str:
    text = (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")
    for key, value in substitutions.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _is_untouched_cimble_file(path: Path, marker: str) -> bool:
    if not path.is_file():
        return False
    try:
        return marker in path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False


def _write_if_absent(
    path: Path, template_name: str, substitutions: dict[str, str], marker: str, force: bool, dry_run: bool
) -> InitAction:
    if path.exists():
        if not (force and _is_untouched_cimble_file(path, marker)):
            return InitAction(path, "skipped-exists")
    if dry_run:
        return InitAction(path, "skipped-dry-run")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_render(template_name, substitutions), encoding="utf-8")
    return InitAction(path, "created")


def init(
    project_dir: Path,
    project_name: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> list[InitAction]:
    """Scaffold a starting CLAUDE.md — the only thing `cimble init` generates without a target.

    Splitting content out into memory/ is a per-project judgment call (what moves where), so it's
    not automated here — use `init_index`/`init_topic` to scaffold the *shape* of a split once
    you've decided to make one, with a correctly formatted backlink.
    """
    project_dir = Path(project_dir)
    project_name = project_name or project_dir.resolve().name
    claude_md = project_dir / "CLAUDE.md"
    return [
        _write_if_absent(claude_md, "stage1_claude_md.md", {"PROJECT_NAME": project_name}, _CLAUDE_MD_MARKER, force, dry_run)
    ]


def init_index(
    project_dir: Path,
    project_name: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> InitAction:
    """Scaffold `memory/index.md`, backlinked to the project's own CLAUDE.md."""
    project_dir = Path(project_dir)
    project_name = project_name or project_dir.resolve().name
    index_path = project_dir / "memory" / "index.md"
    substitutions = {"PROJECT_NAME": project_name, "BACKLINK": "↑ ../CLAUDE.md"}
    return _write_if_absent(index_path, "memory_index.md", substitutions, _MEMORY_INDEX_MARKER, force, dry_run)


def init_topic(
    project_dir: Path,
    slug: str,
    project_name: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> InitAction:
    """Scaffold `memory/<slug>.md`, backlinked to `memory/index.md` if it exists, else CLAUDE.md."""
    project_dir = Path(project_dir)
    project_name = project_name or project_dir.resolve().name
    topic_path = project_dir / "memory" / f"{slug}.md"
    index_path = project_dir / "memory" / "index.md"
    backlink_target = "index.md" if index_path.is_file() else "../CLAUDE.md"
    substitutions = {
        "PROJECT_NAME": project_name,
        "TOPIC_NAME": slug,
        "BACKLINK": f"↑ {backlink_target}",
    }
    return _write_if_absent(topic_path, "memory_topic.md", substitutions, _MEMORY_TOPIC_MARKER, force, dry_run)
