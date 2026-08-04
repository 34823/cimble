#!/usr/bin/env python3
"""PostToolUse adapter: warn/block when an edited CLAUDE.md or memory/*.md file crosses its
growth threshold (whole-file backstop or a single ## section). Delegates to cimble.check for the
actual logic."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cimble.check import check_file, check_sections  # noqa: E402
from cimble.config import resolve_config  # noqa: E402


def main() -> int:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path")
    if not file_path:
        return 0

    path = Path(file_path)
    if path.name != "CLAUDE.md" and "memory" not in path.parts:
        return 0
    if path.suffix != ".md":
        return 0

    root = Path(os.environ.get("CIMBLE_ROOT", path.parent))
    config = resolve_config(root)

    messages = []

    finding = check_file(path, config.file_threshold)
    if finding is not None and finding.status == "over":
        messages.append(
            f"{finding.path} is now {finding.lines} lines (threshold {finding.threshold}) — {finding.hint}."
        )

    for section in check_sections(path, config.section_threshold):
        if section.status == "over":
            messages.append(
                f"{path} ## {section.heading} is {section.lines} lines (threshold {section.threshold}) — {section.hint}."
            )

    if not messages:
        return 0

    combined = "\n".join(messages)

    if config.strict:
        print(combined, file=sys.stderr)
        return 2

    print(json.dumps({"systemMessage": combined}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
