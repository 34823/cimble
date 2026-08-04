# Methodology

This is the full write-up behind `cimble`. The README has the short version; this is the "why"
and the edge cases.

## The splitting rule, in detail

There is one rule, applied fractally to every `##` section of `CLAUDE.md` and every file it
spawns. There's no separate "stage 2" file type — a project either hasn't split yet (one
`CLAUDE.md`) or has (that `CLAUDE.md` plus a `memory/` tree), and both states are produced by the
same rule at different points.

**The unit is a section, not a file.** A new project gets a single `CLAUDE.md`: what it is, how
to run it, what not to do, a running list of decisions worth remembering, and a `## Topics`
section that starts empty. Each of those is a `##` section. A section stays inline as long as it
fits in roughly 40 lines. Cross that, and it's a candidate to carve out into `memory/<topic>.md`
— move the content, replace the section in `CLAUDE.md` with a one-line hook pointing at the new
file, add the hook under `## Topics`.

**The threshold is a trigger to review, not an order.** Content you reach for often — how to run
it, how to diagnose it, commands you use routinely — can stay past 40 lines; it's operational,
and keeping it one hop away from where you're already looking is worth more than the line count.
Rationale, history, and "why we did it this way" should move out even under 40 lines, because
nobody needs to re-read the reasoning every session. The split is a judgment call about frequency
of access, not something `cimble` automates or should guess at.

**The topic index is a section like any other.** `## Topics` in `CLAUDE.md` holds one line per
carved-out topic. While there are few topics, that list is short and stays inline. Once the list
itself crosses ~40 lines — meaning the project now has enough topics that even the *index* is
big — it carves out the same way everything else does, into `memory/index.md`. This isn't a
"stage 3" concept bolted on top; it's the identical rule applied to the section that happens to
contain links instead of prose. A file carved out of an index is no different in kind from a file
carved out of `CLAUDE.md` directly — the type is "carved-out topic file," full stop.

**There's a whole-file backstop, too.** If `CLAUDE.md` (or any file under `memory/`) crosses
~120 lines even though no single section is individually over 40, that's still a signal — five
35-line sections is a file worth revisiting even though the per-section rule never tripped.
`cimble check` flags this independently of the per-section check.

**Splitting content is manual; scaffolding the shape isn't.** `cimble init` writes the starting
`CLAUDE.md`. `cimble init --topic <slug>` writes `memory/<slug>.md` with a correctly formatted
backlink (to `memory/index.md` if one exists, otherwise to `CLAUDE.md`). `cimble init --index`
writes `memory/index.md`, backlinked to `CLAUDE.md`. None of these decide *what* content moves —
that's a per-project judgment call cimble deliberately leaves to you, the same way it always has.

## Backlinks

Every file `cimble` scaffolds under `memory/` starts with a fixed-format line:

```
↑ <relative path to whatever produced this file>
```

Exactly that format — no variation — because `cimble check` parses it with a regex, not prose
sniffing. Rules:

- The target must resolve to a file that exists. `cimble check` flags a backlink whose target
  doesn't resolve — this is the thing that would otherwise rot silently the first time a file
  gets renamed or moved.
- Following backlinks upward must terminate at a `CLAUDE.md` within 10 hops. A longer chain, or
  one that revisits a file it's already seen, is flagged as cyclic — almost always a copy-paste
  mistake when a file was scaffolded from an existing one.
