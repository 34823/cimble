# CLAUDE.md

## What this is

A pair-trading backtester for forex: `ingest` pulls price data, `backtest` runs strategies
against stored data, `worker` executes live orders.

## How to run it

`docker compose up` — see the backend topic for what each service does.

## What not to do

Never restart the payments worker without draining its queue first — see the backend topic for
why.

See [memory/index.md](memory/index.md) — the topic list itself outgrew this file, so it moved
there.
