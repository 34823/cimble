---
name: cimble
description: Scaffold or check a project's growing CLAUDE.md/memory system. Use when starting a new project's memory setup, when a CLAUDE.md section or a memory/*.md file feels too long, or when asked to "set up cimble", "check memory growth", or split a CLAUDE.md section into its own topic file.
---

# cimble

Progressive, self-splitting project memory. One rule, applied fractally: a `CLAUDE.md` starts as
one file with a `## Topics` index; any `##` section — including that index — that outgrows ~40
lines carves out into `memory/<topic>.md` (or `memory/index.md`, for the topic index itself),
with a backlink to whatever it was carved from. Carved-out files split the same way if they grow.
There's no separate "constitution" file type — a carved-out index and a carved-out topic are the
same kind of object.

## Commands

- `cimble init [project_dir]` (alias: `create-memory`) — scaffold a starting `CLAUDE.md`. Never
  overwrites a file it didn't generate itself.
- `cimble init --topic <slug> [project_dir]` — scaffold `memory/<slug>.md`, backlinked to
  `memory/index.md` if that exists, else to `CLAUDE.md`.
- `cimble init --index [project_dir]` — scaffold `memory/index.md`, backlinked to `CLAUDE.md`.
- `cimble check [path] [--strict] [--check-wikilinks]` (alias: `check-memory`) — report which
  sections and files have crossed threshold, plus any broken or cyclic backlinks. `--strict`
  exits non-zero on any finding (for CI or a hook in strict mode).

## When to use which

- New project, no `CLAUDE.md` yet → `cimble init`.
- `CLAUDE.md` already exists and a section feels long → `cimble check` first to confirm it's
  actually over threshold (and check whether it's frequently-used operational content, which is
  allowed to stay long — see `docs/methodology.md`), then `cimble init --topic <slug>` to lay
  down the target file with a correct backlink, then move the content by hand (what moves where
  is a judgment call cimble deliberately doesn't automate) and replace the section with a
  one-line hook under `## Topics`.
- Topic index itself getting long → same idea, `cimble init --index` instead of `--topic`.
- A topic file keeps growing → split it the same way, one layer down, inside its own subfolder.

Full methodology — backlinks, the diary anchor, lazy descent when reading it back, the
root/dispatcher exception, and the `[[wikilink]]` convention — see `docs/methodology.md` in this
plugin's repo.
