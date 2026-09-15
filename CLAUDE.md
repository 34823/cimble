# CLAUDE.md

`cimble` — an open-source Python toolkit: progressive, self-splitting project memory for
Claude Code. The methodology lives in `docs/methodology.md` and `README.md` — not duplicated here.

## Running

```bash
# from the cimble/ root (venv already set up in .venv)
cimble init <project>                        # starter CLAUDE.md
cimble init <project> --topic <slug>         # carve a section out into memory/<slug>.md
cimble init <project> --index                # carve the topic index out into memory/index.md
cimble check <project>                       # what crossed a threshold (section/file/backlink)
cimble check <project> --strict              # same, but exit non-zero (for CI)
cimble check <project> --check-wikilinks
cimble check <project> --check-missing-links   # topic mentioned in prose but not [[linked]]
cimble check <project> --check-orphans         # memory file nothing points back to
```

Tests: `pytest` from the root (`tests/`, covers `check`, `init`, wikilinks).

## Layout

- `cimble/` — the package itself (`cli.py`, `init.py`, `check.py`, `config.py`, `templates/`).
- `hooks/` — `check_memory_hook.py` + `hooks.json`, a PostToolUse hook on Edit/Write.
- `skills/cimble/` — the Claude Code skill (`/cimble`).
- `examples/` — fictional illustrations of stages 1–3, no real data.
- `docs/methodology.md` — the full write-up for outside readers.

## Don't

- Don't put real data from other projects (`alpha-search`, `gemgymbot`) into `examples/` —
  fictional structures only, this is a public repository.
- Don't hardcode the 120/40 thresholds in the code — they are configurable via a CLI flag /
  `CIMBLE_*` env / `cimble.toml`; the defaults are only a fallback.

## Publishing

The repository is github.com/34823/cimble, public. Check diffs for secrets and personal data
more strictly than usual before pushing.
