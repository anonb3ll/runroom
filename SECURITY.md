# Security Policy

## Supported versions

Runroom is pre-1.0. Only the latest commit on the default branch is supported.
There are no backported security fixes yet.

## Reporting a vulnerability

**Do not open a public issue.**

Report privately through GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
on this repository. Include:

- what an attacker can do, and what access they need to start;
- the smallest reproduction you have;
- affected commit or version.

You will get an acknowledgement within 7 days. Runroom is maintained by a small
team, so please allow reasonable time for a fix before disclosing publicly.

## What is in scope

- Bypassing a review gate, a claim, or a bounded handoff scope.
- Tampering with, truncating, or forging audit history.
- Leaking one participant's credentials to another participant.
- Escaping the configured workspace boundary during a run.
- Any unintended network egress.

## What is out of scope

- Anything a participant is explicitly authorized to do. Runroom bounds
  agents; it does not sandbox a hostile operator on your own machine.
- Vulnerabilities in the agents, models, or providers you connect to Runroom.
- Findings from automated scanners with no demonstrated impact.

## Threat model, briefly

Runroom assumes the machine and the human operator are trusted, and that
connected agents are **capable but not trustworthy** — they may be wrong,
manipulated by content they read, or overconfident. Gates, bounded scopes, and
an append-only audit log exist for that case. Runroom makes no compliance or
certification claim.
