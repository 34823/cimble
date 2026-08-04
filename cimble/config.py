"""Threshold/path resolution: CLI flag > env var > cimble.toml > default."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib  # type: ignore

DEFAULT_FILE_THRESHOLD = 120
DEFAULT_SECTION_THRESHOLD = 40


@dataclass
class Config:
    file_threshold: int = DEFAULT_FILE_THRESHOLD
    section_threshold: int = DEFAULT_SECTION_THRESHOLD
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
    cli_file_threshold: int | None = None,
    cli_section_threshold: int | None = None,
    cli_strict: bool | None = None,
) -> Config:
    toml_data = _load_toml(Path(root) / "cimble.toml")

    if cli_file_threshold is not None:
        file_threshold = cli_file_threshold
    elif "CIMBLE_FILE_THRESHOLD" in os.environ:
        file_threshold = int(os.environ["CIMBLE_FILE_THRESHOLD"])
    else:
        file_threshold = int(toml_data.get("file_threshold", DEFAULT_FILE_THRESHOLD))

    if cli_section_threshold is not None:
        section_threshold = cli_section_threshold
    elif "CIMBLE_SECTION_THRESHOLD" in os.environ:
        section_threshold = int(os.environ["CIMBLE_SECTION_THRESHOLD"])
    else:
        section_threshold = int(toml_data.get("section_threshold", DEFAULT_SECTION_THRESHOLD))

    if cli_strict:
        strict = True
    elif "CIMBLE_STRICT" in os.environ:
        strict = _env_bool(os.environ["CIMBLE_STRICT"])
    else:
        strict = bool(toml_data.get("strict", False))

    return Config(
        file_threshold=file_threshold,
        section_threshold=section_threshold,
        strict=strict,
    )
