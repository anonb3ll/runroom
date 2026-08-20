# Scope exclusions

Runroom is a focused public slice, extracted from a larger private system that
its maintainers run day to day. This page states plainly what is **not** in this
repository, so you can tell a missing feature from a deliberate omission — and
so nobody files a PR against work that was never meant to land here.

## Not included, and not planned for this repo

- **Private workspace integrations.** Personal knowledge vaults, private note
  stores, and host-specific configuration.
- **The maintainers' own operational deployment.** Service definitions, hub
  topology, tokens, audit-root configuration, and machine inventories.
- **Private memory and retrieval systems.** The semantic memory plane the
  private system uses for cross-session recall.
- **Proprietary or personal data of any kind.** No real run ledgers, no real
  identities, no customer or employer material. Every fixture in this repo is
  synthetic.
- **Business logic from unrelated private projects.**

## Deferred, and reconsidered only with evidence

- Enterprise governance packaging and policy bundles
- Hosted or multi-tenant operation
- Mobile clients
- Advanced dashboards and reporting
- Automatic learning from prior runs
- Broad autonomous operation without gates
- Compliance certification of any kind

## Why the split exists

Runroom is a public validation slice, not a copy of a private system with the
names changed. The coordination primitives — identities, claims, bounded
handoffs, review gates, audit history — are the part that might be generally
useful. The rest is one person's operational setup and does not belong in
anyone else's repository.

If you need one of the deferred items, open an issue describing the workflow it
would unblock. Use cases move this list; requests on their own do not.
