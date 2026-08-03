"""cimble CLI: `init`/`create-memory` and `check`/`check-memory`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .check import check_thresholds, check_wikilinks
from .config import resolve_config
from .init import init as init_project


def _add_init_parser(subparsers: argparse._SubParsersAction) -> None:
    for name in ("init", "create-memory"):
        parser = subparsers.add_parser(name, help="Scaffold CLAUDE.md / memory/constitution.md")
        parser.add_argument("project_dir", nargs="?", default=".")
        parser.add_argument("--stage", type=int, choices=(1, 2), default=1)
        parser.add_argument("--project-name", default=None)
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.set_defaults(handler=_run_init)


def _add_check_parser(subparsers: argparse._SubParsersAction) -> None:
    for name in ("check", "check-memory"):
        parser = subparsers.add_parser(name, help="Check CLAUDE.md/constitution.md growth thresholds")
        parser.add_argument("path", nargs="?", default=".")
        parser.add_argument("--claude-md-threshold", type=int, default=None)
        parser.add_argument("--constitution-threshold", type=int, default=None)
        parser.add_argument("--check-wikilinks", action="store_true")
        parser.add_argument("--strict", action="store_true")
        parser.add_argument("--format", choices=("text", "json"), default="text")
        parser.set_defaults(handler=_run_check)


def _run_init(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir)
    actions = init_project(
        project_dir,
        stage=args.stage,
        project_name=args.project_name,
        force=args.force,
        dry_run=args.dry_run,
    )
    for action in actions:
        print(f"{action.action:16s} {action.path}")

    if any(a.action == "skipped-exists" for a in actions):
        print(
            "Refusing to overwrite existing, human-owned files. "
            "If a split is due, move content manually — see docs/methodology.md.",
            file=sys.stderr,
        )
        return 1
    return 0


def _run_check(args: argparse.Namespace) -> int:
    root = Path(args.path)
    config = resolve_config(
        root,
        cli_claude_md_threshold=args.claude_md_threshold,
        cli_constitution_threshold=args.constitution_threshold,
        cli_strict=args.strict or None,
    )
    findings = check_thresholds(root, config.claude_md_threshold, config.constitution_threshold)
    over = [f for f in findings if f.status == "over"]

    broken_wikilinks = []
    if args.check_wikilinks:
        memory_root = root / "memory"
        if memory_root.is_dir():
            broken_wikilinks = [w for w in check_wikilinks(memory_root) if not w.resolved]

    if args.format == "json":
        payload = {
            "findings": [
                {"path": str(f.path), "kind": f.kind, "lines": f.lines, "threshold": f.threshold, "status": f.status}
                for f in findings
            ],
            "broken_wikilinks": [
                {"source": str(w.source), "target": w.target} for w in broken_wikilinks
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        for f in findings:
            hint = f"  {f.status.upper()} — {f.hint}" if f.status == "over" else "  ok"
            print(f"{f.path}  {f.lines} / {f.threshold} lines{hint}")
        for w in broken_wikilinks:
            print(f"{w.source}  broken wikilink -> [[{w.target}]]", file=sys.stderr)

    if config.strict and (over or broken_wikilinks):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cimble")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_init_parser(subparsers)
    _add_check_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
