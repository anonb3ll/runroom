# Runroom

**A shared room for one run: two agents, one human, one task ledger, full history.**

Runroom is an open-source coordination layer for multi-agent work. It lets two
or more AI agents — running on different providers, in different tools, under
different identities — work the same task without losing context or ownership,
and it puts a human review gate in front of anything that matters.

Every dispatch, handoff, approval, rejection, and remediation is recorded. When
you ask "who did this, on whose authority, and what did the reviewer see?",
Runroom has the answer.

- **Status:** pre-release. The public slice is being packaged now; see
  [Project status](#project-status) before you try to install it.
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

> Runroom is not yet published to PyPI. This section documents the intended
> first-run experience and will become executable with the first tagged
> release. Nothing here is a claim about what works today.

```bash
pip install runroom        # not yet available — see Project status
runroom init               # create a local room
runroom agent add reviewer --provider <provider>
runroom agent add worker   --provider <other-provider>
runroom task add "Fix the flaky auth test"
runroom dispatch <task-id> --to worker
runroom handoff <task-id> --to reviewer --scope read-only
runroom review <task-id>   # approve | reject | remediate | continue
runroom log <task-id>      # the full audit history
```

## Frequently asked questions

### How do I hand off a task from one AI agent to another?

Dispatch the run to the first agent, then hand it off with an explicit scope.
The receiving agent inherits the run's history and its bounded permissions, not
your whole environment. The handoff is recorded with both identities.

### How do I keep a human in the loop without babysitting every step?

Put review gates only where the cost of being wrong is real — merges, deploys,
external messages, credential use. Between gates the agents proceed on their
own. A gate blocks until a human resolves it; it does not time out into
approval.

### Does Runroom work across different model providers?

Yes. Participants are identities, not models. Two participants can run on
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

[Citetrail](https://github.com/citetrail/citetrail) gives agents local,
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

## License

[Apache License 2.0](LICENSE). Copyright 2026 The Runroom Contributors.
