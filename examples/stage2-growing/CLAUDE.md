# CLAUDE.md

See [memory/constitution.md](memory/constitution.md) — architecture, rationale, and findings
live there.

## How to run it

`docker compose up` — see constitution for what each service does.

## What not to do

Never restart the payments worker without draining its queue first — see constitution for why.
