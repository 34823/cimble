"""Scaffolding: `cimble init` / `cimble create-memory`."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

TEMPLATES_DIR = Path(__file__).parent / "templates"

_STAGE1_MARKER = "<!-- cimble:stage1:v1 -->"
_STAGE2_CLAUDE_MARKER = "<!-- cimble:stage2-claude:v1 -->"
_STAGE2_CONSTITUTION_MARKER = "<!-- cimble:stage2-constitution:v1 -->"

ActionKind = Literal["created", "skipped-exists", "skipped-dry-run"]


@dataclass
class InitAction:
    path: Path
    action: ActionKind


def _render(template_name: str, project_name: str) -> str:
    text = (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")
    return text.replace("{{PROJECT_NAME}}", project_name)


def _is_untouched_cimble_file(path: Path, marker: str) -> bool:
    if not path.is_file():
        return False
    try:
        return marker in path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False


def _write_if_absent(
    path: Path, template_name: str, project_name: str, marker: str, force: bool, dry_run: bool
) -> InitAction:
    if path.exists():
        if not (force and _is_untouched_cimble_file(path, marker)):
            return InitAction(path, "skipped-exists")
    if dry_run:
        return InitAction(path, "skipped-dry-run")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_render(template_name, project_name), encoding="utf-8")
    return InitAction(path, "created")


def init(
    project_dir: Path,
    stage: int = 1,
    project_name: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> list[InitAction]:
    project_dir = Path(project_dir)
    project_name = project_name or project_dir.resolve().name
    claude_md = project_dir / "CLAUDE.md"

    if stage == 1:
        return [_write_if_absent(claude_md, "stage1_claude_md.md", project_name, _STAGE1_MARKER, force, dry_run)]

    if stage == 2:
        actions = []
        if claude_md.exists():
            actions.append(InitAction(claude_md, "skipped-exists"))
        else:
            actions.append(
                _write_if_absent(claude_md, "stage2_claude_md.md", project_name, _STAGE2_CLAUDE_MARKER, force, dry_run)
            )
        constitution = project_dir / "memory" / "constitution.md"
        actions.append(
            _write_if_absent(
                constitution, "stage2_constitution.md", project_name, _STAGE2_CONSTITUTION_MARKER, force, dry_run
            )
        )
        return actions

    raise ValueError(f"unsupported stage: {stage} (only 1 and 2 are scaffoldable — stage 3 is a manual split)")
