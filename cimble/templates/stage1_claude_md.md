<!-- cimble:stage1:v1 -->
# CLAUDE.md

<!-- Everything about {{PROJECT_NAME}} lives here while it stays under ~120 lines, and while no
     single `##` section below passes ~40 lines. Once a section outgrows that (or the file
     outgrows 120 lines even with every section under 40), carve that one section out:
     `cimble init --topic <slug>` scaffolds `memory/<slug>.md` with a correct backlink, then move
     the content and replace the section here with a one-line hook pointing at it. Run
     `cimble check` any time to see what's over. -->

## What this is

(One paragraph: what this project does.)

## How to run it

(Commands you actually reach for — dev server, tests, deploy. Keep these here even if this
section runs long — frequently-used operational content stays visible, it's not a candidate for
carving just because it's over the line count.)

## What not to do

(Hard constraints, footguns, things that must never happen.)

## Decisions worth remembering

(Short, dated notes on non-obvious choices. Promote durable facts here as you learn them —
undated for things that are just true, dated for things that changed: `Switched from polling
to webhooks — 2026-03-05`.)

## Topics

<!-- The index. One line per carved-out topic, specific enough to decide "open it or not"
     without opening it — same bar as a good MEMORY.md hook. Empty until something's carved out.
     If this section itself outgrows ~40 lines, carve it out too: `cimble init --index` scaffolds
     `memory/index.md` and this section shrinks to a single link pointing at it. -->
