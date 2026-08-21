# CLI reference

All commands accept `--room PATH` (default: `.runroom`). The room directory holds
one SQLite ledger; never commit it.

## Lifecycle

| Command | Purpose |
| --- | --- |
| `runroom init` | Create a new room at `--room` |
| `runroom status` | List every run, holder, scope, and status |

## Participants

| Command | Purpose |
| --- | --- |
| `runroom agent add NAME --provider PROVIDER [--credential-ref REF] [--reviewer]` | Register an agent identity |
| `runroom human add NAME` | Register a human reviewer |

Two agents on the same provider are still two participants. Credentials are stored
as opaque references (`credential-ref`), never secret values.

## Runs

| Command | Purpose |
| --- | --- |
| `runroom task add TITLE...` | Create a run (words joined into the title) |
| `runroom dispatch RUN_ID --to AGENT [--lease SECONDS]` | Exclusive claim; default lease 3600s |
| `runroom handoff RUN_ID --to AGENT --by HOLDER --scope SCOPE` | Pass work with an explicit bound |
| `runroom act RUN_ID --by HOLDER --action ACTION [--note TEXT]` | Perform a permitted action |
| `runroom submit RUN_ID --by HOLDER [--summary TEXT]` | Open a review gate (blocks until resolved) |
| `runroom review RUN_ID --by REVIEWER --decision DECISION [--note TEXT]` | Resolve a gate |

### Scopes

| Scope | Permitted actions |
| --- | --- |
| `read-only` | `comment`, `submit` |
| `propose` | above + `propose-change` |
| `full` | above + `merge`, `deploy` |

Unknown scopes are refused. Refused actions are recorded as `scope-violation` before exit 1.

### Review decisions

`approve`, `reject`, `remediate`, `continue`. The submitter cannot review their own run.
Gates do not time out into approval.

## History and recovery

| Command | Purpose |
| --- | --- |
| `runroom log RUN_ID [--json]` | Append-only audit history |
| `runroom recover [--json]` | Release claims whose lease expired |

## Exit codes

- `0` — success (including intentional refusals that were recorded, e.g. scope violation on `act`)
- `1` — Runroom refused the command (`runroom: …` on stderr)

## Environment

No required environment variables. Runroom is fully local.
