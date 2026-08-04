# cimble

Progressive, self-splitting project memory for Claude Code (and any agent that reads a
`CLAUDE.md`-shaped file).

Named after **cambium** — the living layer in a tree trunk where old growth turns into new
growth — kept simple. *Cambium, but simple.*

## The cycle

> Work gets logged to a diary. `CLAUDE.md` holds everything about a project — operational
> info and an index of topics — as one file, as long as every section in it stays small. The
> moment one section (including the topic index itself) outgrows its slot, that section — and
> only that section — gets carved out into its own file under `memory/`, with a line pointing
> back to where it came from. Carved-out files grow and split the same way, one layer at a time.

That's the whole idea. Everything below is detail.

## Why

`CLAUDE.md` files rot in one of two directions: they stay too small to be useful, or they grow
into a 400-line wall nobody reads before editing. cimble gives growth a shape instead of a
ceiling — a project's memory is allowed to get big, but only by branching, never by piling on.

## How it grows

There's one rule, applied fractally — no separate "stage 2 file":

- The unit of splitting is a `##` section, not a file. A section that outgrows ~40 lines is a
  candidate to carve into `memory/<topic>.md`. A whole file that outgrows ~120 lines even with
  every section under that — that's the backstop, and it's a sign to go carve something anyway.
- The threshold is a trigger to review, not an automatic order: content you reach for often
  (how to run it, what not to do) can stay past the line count; rationale and history you rarely
  need should move out even under it. Frequency of use decides, not just size.
- The topic index — the list of one-line hooks pointing at carved-out topics — is a section like
  any other. Small project: it lives inline in `CLAUDE.md`, under a `## Topics` heading. Once
  that list itself outgrows ~40 lines, it carves out too, into `memory/index.md` — not because
  it's a different kind of thing, but because the same rule applied to it.

There's no `constitution.md`, and no "stage 2" as a separate shape to scaffold — a project that
hasn't split yet just looks like a single `CLAUDE.md`; a project that has looks like `CLAUDE.md`
plus a `memory/` tree. Both are the same rule at different points.

`cimble init` scaffolds a starting `CLAUDE.md`. `cimble init --index` and `cimble init --topic
<slug>` scaffold the *shape* of a split — file, path, and a correctly formatted backlink — once
you've decided to make one. Deciding *what* content moves where stays a per-project judgment
call cimble doesn't automate.

## Backlinks

Every file under `memory/` starts with one fixed-format line pointing at whatever produced it:

```
↑ ../CLAUDE.md
```

or, for a file carved out of an index: `↑ index.md`. This is what lets a cold read of a deep
topic file trace back to the top — and what `cimble check` parses to catch a broken or renamed
path, or a copy-paste cycle, before it rots silently.

## Reading it back: lazy descent

The point of splitting is wasted if reading it back means loading the whole tree anyway. The
rule for an agent (or a human) reading this structure: stop at the first level that answers the
question. Read `CLAUDE.md`. If that's enough, stop — don't open `memory/`. Only descend one level
if `CLAUDE.md` doesn't have the answer *and* its topic index has a hook that specifically matches
what you're looking for. Never scan `memory/` wholesale "just in case." This only works if hooks
are specific enough to make that call without opening the file — "about the backend" is a bad
hook; "why retries are capped at 3, and what breaks if you raise it" is a good one.

## The one exception: a root/dispatcher `CLAUDE.md`

This growth rule is for **one project's** `CLAUDE.md`. A root `CLAUDE.md` sitting over several
*independent* projects — routing ("what's where") rather than holding content — doesn't follow
it. It has its own pressure valve: an overgrown section moves into a dated diary
(`diary/YYYY-MM.md`) or a sibling role file (how the agent behaves, how the environment is set
up) — never into `memory/`, because a dispatcher root isn't "a project" in the sense this
methodology means.

If a project sits under a dispatcher root, exactly one line in that root `CLAUDE.md` says where
the diary lives (e.g. `Diary: diary/YYYY-MM.md`). No file below it repeats that line — a deep
`memory/<topic>.md` finds the diary transitively, by following its own backlink chain up through
its project's `CLAUDE.md` to the root that already states it. A standalone project (no dispatcher
above it) has no such requirement. See `docs/methodology.md` for the full split.

## The `[[wikilink]]` convention

Inside `memory/`, files reference each other *sideways* by slug, not by path: `[[debug-conventions]]`,
not `[debug](../debug/conventions.md)`. The slug comes from a `name:` field in the file's
frontmatter (falls back to the filename stem). This survives files moving around during a later
split — paths break, slugs don't. `cimble check --check-wikilinks` flags references that don't
resolve. (Backlinks, above, are the one mandatory *upward* pointer; wikilinks are optional
lateral references between topics.)

## Install

```bash
pip install cimble
```

Or install as a Claude Code plugin directly from this repo (adds the `cimble` skill and the
growth-threshold hook automatically).

## Usage

```bash
# Start a new project
cimble init my-project

# Once a section is worth carving out
cimble init my-project --topic backend

# Once the topic index itself needs its own file
cimble init my-project --index

# See what's over threshold, plus any broken backlinks
cimble check my-project

# Same, but exit non-zero if anything's over (for CI)
cimble check my-project --strict

# Also flag [[wikilinks]] that don't resolve
cimble check my-project --check-wikilinks
```

`create-memory` and `check-memory` work as aliases for `init` and `check`, if that's the name
you reach for.

Thresholds are configurable — CLI flag, then `CIMBLE_FILE_THRESHOLD` / `CIMBLE_SECTION_THRESHOLD`
/ `CIMBLE_STRICT` env vars, then a `cimble.toml` at the project root, then the 120/40 defaults.
Nothing is hardcoded to any one project's layout.

## As a hook

Installing this as a Claude Code plugin wires `cimble check` into `PostToolUse` on `Edit`/`Write`
— the moment an edit pushes a section, or a whole file, over threshold, you get a `systemMessage`
nudge (or, in `--strict`/`CIMBLE_STRICT` mode, an error Claude has to act on before continuing).
See `docs/methodology.md` for the full hook design and why `PostToolUse` beats a session-end
check for this specific job.

## Examples

`examples/` has generalized, structure-only illustrations of a project before and after it's
split — fictitious projects, no real data, just the shape.

## Docs

Full write-up — the diary, the promotion rule (diary → CLAUDE.md/memory, dated vs. undated
facts), `feedback_*` entries, backlinks, the diary anchor, lazy descent, the dispatcher-root
exception, and the hook design — lives in [`docs/methodology.md`](docs/methodology.md).

## License

MIT.
