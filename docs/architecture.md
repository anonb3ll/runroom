# Architecture

Runroom is a **local coordination ledger** for multi-agent work. It is not an agent
runtime, model router, or hosted service.

## Components

```
┌─────────────┐     CLI / future MCP     ┌──────────────────┐
│ Your agents │ ───────────────────────► │ Runroom Room     │
│ + humans    │                          │ (SQLite ledger)  │
└─────────────┘                          └──────────────────┘
```

- **Room** — one directory with a single `runroom.db` file.
- **Participant** — a named identity (`agent` or `human`) with optional provider and credential reference.
- **Run** — one unit of work with title, notes, status, current holder, and scope.
- **Event** — append-only audit row: actor, action, JSON detail, monotonic sequence.

## State machine (simplified)

```
open ──dispatch──► claimed ──submit──► awaiting_review
  ▲                    │                      │
  │                    │ handoff              │ review
  │                    ▼                      ▼
  └──recover/expiry──┘              approved / rejected
                                      (or back to claimed on remediate/continue)
```

## Design invariants

1. **Exclusive claims** — at most one live holder per run.
2. **Named scopes** — handoffs must specify `read-only`, `propose`, or `full`; no implicit escalation.
3. **Blocking gates** — `awaiting_review` waits until a human or designated reviewer acts.
4. **Append-only history** — SQLite triggers reject UPDATE/DELETE on `events`.
5. **Credential isolation** — credentials never travel with a handoff; each holder uses their own ref.
6. **Recorded refusals** — scope violations and gate blocks are evidence, not silent failures.

## Provider boundaries

Each agent registers a `provider` string (opaque to Runroom). Handoffs record
`crossed_provider_boundary` when sender and receiver differ. Runroom does not
exchange API keys or spawn subprocesses — it only records who held authority when.

## What Runroom does not do

See [limitations.md](limitations.md): no OS sandbox, no autonomy layer, no sync,
no MCP server in v0.1 (CLI is the integration surface today).
