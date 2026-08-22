# Contributing to Runroom

Thanks for looking. Runroom is pre-1.0 and released to test whether it solves a
real problem — so a clear bug report or a description of the workflow you were
trying to run is worth as much as a patch.

## Before you start

- Read [docs/limitations.md](docs/limitations.md). Some gaps are deliberate.
- Read [docs/private-exclusions.md](docs/private-exclusions.md). Some features
  exist elsewhere and are intentionally out of scope here; PRs that pull them in
  will be declined regardless of quality.
- For anything larger than a bug fix, open an issue first and describe the
  workflow you want to work. Interfaces are still moving.

## Ground rules

1. **Never weaken a gate to make a test pass.** Claims, bounded scopes, review
   gates, and audit records are the product. If one of them is inconvenient,
   that is a design discussion, not a patch.
2. **The audit log is append-only.** No feature may edit or delete history.
3. **No silent network calls.** Runroom is local. Any code that opens a socket
   needs an explicit, documented reason and an opt-in.
4. **No secrets in the repo** — not in tests, not in fixtures, not in examples.
5. **Tests first for behavior changes.** A bug fix comes with a test that fails
   without it.

## Development setup

```bash
git clone https://github.com/anonb3ll/runroom
cd runroom
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest -q
PATH="$PWD/.venv/bin:$PATH" ./examples/demo.sh
```

All four must pass before you open a PR. CI runs exactly these. If you use
[uv](https://github.com/astral-sh/uv), `uv.lock` is present for a reproducible
dev install (`uv sync --extra dev`).

## Pull requests

- One logical change per PR, with a description of what a reviewer should try.
- Include the commands you ran and their output. "Tests pass" is not evidence;
  the output is.
- Say plainly what you did not test.
- Conventional Commit subject lines (`fix:`, `feat:`, `docs:`, `chore:`).

## Reporting bugs

Use the bug template. The three things that make a report actionable: what you
expected, what happened, and the smallest sequence of commands that reproduces
it.

## Security

Do not open a public issue. See [SECURITY.md](SECURITY.md).

## License

By contributing you agree that your contributions are licensed under the
[Apache License 2.0](LICENSE).
