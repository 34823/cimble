#!/usr/bin/env python3
"""PostToolUse adapter: warn/block when an edited CLAUDE.md or constitution.md crosses its
growth threshold. Delegates to cimble.check for the actual logic."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cimble.check import check_file  # noqa: E402
from cimble.config import resolve_config  # noqa: E402


def main() -> int:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path")
    if not file_path:
        return 0

    path = Path(file_path)
    if path.name not in ("CLAUDE.md", "constitution.md"):
        return 0
    if path.name == "constitution.md" and "memory" not in path.parts:
        return 0

    root = Path(os.environ.get("CIMBLE_ROOT", path.parent))
    config = resolve_config(root)
    finding = check_file(path, config.claude_md_threshold, config.constitution_threshold)
    if finding is None or finding.status == "ok":
        return 0

    message = f"{finding.path} is now {finding.lines} lines (threshold {finding.threshold}) — time to {finding.hint}."

    if config.strict:
        print(message, file=sys.stderr)
        return 2

    print(json.dumps({"systemMessage": message}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
