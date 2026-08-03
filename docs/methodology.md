# Methodology

This is the full write-up behind `cimble`. The README has the short version; this is the "why"
and the edge cases.

## The three stages, in detail

**Stage 1 — one file.** A new project gets a single `CLAUDE.md`: what it is, how to run it, what
not to do, and a running list of decisions worth remembering (dated when they change, undated
for things that are just true — dating everything turns the file into a changelog). It stays
here as long as it fits in roughly 120 lines.

**Stage 2 — operations vs. rationale.** Once `CLAUDE.md` crosses ~120 lines, split it:
architecture and "why we did it this way" move to `memory/constitution.md`; `CLAUDE.md` keeps
only what gets read often — how to run it, what not to do — plus a link to the constitution.
`constitution.md` is not a dumping ground for everything that used to be in `CLAUDE.md`; the
split is a judgment call about what's operational (stays) vs. structural (moves), made per
project, not automated by cimble.

**Stage 3 — the constitution splits itself.** Once `constitution.md` crosses ~150 lines, it stops
being the content and becomes the index: one line per topic, linking into `memory/<topic>/`
files. Those topic files grow the same way stage 1→2 did, and split the same way if they
themselves get too long — the rule is recursive, and there's no fixed depth limit. `constitution.md`
never disappears; its role just keeps shrinking down to a table of contents.

Nothing here automates *what* moves where during a split. That's deliberate: the shape of a
split depends on the project, and guessing wrong is worse than leaving it manual. `cimble init`
scaffolds the skeleton for stages 1 and 2; stage 3 is convention and a template, not a generated
artifact.

## The diary

Day-to-day facts — what got built, changed, broken, fixed, shipped, decided — get logged
immediately to a dated diary (`diary/YYYY-MM.md`, one file per month), not to `CLAUDE.md`
directly. The diary is a staging area, not a destination.

## Promotion

Whatever gets written to the diary and turns out to be durable — still true weeks later, still
relevant — gets promoted into `CLAUDE.md` (stage 1) or the constitution (stage 2+). The diary is
the intake; the project file is what survived. If the two ever disagree, the project file wins —
it's the one that got revisited and kept.

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
doesn't follow the same stage-2/3 split.

Instead, a dispatcher root has its own release valve: an overgrown section moves out to a dated
diary entry, or to a sibling role file at the same level (how the agent should behave, how the
shared environment is set up) — never into a `memory/constitution.md`. The distinction matters
because a dispatcher root isn't supposed to grow structurally the way a single project does; it
stays a small, stable table of pointers, and pressure gets released sideways (into siblings)
rather than downward (into a nested `memory/`).

Concretely: if you have `/CLAUDE.md` routing between `/project-a/`, `/project-b/`, ... — that
root file follows the exception. `/project-a/CLAUDE.md` follows the normal three stages.

## The `[[wikilink]]` convention

Inside `memory/`, cross-references use `[[slug]]`, resolved against a `name:` field in each
file's frontmatter (falling back to the filename stem if there's no frontmatter). Linking by
slug instead of by relative path means a later stage-2→3 split — which moves files into new
subfolders — doesn't silently break every existing reference. `cimble check --check-wikilinks`
scans `memory/**/*.md`, builds the slug index, and flags any `[[target]]` that doesn't resolve.

This check is off by default (`--check-wikilinks`) — it's a hygiene tool, not a hard requirement,
and the slug-matching rules may need refinement as real usage turns up edge cases (links via a
path fragment instead of a slug, for instance).

## The hook: why `PostToolUse`, not `Stop`

A threshold breach is tied to one specific file at one specific edit. A `Stop` hook only fires
when the whole session ends — a file can sit over threshold for an entire long session before
anything says so. `PostToolUse` on `Edit`/`Write`, filtered to `CLAUDE.md`/`constitution.md`
paths, catches the breach at the moment it happens, and already has the file path from
`tool_input` — no need to rescan the whole project on every edit.

`PostToolUse` can't block an edit that already landed, but exit code 2 feeds `stderr` back to
Claude as an error it has to act on in the same turn — in practice as strong a nudge as a
blocking `Stop` hook, just faster and scoped to the file that actually crossed the line. Soft
mode (default) prints a `systemMessage` and exits 0; strict mode (`CIMBLE_STRICT=1`, or `strict =
true` in `cimble.toml`) prints to `stderr` and exits 2.

Edits made outside `Edit`/`Write` (e.g. `cat >> CLAUDE.md` via `Bash`) don't trigger
`PostToolUse` at all — for full coverage, pair the hook with `cimble check --strict` run as a
`Stop` hook once per session, or in CI.

## What's deliberately out of scope for v1

- Automating what content moves where during a stage split — a per-project judgment call, not
  something a tool should decide.
- A worked, organically-grown stage-3 example — every example in this repo is illustrative,
  built to show the shape, not a project that was actually observed crossing 150 lines and
  splitting on its own.
- Soft length checks for arbitrary topic files under `memory/<topic>/` — only `CLAUDE.md` and
  `constitution.md` have a stated threshold today; whether topic files need one too is an open
  question, not a silent decision.
