# Runroom documentation

| Document | What it covers |
| --- | --- |
| [CLI reference](cli-reference.md) | Every `runroom` command, flag, and exit behavior |
| [Architecture](architecture.md) | Runs, participants, scopes, review gates, audit history |
| [Limitations](limitations.md) | Honest boundaries and deferred features |
| [Privacy](privacy.md) | Local-only posture; no telemetry |
| [Private exclusions](private-exclusions.md) | What deliberately lives outside this repo |
| [Integration contract](integration-contract.md) | Optional link to Citetrail |

Start with the [README](../README.md) quickstart, then run the demo with the
venv on `PATH`:

```bash
python3 -m venv .venv && .venv/bin/pip install -e .
PATH="$PWD/.venv/bin:$PATH" ./examples/demo.sh
```
