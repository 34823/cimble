---
name: cimble
description: Scaffold or check a project's growing CLAUDE.md/memory system. Use when starting a new project's memory setup, when CLAUDE.md or memory/constitution.md feels too long, or when asked to "set up cimble", "check memory growth", or split a CLAUDE.md into a constitution.
---

# cimble

Progressive, self-splitting project memory. A project's `CLAUDE.md` starts as one file; once it
outgrows ~120 lines it splits into `memory/constitution.md`; once that outgrows ~150 lines it
splits into `memory/<topic>/` files, and `constitution.md` shrinks back down to an index.

## Commands

- `cimble init [--stage 1|2] [project_dir]` (alias: `create-memory`) — scaffold a starting
  `CLAUDE.md`, or a `CLAUDE.md` + `memory/constitution.md` pair for stage 2. Never overwrites a
  file it didn't generate itself.
- `cimble check [path] [--strict] [--check-wikilinks]` (alias: `check-memory`) — report which
  `CLAUDE.md`/`constitution.md` files have crossed their threshold and are due for a split.
  `--strict` exits non-zero on any finding (for CI or a hook in strict mode).

## When to use which

- New project, no CLAUDE.md yet → `cimble init`.
- CLAUDE.md already exists and feels long → `cimble check` first to confirm it's actually over
  threshold, then split content into `memory/constitution.md` by hand (what moves where is a
  judgment call cimble deliberately doesn't automate) and re-run `cimble init --stage 2` to lay
  down the constitution skeleton if it isn't there yet.
- Splitting a constitution into topics (stage 3) is always manual — see `docs/methodology.md`.

Full methodology, the root/dispatcher exception, and the `[[wikilink]]` convention: see
`docs/methodology.md` in this plugin's repo.
