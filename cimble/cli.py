"""cimble CLI: `init`/`create-memory` and `check`/`check-memory`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .check import check_all_sections, check_backlinks, check_thresholds, check_wikilinks
from .config import resolve_config
from .init import init as init_project
from .init import init_index, init_topic


def _add_init_parser(subparsers: argparse._SubParsersAction) -> None:
    for name in ("init", "create-memory"):
        parser = subparsers.add_parser(name, help="Scaffold CLAUDE.md, or a memory/index.md or memory/<topic>.md split")
        parser.add_argument("project_dir", nargs="?", default=".")
        parser.add_argument("--topic", default=None, help="Scaffold memory/<slug>.md instead of CLAUDE.md")
        parser.add_argument("--index", action="store_true", help="Scaffold memory/index.md instead of CLAUDE.md")
        parser.add_argument("--project-name", default=None)
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.set_defaults(handler=_run_init)


def _add_check_parser(subparsers: argparse._SubParsersAction) -> None:
    for name in ("check", "check-memory"):
        parser = subparsers.add_parser(name, help="Check CLAUDE.md/memory growth thresholds and backlinks")
        parser.add_argument("path", nargs="?", default=".")
        parser.add_argument("--file-threshold", type=int, default=None)
        parser.add_argument("--section-threshold", type=int, default=None)
        parser.add_argument("--check-wikilinks", action="store_true")
        parser.add_argument("--strict", action="store_true")
        parser.add_argument("--format", choices=("text", "json"), default="text")
        parser.set_defaults(handler=_run_check)


def _run_init(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir)

    if args.topic and args.index:
        print("--topic and --index are mutually exclusive", file=sys.stderr)
        return 2

    if args.topic:
        actions = [init_topic(project_dir, args.topic, project_name=args.project_name, force=args.force, dry_run=args.dry_run)]
    elif args.index:
        actions = [init_index(project_dir, project_name=args.project_name, force=args.force, dry_run=args.dry_run)]
    else:
        actions = init_project(project_dir, project_name=args.project_name, force=args.force, dry_run=args.dry_run)

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
        cli_file_threshold=args.file_threshold,
        cli_section_threshold=args.section_threshold,
        cli_strict=args.strict or None,
    )
    findings = check_thresholds(root, config.file_threshold)
    section_findings = check_all_sections(root, config.section_threshold)
    backlink_findings = check_backlinks(root)

    over = [f for f in findings if f.status == "over"]
    over_sections = [f for f in section_findings if f.status == "over"]
    broken_backlinks = [b for b in backlink_findings if b.status != "ok"]

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
            "sections": [
                {"path": str(f.path), "heading": f.heading, "lines": f.lines, "threshold": f.threshold, "status": f.status}
                for f in section_findings
            ],
            "backlinks": [
                {"path": str(b.path), "target": b.target, "status": b.status} for b in backlink_findings
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
        for s in over_sections:
            print(f"{s.path}  ## {s.heading}: {s.lines} / {s.threshold} lines  OVER — {s.hint}")
        for b in broken_backlinks:
            print(f"{b.path}  backlink {b.status.upper()} — {b.hint}", file=sys.stderr)
        for w in broken_wikilinks:
            print(f"{w.source}  broken wikilink -> [[{w.target}]]", file=sys.stderr)

    if config.strict and (over or over_sections or broken_backlinks or broken_wikilinks):
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
