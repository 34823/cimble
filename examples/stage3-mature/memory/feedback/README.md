---
name: feedback-example
description: Example feedback entry — corrections carried forward so they aren't repeated.
---

Don't mock the datastore in integration tests.

**Why:** a mocked test passed while the real migration broke, and it shipped anyway.
**How to apply:** integration tests for `backend/` hit a real (test) datastore, never a mock.
