# CLAUDE.md

## What this is

A small Telegram bot that posts a daily digest. Single script, single cron job.

## How to run it

`python bot.py` — reads `TOKEN` from env. Cron runs it once a day via systemd timer.

## What not to do

Don't add a database. The digest is stateless by design — recomputing from source is cheaper
than keeping state in sync.

## Decisions worth remembering

Switched from polling to a systemd timer — 2026-02-01. Polling kept the process alive for no
reason; the job runs once, does its thing, exits.

## Topics

<!-- Empty — nothing has grown enough to carve out yet. -->
