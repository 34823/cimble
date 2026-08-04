↑ index.md

---
name: backend
---

# Backend

Service boundaries: `ingest`, `backtest`, `worker` — split 2026-01-10 because backtests were
queueing behind ingest's network I/O. See [[no-mock-datastore]] for the testing convention that
applies to this service split.
