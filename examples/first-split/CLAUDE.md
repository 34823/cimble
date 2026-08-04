# CLAUDE.md

## What this is

A pair-trading backtester for forex: `ingest` pulls price data, `backtest` runs strategies
against stored data, `worker` executes live orders.

## How to run it

`docker compose up` — see the backend topic for what each service does.

## What not to do

Never restart the payments worker without draining its queue first — see the backend topic for
why.

## Topics

- [Backend](memory/backend.md) — service boundaries, why they're split this way, and the open
  question about `worker`'s datastore
