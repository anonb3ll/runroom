# Limitations

Written plainly, because the fastest way to waste your time is to discover these
after you have installed it.

## Not yet true

Runroom is pre-release. It installs from source and the documented workflow runs
end to end, but it is not on PyPI, interfaces will change without deprecation
cycles, and there is no upgrade path between pre-1.0 versions. Treat anything you
build against it as provisional.

There is no MCP server yet — agents drive Runroom through the CLI today.

## Deliberate boundaries

- **Local only.** One machine, one ledger. There is no server, no sync, and no
  way for two people on two machines to share a room today.
- **No autonomy layer.** Runroom will not decide what an agent should do next,
  retry failed work on its own, or escalate without being told to.
- **No sandbox.** Bounded handoffs constrain what a participant is *authorized*
  to do and record what it did. They are not an OS-level jail. An agent with
  shell access can exceed its stated scope; the audit log will show it, but
  Runroom will not have prevented it. Combine with your own isolation
  (containers, VMs, restricted credentials) for untrusted agents.
- **No provider adapters bundled.** Runroom coordinates identities; it does not
  ship integrations for every agent runtime. Connecting a new one is your work.
- **Human review is blocking by design.** A gate has no timeout that resolves to
  approval. If nobody reviews, the run waits. That is the intended failure mode.

## Known rough edges

- Failure and recovery paths are exercised by fixtures, but a crash mid-handoff
  can leave a run claimed until the claim expires.
- Audit history is append-only in the database: SQLite triggers reject UPDATE and
  DELETE on the events table. That stops application bugs and stray SQL. It does
  not stop an operator who deletes the whole file — ledger signing is a
  candidate, not a feature.
- Concurrency has been tested at a handful of participants, not at scale.

## Explicitly deferred

Enterprise governance packaging, hosted multi-tenancy, mobile clients, advanced
dashboards, automatic learning from past runs, broad autonomy, and any
compliance certification. These are deferred until there is evidence that people
use the core workflow — not because they are impossible.

## No claims made

Runroom makes no security, safety, or compliance certification claim, and no
claim about adoption or traction.
