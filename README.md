# Runroom

**A shared room for one run: two agents, one human, one task ledger, full history.**

Runroom is an open-source coordination layer for multi-agent work. It lets two
or more AI agents — running on different providers, in different tools, under
different identities — work the same task without losing context or ownership,
and it puts a human review gate in front of anything that matters.

Every dispatch, handoff, approval, rejection, and remediation is recorded. When
you ask "who did this, on whose authority, and what did the reviewer see?",
Runroom has the answer.

- **Status:** pre-release, installable from source. Not on PyPI yet; see
  [Project status](#project-status).
- **License:** [Apache-2.0](LICENSE)
- **Runs locally.** No hosted service, no account, no telemetry.

---

## The problem Runroom solves

You have more than one coding agent. One of them starts a task, hits the edge of
what it should decide alone, and stops — or worse, doesn't stop. Handing that
work to a second agent means re-explaining everything. Handing it to a human
means a Slack message with no state attached. Nothing records who approved what.

Runroom makes the handoff itself a first-class object:

| Without Runroom | With Runroom |
| --- | --- |
| Context is re-pasted between agents | The run carries its own context |
| Ownership is implied by whoever spoke last | Ownership is claimed, held, and released explicitly |
| Human approval happens in chat, unrecorded | Approval is a gate with a recorded decision |
| "Which agent changed this?" is unanswerable | Every action is attributed and timestamped |
| Autonomy is all-or-nothing | Autonomy is bounded per handoff |

## Core concepts

- **Run** — one unit of work with a shared, append-only history.
- **Participant** — an agent identity or a human, each with its own credentials
  and its own permitted actions. Two agents on the same provider are still two
  participants.
- **Dispatch** — assigning a run to a participant. Claims are exclusive, so two
  agents cannot silently work the same task.
- **Bounded handoff** — passing a run to another participant along with an
  explicit scope: what the receiver may do, and where it must stop.
- **Review gate** — a point where a human (or a designated reviewing agent)
  must choose: **approve**, **reject**, **remediate**, or **continue**.
- **Audit history** — the immutable record of all of the above.

## Quickstart

Runroom is not on PyPI yet. Install from source — this path is exercised in CI on
every commit, so it works today:

```bash
git clone https://github.com/anonb3ll/runroom
cd runroom
python3 -m venv .venv && .venv/bin/pip install -e .
export PATH="$PWD/.venv/bin:$PATH"
```

Then run the whole workflow. `./examples/demo.sh` does exactly this, end to end,
in a temporary directory:

```bash
runroom --room ./myroom init

# Two agents on two different providers, and a human who can resolve gates.
runroom --room ./myroom agent add worker --provider provider-a
runroom --room ./myroom agent add second --provider provider-b
runroom --room ./myroom human add anna

# One run, dispatched, then handed on with an explicit bound.
runroom --room ./myroom task add "Fix the flaky auth test"
runroom --room ./myroom dispatch 1 --to worker
runroom --room ./myroom handoff 1 --to second --by worker --scope read-only

# read-only permits comment and submit. Anything else is refused and recorded.
runroom --room ./myroom act 1 --by second --action merge      # exits 1
runroom --room ./myroom act 1 --by second --action comment --note "CI 4821 green"

# The gate. It blocks until a person resolves it.
runroom --room ./myroom submit 1 --by second --summary "auth test fixed"
runroom --room ./myroom review 1 --by anna --decision remediate --note "add a test"
runroom --room ./myroom review 1 --by anna --decision approve

runroom --room ./myroom log 1        # the full history, --json for machines
runroom --room ./myroom status       # every run and who holds it
```

The history that produces is the point:

```
   1  system       run-created        {"title": "Fix the flaky auth test"}
   2  worker       dispatch           {"scope": "full", "to": "worker"}
   3  worker       handoff            {"crossed_provider_boundary": true, "scope": "read-only", ...}
   4  second       scope-violation    {"attempted": "merge", "scope": "read-only"}
   5  second       comment            {"note": "CI 4821 green"}
   6  second       review-requested   {"summary": "auth test fixed"}
   7  anna         review-decision    {"decision": "remediate", "note": "add a test", ...}
   8  second       review-requested   {"summary": "regression test added"}
   9  anna         review-decision    {"decision": "approve", ...}
```

Note line 4. The refused action is in the record — a blocked attempt is evidence,
and dropping it would hide the case you most want to see.

## Documentation

| Guide | Description |
| --- | --- |
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/cli-reference.md](docs/cli-reference.md) | Full CLI reference |
| [docs/architecture.md](docs/architecture.md) | Runs, scopes, gates, audit model |
| [docs/limitations.md](docs/limitations.md) | Honest boundaries |
| [docs/integration-contract.md](docs/integration-contract.md) | Optional Citetrail integration |

## Frequently asked questions

### How do I hand off a task from one AI agent to another?

`runroom dispatch <id> --to <agent>`, then
`runroom handoff <id> --to <other-agent> --by <agent> --scope <scope>`.
The receiving agent inherits the run's history and its bounded permissions, not
your whole environment. The handoff is recorded with both identities.

### How do I keep a human in the loop without babysitting every step?

`runroom submit` opens a gate; `runroom review --decision approve|reject|remediate|continue`
closes it. Put gates only where the cost of being wrong is real — merges, deploys,
external messages, credential use. Between gates the agents proceed on their
own. A gate blocks until a human resolves it; it does not time out into
approval.

### Does Runroom work across different model providers?

Yes. Participants are identities, not models. Each handoff records
`crossed_provider_boundary`, and credentials never travel with a run. Two participants can run on
different providers, and the provider boundary is enforced and recorded — an
agent's credentials are not shared with the participant it hands off to.

### Does my code or data leave my machine?

No. Runroom runs locally and stores its ledger locally. It has no hosted
component and sends no telemetry. See [docs/privacy.md](docs/privacy.md).

### Is this an agent framework?

No. Runroom does not write prompts, choose models, or run inference. Bring your
own agents — Claude Code, Codex, or anything that can call a CLI or an MCP
server — and Runroom coordinates them.

### How is this different from a task queue?

A task queue moves work. Runroom moves work *and* the authority to do it, and
records both. Claims, bounded scopes, review gates, and attribution are the
product; the queue is an implementation detail.

## What Runroom is not

- Not a hosted service, and not a multi-tenant SaaS.
- Not an autonomy system. It does not decide what agents should do next.
- Not a compliance product. Runroom makes no certification claim of any kind.
- Not a replacement for your CI, your VCS, or your agent runtime.
- Not a mobile app.

See [docs/limitations.md](docs/limitations.md) for the honest boundaries, and
[docs/private-exclusions.md](docs/private-exclusions.md) for what deliberately
lives outside this repo.

## Related project

[Citetrail](https://github.com/anonb3ll/citetrail) gives agents local,
provenance-backed recall of what your browser saw. The two projects are
independent and neither requires the other; an optional integration
demonstrates Citetrail references feeding a governed Runroom task.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Security reports go to
[SECURITY.md](SECURITY.md) — please do not open a public issue for a
vulnerability.

## Project status

Pre-release, pre-1.0. Interfaces will change. Runroom is being released to find
out whether the problem it solves is a problem other people have — if you try
it, the most useful thing you can send back is what you were trying to do and
where it stopped working.

Published at [github.com/anonb3ll/runroom](https://github.com/anonb3ll/runroom).
Organization migration to `runroom-dev` is planned once the GitHub org is created.

## License

[Apache License 2.0](LICENSE). Copyright 2026 The Runroom Contributors.
