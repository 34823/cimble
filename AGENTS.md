# Cimble

Python toolkit for progressive file-based project memory. This is a public repository;
never add real personal data, credentials, or private project examples.

- Developer guide: [docs/DEVELOPING.md](docs/DEVELOPING.md).
- Methodology: [docs/methodology.md](docs/methodology.md).
- Package: `cimble/`; regressions: `tests/`; adapters: `hooks/` and `cimble/codex_hook.py`.
- Run tests with `python -m pytest` in an environment with pytest installed.
- Keep thresholds configurable; defaults are not project-specific policy.
- `AGENTS.md` is the preferred project instruction file; legacy `CLAUDE.md` remains supported by the toolkit.
- Hooks warn, not rewrite memory. Exact-file optimization must not suppress scanning for opaque shell operations.
- Test fixtures must not modify live memory, settings, or production caches.
