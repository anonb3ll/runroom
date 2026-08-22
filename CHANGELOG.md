# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Public repository scaffold: README, Apache-2.0 license, contribution,
  security, privacy, limitations, and scope-exclusion documentation.
- Room core: participants (agents and humans, per-provider identities),
  runs, exclusive claims with leases, bounded handoffs, review gates with
  four outcomes, lease recovery, and credential isolation across providers.
- Append-only audit history, enforced by SQLite triggers.
- `runroom` CLI: init, agent/human add, task add, dispatch, handoff, act,
  submit, review, log (`--json`), recover, status.
- `runroom --version` and `python -m runroom` entry.
- `examples/demo.sh` — the README workflow end to end, run in CI.
- CI on Python 3.10, 3.12, and 3.13: ruff check, ruff format, pytest, demo,
  and a wheel install smoke test.

### Fixed
- CLI reference exit codes: recorded refusals (such as scope violations) exit
  `1`, matching the CLI and the README demo.

<!-- No release has been tagged yet. -->
