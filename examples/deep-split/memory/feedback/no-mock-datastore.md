↑ index.md

---
name: no-mock-datastore
---

# No mocked datastore in integration tests

**Why:** a mocked test passed while the real migration broke, and it shipped anyway.
**How to apply:** integration tests for `backend/` hit a real (test) datastore, never a mock.
