"""Non-blocking Codex PostToolUse growth warnings, including shell-written files.

Codex sends apply_patch in tool_input.command rather than Claude's file_path.
For opaque shell/code tools we compare bounded instruction/memory scopes by mtime;
we never execute or attempt to interpret the command itself.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from .check import check_file, check_sections
from .config import resolve_config

_PATCH_PATH = re.compile(r"^\*\*\* (?:Add File|Update File|Move to): (.+)$", re.MULTILINE)
_SKIP = {".git", ".wine", "node_modules", ".venv", "venv", "__pycache__", "graveyard", "backups"}


def _memory_files(root: Path):
    if not root.is_dir() or root.is_symlink():
        return
    count = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in _SKIP and not d.startswith('.')]
        for name in files:
            if name.endswith('.md'):
                path = Path(directory) / name
                if not path.is_symlink():
                    yield path
                count += 1
                if count >= 5000:
                    return


def project_scopes(cwd: Path) -> set[Path]:
    """Ancestors + immediate projects; no recursive walk through a multi-project root."""
    scopes = {cwd, *cwd.parents}
    try:
        for child in cwd.iterdir():
            if (child.is_dir() and not child.is_symlink() and not child.name.startswith('.')
                    and child.name not in _SKIP
                    and any((child / n).is_file() for n in ('AGENTS.md', 'CLAUDE.md'))):
                scopes.add(child)
    except OSError:
        pass
    # A worktree's shared memory can live in the main checkout.
    try:
        result = subprocess.run(['git', '-C', str(cwd), 'rev-parse', '--path-format=absolute',
                                 '--git-common-dir'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            scopes.add(Path(result.stdout.strip()).parent)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return scopes


def candidate_paths(payload: dict, home: Path | None = None) -> tuple[set[Path], set[Path]]:
    cwd = Path(payload.get('cwd') or os.getcwd()).resolve()
    tool_input = payload.get('tool_input') or {}
    explicit = set()
    if isinstance(tool_input, dict):
        if tool_input.get('file_path'):
            explicit.add(Path(tool_input['file_path']))
        command = tool_input.get('command', '')
        if isinstance(command, str) and '*** Begin Patch' in command:
            explicit.update(Path(p) for p in _PATCH_PATH.findall(command))
    explicit = {(p if p.is_absolute() else cwd / p).resolve() for p in explicit}
    candidates = set(explicit)
    home = home or Path.home()
    for scope in project_scopes(cwd):
        for name in ('AGENTS.md', 'CLAUDE.md'):
            path = scope / name
            if path.is_file():
                candidates.add(path)
                break
        candidates.update(_memory_files(scope / 'memory'))
        encoded = str(scope).replace('/', '-')
        candidates.update(_memory_files(home / '.claude' / 'projects' / encoded / 'memory'))
    return candidates, explicit


def _config_root(path: Path) -> Path:
    return next((p for p in path.parents if (p / 'cimble.toml').is_file()), path.parent)


def warnings(payload: dict, state_path: Path, *, now: float | None = None,
             home: Path | None = None) -> list[str]:
    now = time.time() if now is None else now
    candidates, explicit = candidate_paths(payload, home)
    try:
        previous = json.loads(state_path.read_text())
    except (OSError, ValueError):
        previous = {}
    current = dict(previous)
    messages = []
    checked = set()
    for path in sorted(candidates):
        try:
            stat = path.stat()
            fingerprint = [stat.st_mtime_ns, stat.st_size]
            key = str(path)
            current[key] = fingerprint
            if previous.get(key) == fingerprint:
                continue
            # Don't flood a new session with old findings from unrelated projects.
            if key not in previous and path not in explicit and stat.st_mtime < now - 15:
                continue
            config = resolve_config(_config_root(path))
            finding = check_file(path, config.file_threshold, config.claude_md_threshold)
            if finding is None or finding.path in checked:
                continue
            checked.add(finding.path)
            if finding.status == 'over':
                messages.append(f'{finding.path}: {finding.lines} lines (threshold {finding.threshold}); {finding.hint}.')
            for section in check_sections(finding.path, config.section_threshold, config.exempt_sections):
                if section.status == 'over':
                    messages.append(f'{finding.path} ## {section.heading}: {section.lines} lines '
                                    f'(threshold {section.threshold}); {section.hint}.')
        except (OSError, ValueError, UnicodeError):
            continue
    state_path.parent.mkdir(parents=True, exist_ok=True)
    pending = state_path.with_suffix('.tmp')
    pending.write_text(json.dumps(current))
    os.chmod(pending, 0o600)
    pending.replace(state_path)
    return messages


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        session = str(payload.get('session_id') or payload.get('cwd') or 'default')
        key = hashlib.sha256(session.encode()).hexdigest()[:24]
        state = Path(os.environ.get('CIMBLE_CODEX_CACHE', Path.home() / '.cache/cimble-codex')) / (key + '.json')
        messages = warnings(payload, state)
        if messages:
            text = 'Cimble: consider splitting oversized instructions/memory; no automatic edits.\n' + '\n'.join(messages[:12])
            print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse',
                                                     'additionalContext': text}}))
    except (OSError, ValueError, TypeError):
        pass  # Growth advice must not make a successful tool fail.
    return 0


if __name__ == '__main__':
    sys.exit(main())
