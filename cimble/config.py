"""Threshold/path resolution: CLI flag > env var > cimble.toml > default."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib  # type: ignore

DEFAULT_CLAUDE_MD_THRESHOLD = 120
DEFAULT_CONSTITUTION_THRESHOLD = 150


@dataclass
class Config:
    claude_md_threshold: int = DEFAULT_CLAUDE_MD_THRESHOLD
    constitution_threshold: int = DEFAULT_CONSTITUTION_THRESHOLD
    strict: bool = False


def _load_toml(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f).get("cimble", {})


def _env_bool(value: str) -> bool:
    return value.strip().lower() not in ("", "0", "false", "no")


def resolve_config(
    root: Path,
    cli_claude_md_threshold: int | None = None,
    cli_constitution_threshold: int | None = None,
    cli_strict: bool | None = None,
) -> Config:
    toml_data = _load_toml(Path(root) / "cimble.toml")

    if cli_claude_md_threshold is not None:
        claude_md_threshold = cli_claude_md_threshold
    elif "CIMBLE_CLAUDE_MD_THRESHOLD" in os.environ:
        claude_md_threshold = int(os.environ["CIMBLE_CLAUDE_MD_THRESHOLD"])
    else:
        claude_md_threshold = int(toml_data.get("claude_md_threshold", DEFAULT_CLAUDE_MD_THRESHOLD))

    if cli_constitution_threshold is not None:
        constitution_threshold = cli_constitution_threshold
    elif "CIMBLE_CONSTITUTION_THRESHOLD" in os.environ:
        constitution_threshold = int(os.environ["CIMBLE_CONSTITUTION_THRESHOLD"])
    else:
        constitution_threshold = int(toml_data.get("constitution_threshold", DEFAULT_CONSTITUTION_THRESHOLD))

    if cli_strict:
        strict = True
    elif "CIMBLE_STRICT" in os.environ:
        strict = _env_bool(os.environ["CIMBLE_STRICT"])
    else:
        strict = bool(toml_data.get("strict", False))

    return Config(
        claude_md_threshold=claude_md_threshold,
        constitution_threshold=constitution_threshold,
        strict=strict,
    )
