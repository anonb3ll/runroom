# Privacy and data handling

## Short version

Runroom runs on your machine. It has no hosted component, no account system,
and no telemetry. It does not phone home — not for usage counts, not for crash
reports, not for version checks.

## What Runroom stores

Locally, in the room directory you create with `runroom init`:

- run metadata: titles, notes, status, timestamps;
- participant identities: the labels and provider names you configure;
- the audit log: dispatches, claims, handoffs, review decisions, and their
  attribution;
- whatever your agents write into a run's notes.

That last item is the one to watch. If an agent pastes a secret, a customer
name, or a file's contents into a run, Runroom stores it verbatim in the ledger.

## What Runroom does not store

- Your model provider credentials. Runroom references credentials your agents
  already hold; it does not collect, proxy, or persist them.
- Your source code. Runroom records that an action happened, not a copy of your
  working tree.

## Network egress

Runroom itself makes no outbound requests. The agents you connect to it
obviously do — Runroom neither sees nor controls the traffic between an agent
and its provider.

## Before you share a ledger

A run ledger is a transcript. Review it before attaching one to a bug report.
Redaction tooling is on the roadmap, not in the box.

## Deleting data

Delete the room directory. There is no other copy.
