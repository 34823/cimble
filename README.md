# cimble

Progressive, self-splitting project memory for Claude Code (and any agent that reads a
`CLAUDE.md`-shaped file).

Named after **cambium** — the living layer in a tree trunk where old growth turns into new
growth — kept simple. *Cambium, but simple.*

## The cycle

> Work gets logged to a diary. Each folder that grows enough gets its own `CLAUDE.md`. Once a
> `CLAUDE.md` outgrows its threshold, it splits — a `constitution.md` becomes the index over
> topic files, `CLAUDE.md` keeps only what you need day to day. Topic files grow the same way,
> and split the same way, one layer at a time.

That's the whole idea. Everything below is detail.

## Why

`CLAUDE.md` files rot in one of two directions: they stay too small to be useful, or they grow
into a 400-line wall nobody reads before editing. cimble gives growth a shape instead of a
ceiling — a project's memory is allowed to get big, but only by branching, never by piling on.

## The three stages

| Stage | State | Trigger to move on |
|---|---|---|
| 1 | Everything lives in `CLAUDE.md` | `CLAUDE.md` passes ~120 lines |
| 2 | `CLAUDE.md` is operational-only ("how to run it", "what not to do"); architecture and rationale move to `memory/constitution.md` | `constitution.md` passes ~150 lines |
| 3 | `constitution.md` shrinks to an index; each topic gets its own `memory/<topic>/` file(s), which grow and split the same way | — recurses; no ceiling on depth |

Stage 3 isn't automated — deciding what content moves into which topic is a judgment call
specific to the project, not something a tool should guess at. `cimble` scaffolds stages 1 and
2; stage 3 is templates and convention only.

## The one exception: a root/dispatcher `CLAUDE.md`

The three-stage rule is for **one project's** `CLAUDE.md`. A root `CLAUDE.md` sitting over
several *independent* projects — routing ("what's where") rather than holding content — doesn't
follow it. It has its own pressure valve: an overgrown section moves into a dated diary
(`diary/YYYY-MM.md`) or a sibling role file (how the agent behaves, how the environment is set
up) — never into a `memory/constitution.md`, because a dispatcher root isn't "a project" in the
sense this methodology means. See `docs/methodology.md` for the full split.

## The `[[wikilink]]` convention

Inside `memory/`, files reference each other by slug, not by path: `[[debug-conventions]]`, not
`[debug](../debug/conventions.md)`. The slug comes from a `name:` field in the file's frontmatter
(falls back to the filename stem). This survives files moving around during a later split —
paths break, slugs don't. `cimble check --check-wikilinks` flags references that don't resolve.

## Install

```bash
pip install cimble
```

Or install as a Claude Code plugin directly from this repo (adds the `cimble` skill and the
growth-threshold hook automatically).

## Usage

```bash
# Start a new project at stage 1
cimble init my-project

# Start (or catch up to) stage 2
cimble init my-project --stage 2

# See what's over threshold
cimble check my-project

# Same, but exit non-zero if anything's over (for CI)
cimble check my-project --strict

# Also flag [[wikilinks]] that don't resolve
cimble check my-project --check-wikilinks
```

`create-memory` and `check-memory` work as aliases for `init` and `check`, if that's the name
you reach for.

Thresholds are configurable — CLI flag, then `CIMBLE_CLAUDE_MD_THRESHOLD` /
`CIMBLE_CONSTITUTION_THRESHOLD` / `CIMBLE_STRICT` env vars, then a `cimble.toml` at the project
root, then the 120/150 defaults. Nothing is hardcoded to any one project's layout.

## As a hook

Installing this as a Claude Code plugin wires `cimble check` into `PostToolUse` on `Edit`/`Write`
— the moment an edit pushes `CLAUDE.md` or a `constitution.md` over threshold, you get a
`systemMessage` nudge (or, in `--strict`/`CIMBLE_STRICT` mode, an error Claude has to act on
before continuing). See `docs/methodology.md` for the full hook design and why `PostToolUse`
beats a session-end check for this specific job.

## Examples

`examples/` has generalized, structure-only illustrations of all three stages — fictitious
projects, no real data, just the shape.

## Docs

Full write-up — the diary, the promotion rule (diary → CLAUDE.md/constitution, dated vs.
undated facts), `feedback_*` entries, the dispatcher-root exception, and the hook design — lives
in [`docs/methodology.md`](docs/methodology.md).

## License

MIT.