- The tree has one parent per file. If a topic is genuinely relevant to two projects, it belongs
  at their true common ancestor (usually a dispatcher root's own memory, if that pattern applies)
  — not duplicated in both, which would desync the two copies over time.

This is deliberately mechanical rather than semantic — `cimble check` can tell you a backlink is
missing or broken, but it can't tell you a *hook* has gone stale (see below). Different problem,
different tool.

## The diary anchor

If a project sits under a dispatcher root (see below), the diary lives one level above the
project, and exactly one line in the root `CLAUDE.md` states where: `Diary: diary/YYYY-MM.md` (or
the Russian equivalent, `Дневник: ...`, if that's the working language — `cimble` doesn't enforce
a language, only that the line exists and is singular). No file below the root repeats it. A deep
`memory/<topic>.md`, opened cold, finds the diary transitively: follow its own backlink to
`memory/index.md`, that file's backlink to `CLAUDE.md`, and that file's backlink (if the project
sits under a dispatcher) to the root — which already documents the diary. The backlink chain that
exists for splitting also serves as the navigation path back, without a second mechanism.

A standalone project — no dispatcher root above it — has no diary-anchor requirement at all. This
is strictly a consequence of the dispatcher pattern, not a base requirement of the growth rule.

## Hooks that stay useful

A hook is the one line under `## Topics` (or in `memory/index.md`) that lets a reader decide
"open this file or not" without opening it. Whether a hook is still good is semantic — `cimble`
can't check it automatically — so the only real defense is holding new hooks to a visible
standard when they're written:

- Bad: "About the backend." Tells you the topic, not when it matters.
- Good: "Why retries are capped at 3, and what breaks if you raise it — read before touching the
  retry logic."

Hooks degrade over time as the file they point to changes and the hook doesn't. Treat "does this
hook still match its file" as a standing item in whatever periodic memory review a project
already does (see `feedback_*` entries, below, for the kind of review this project's own
`CLAUDE.md` should schedule).

## Reading it back: lazy descent

Splitting only saves context if reading it back doesn't undo the saving. The rule: stop at the
first level that answers the question.

1. Read `CLAUDE.md`. If it answers the task, stop — don't open `memory/` at all.
2. Descend one level only if `CLAUDE.md` doesn't have the answer *and* its `## Topics` section (or
   `memory/index.md`, if that's where the index carved out to) has a hook that specifically
   matches the task. Read exactly that one file.
3. Never read the `memory/` directory wholesale "just in case," and never read an index end to
   end looking for something — scan the hooks, match one, open exactly that.

This is a behavioral rule, not a structural one — nothing in the file format enforces it, and an
overcautious agent can always ignore it and read everything anyway. The only real mitigation is
making rule 2 actually usable: hooks specific enough that the decision doesn't require opening
the file to make. A vague hook doesn't just fail to help — it actively defeats the point, because
it forces the reader to open the file to find out.

## The diary

Day-to-day facts — what got built, changed, broken, fixed, shipped, decided — get logged
immediately to a dated diary (`diary/YYYY-MM.md`, one file per month), not to `CLAUDE.md`
directly. The diary is a staging area, not a destination.

## Promotion

Whatever gets written to the diary and turns out to be durable — still true weeks later, still
relevant — gets promoted into `CLAUDE.md`, or directly into a `memory/<topic>.md` if it's clearly
rationale rather than day-to-day operational content. The diary is the intake; the project file
is what survived. If the two ever disagree, the project file wins — it's the one that got
revisited and kept.

## `feedback_*` entries

When a correction lands — "don't do X", or a non-obvious choice gets explicitly confirmed as
right — it's worth writing down separately from the diary, because the "why" behind it is easy
to lose. A `feedback_*` entry has two required lines:

```
**Why:** the reason this rule exists — often a past incident or a strong, stated preference.
**How to apply:** when this should actually change behavior, so edge cases can be judged later.
```

Record confirmations, not just corrections — "yes, that approach was right" is just as useful
to remember as "no, don't do that," and confirmations are much easier to forget you ever
received.

## The root/dispatcher exception

Everything above describes **one project's** memory. A root `CLAUDE.md` that sits above several
*independent* projects — and whose job is routing ("here's where the Telegram bot lives, here's
where the backtester lives"), not holding content itself — is not "a project" in this sense, and
doesn't follow the same splitting rule.

Instead, a dispatcher root has its own release valve: an overgrown section moves out to a dated
diary entry, or to a sibling role file at the same level (how the agent should behave, how the
shared environment is set up) — never into a `memory/` tree. The distinction matters because a
dispatcher root isn't supposed to grow structurally the way a single project does; it stays a
small, stable table of pointers, and pressure gets released sideways (into siblings) rather than
downward (into a nested `memory/`).

Concretely: if you have `/CLAUDE.md` routing between `/project-a/`, `/project-b/`, ... — that
root file follows the exception, and it's the one place that states the diary anchor (see
above). `/project-a/CLAUDE.md` follows the normal splitting rule.

## The `[[wikilink]]` convention

Inside `memory/`, cross-references use `[[slug]]`, resolved against a `name:` field in each
file's frontmatter (falling back to the filename stem if there's no frontmatter). Linking by
slug instead of by relative path means a later split — which moves files into new subfolders —
doesn't silently break every existing reference. `cimble check --check-wikilinks` scans
`memory/**/*.md`, builds the slug index, and flags any `[[target]]` that doesn't resolve.

This check is off by default (`--check-wikilinks`) — it's a hygiene tool, not a hard requirement,
and the slug-matching rules may need refinement as real usage turns up edge cases (links via a
path fragment instead of a slug, for instance). Wikilinks are lateral, between topics; backlinks
(above) are the one mandatory upward pointer, and are checked unconditionally.

## The hook: why `PostToolUse`, not `Stop`

A threshold breach is tied to one specific file at one specific edit. A `Stop` hook only fires
when the whole session ends — a file can sit over threshold for an entire long session before
anything says so. `PostToolUse` on `Edit`/`Write`, filtered to `CLAUDE.md`/`memory/*.md` paths,
catches the breach at the moment it happens, and already has the file path from `tool_input` — no
need to rescan the whole project on every edit.

`PostToolUse` can't block an edit that already landed, but exit code 2 feeds `stderr` back to
Claude as an error it has to act on in the same turn — in practice as strong a nudge as a
blocking `Stop` hook, just faster and scoped to the file that actually crossed the line. Soft
mode (default) prints a `systemMessage` and exits 0; strict mode (`CIMBLE_STRICT=1`, or `strict =
true` in `cimble.toml`) prints to `stderr` and exits 2.

Edits made outside `Edit`/`Write` (e.g. `cat >> CLAUDE.md` via `Bash`) don't trigger
`PostToolUse` at all — for full coverage, pair the hook with `cimble check --strict` run as a
`Stop` hook once per session, or in CI.

## What's deliberately out of scope for v1

- Automating what content moves where during a split — a per-project judgment call, not
  something a tool should decide.
- Judging whether a hook is still accurate — semantic, not mechanical; `cimble check` only
  verifies backlinks resolve, not that hooks describe their target correctly.
- A worked, organically-grown deep-split example — every example in this repo is illustrative,
  built to show the shape, not a project that was actually observed crossing thresholds and
  splitting on its own.
- Detecting the dispatcher-root pattern automatically to enforce the diary-anchor rule — `cimble
  check` doesn't try to guess whether a `CLAUDE.md` is a dispatcher root; the diary anchor is a
  convention to follow, not (yet) something the tool verifies.
