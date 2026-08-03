# Backend

Service boundaries: `ingest`, `backtest`, `worker` — split 2026-01-10 because backtests were
queueing behind ingest's network I/O. See `constitution.md` for the short version; this file is
where backend-specific detail accumulates once the index entry alone isn't enough.
