↑ ../CLAUDE.md

# Backend

Three services: `ingest` (pulls price data), `backtest` (runs strategies against stored data),
`worker` (executes live orders). Split into services because `backtest` needs to run thousands
of times per experiment and shouldn't compete with `ingest`'s I/O.

Moved from a single monolith to three services — 2026-01-10. Backtests were queueing behind
ingest's network calls and taking 10x longer than necessary.

## Open questions

Whether `worker` should share a datastore with `backtest` or read through an API — currently
shares, works fine at current scale, revisit if `backtest` ever needs to scale independently.
