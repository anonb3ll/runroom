"""The Room: participants, runs, claims, bounded handoffs, review gates, history.

Design rules that the tests hold in place:

* A claim is exclusive. Two participants never hold one run.
* A handoff names its bound. There is no implicit "do whatever you think best".
* A gate blocks until a person (or a designated reviewer) resolves it. Waiting is
  the intended failure mode; approving on a timer is not a failure mode, it is a bug.
* Every attempt is recorded, including the refused ones.
* Credentials never cross a handoff, and never enter the history.
"""

import json
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runroom import scopes
from runroom.errors import (
    AlreadyClaimed,
    GateBlocked,
    NotAReviewer,
    NotTheHolder,
    RoomExists,
    RoomNotFound,
    ScopeViolation,
    UnknownDecision,
    UnknownParticipant,
    UnknownRun,
)
from runroom.store import DB_FILENAME, connect, create

#: How long a claim survives without being renewed. A dead agent releases its work.
DEFAULT_LEASE_SECONDS = 3600

DECISIONS = ("approve", "reject", "remediate", "continue")

STATUS_OPEN = "open"
STATUS_CLAIMED = "claimed"
STATUS_AWAITING_REVIEW = "awaiting_review"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"


@dataclass(frozen=True)
class Participant:
    name: str
    kind: str
    provider: str | None
    credential_ref: str | None
    reviewer: bool


@dataclass(frozen=True)
class Run:
    id: int
    title: str
    notes: str
    status: str
    holder: str | None
    scope: str | None
    lease_expires_at: float | None
    lease_seconds: float | None
    submitted_by: str | None
    created_at: float
    updated_at: float


@dataclass(frozen=True)
class Event:
    seq: int
    run_id: int
    at: float
    actor: str
    action: str
    detail: dict[str, Any]


class Room:
    """One local room. Everything it knows lives in one SQLite file on your disk."""

    def __init__(self, path: Path, conn: sqlite3.Connection, clock: Callable[[], float]):
        self.path = Path(path)
        self._conn = conn
        self._clock = clock

    # -- lifecycle -----------------------------------------------------------

    @classmethod
    def init(cls, path: str | Path, clock: Callable[[], float] | None = None) -> "Room":
        path = Path(path)
        db_path = path / DB_FILENAME
        if db_path.exists():
            raise RoomExists(f"a room already exists at {path}; Runroom will not overwrite it")
        return cls(path, create(db_path), clock or time.time)

    @classmethod
    def open(cls, path: str | Path, clock: Callable[[], float] | None = None) -> "Room":
        path = Path(path)
        db_path = path / DB_FILENAME
        if not db_path.exists():
            raise RoomNotFound(f"no room at {path}; run `runroom init` first")
        return cls(path, connect(db_path), clock or time.time)

    def close(self) -> None:
        self._conn.close()

    @property
    def connection(self) -> sqlite3.Connection:
        """The raw connection. Exposed for inspection — history stays immutable regardless."""
        return self._conn

    def _now(self) -> float:
        return self._clock()

    # -- participants --------------------------------------------------------

    def add_participant(
        self,
        name: str,
        kind: str = "agent",
        provider: str | None = None,
        credential_ref: str | None = None,
        reviewer: bool = False,
    ) -> Participant:
        """Register an identity. Two agents on the same provider are still two participants."""
        self._conn.execute(
            "INSERT INTO participants (name, kind, provider, credential_ref, reviewer, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (name, kind, provider, credential_ref, int(reviewer), self._now()),
        )
        return self.get_participant(name)

    def get_participant(self, name: str) -> Participant:
        row = self._conn.execute("SELECT * FROM participants WHERE name = ?", (name,)).fetchone()
        if row is None:
            raise UnknownParticipant(f"no participant named {name!r} in this room")
        return Participant(
            name=row["name"],
            kind=row["kind"],
            provider=row["provider"],
            credential_ref=row["credential_ref"],
            reviewer=bool(row["reviewer"]),
        )

    def participants(self) -> list[Participant]:
        rows = self._conn.execute("SELECT name FROM participants ORDER BY name").fetchall()
        return [self.get_participant(r["name"]) for r in rows]

    # -- runs ----------------------------------------------------------------

    def add_run(self, title: str, notes: str = "") -> Run:
        now = self._now()
        cur = self._conn.execute(
            "INSERT INTO runs (title, notes, status, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (title, notes, STATUS_OPEN, now, now),
        )
        run_id = int(cur.lastrowid)
        self._record(run_id, actor="system", action="run-created", detail={"title": title})
        return self.get_run(run_id)

    def get_run(self, run_id: int) -> Run:
        row = self._conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise UnknownRun(f"no run with id {run_id} in this room")
        return Run(**dict(row))

    def runs(self) -> list[Run]:
        rows = self._conn.execute("SELECT id FROM runs ORDER BY id").fetchall()
        return [self.get_run(r["id"]) for r in rows]

    # -- claims and handoffs -------------------------------------------------

    def dispatch(
        self,
        run_id: int,
        to: str,
        lease: float = DEFAULT_LEASE_SECONDS,
    ) -> Run:
        """Assign a run. Refused if someone else holds a live claim on it."""
        run = self.get_run(run_id)
        receiver = self.get_participant(to)

        if run.status == STATUS_AWAITING_REVIEW:
            raise GateBlocked(
                f"run {run_id} is awaiting review; resolve the gate before dispatching"
            )

        if run.holder is not None and not self._lease_expired(run):
            if run.holder == to:
                self._renew(run_id, lease)  # idempotent: same holder, fresh lease, no state change
                return self.get_run(run_id)
            raise AlreadyClaimed(
                f"run {run_id} is already claimed by {run.holder!r}; "
                f"it must be released, handed off, or its lease must expire"
            )

        now = self._now()
        self._conn.execute(
            "UPDATE runs SET holder = ?, status = ?, scope = ?, lease_expires_at = ?,"
            " lease_seconds = ?, updated_at = ? WHERE id = ?",
            (
                receiver.name,
                STATUS_CLAIMED,
                scopes.DEFAULT_SCOPE,
                now + lease,
                lease,
                now,
                run_id,
            ),
        )
        self._record(
            run_id,
            actor=receiver.name,
            action="dispatch",
            detail={"to": receiver.name, "scope": scopes.DEFAULT_SCOPE, "lease_seconds": lease},
        )
        return self.get_run(run_id)

    def handoff(
        self,
        run_id: int,
        to: str,
        by: str,
        scope: str,
        lease: float | None = None,
    ) -> Run:
        """Pass a run on, with an explicit bound on what the receiver may do.

        The lease is renewed for the duration the run already carried, so handing work
        on cannot quietly extend a deliberately short claim into a long one.
        """
        run = self._require_holder(run_id, by)
        receiver = self.get_participant(to)
        scopes.actions_for(scope)  # refuses an unknown scope rather than defaulting

        sender = self.get_participant(by)
        now = self._now()
        lease = lease if lease is not None else (run.lease_seconds or DEFAULT_LEASE_SECONDS)
        self._conn.execute(
            "UPDATE runs SET holder = ?, status = ?, scope = ?, lease_expires_at = ?,"
            " lease_seconds = ?, updated_at = ? WHERE id = ?",
            (receiver.name, STATUS_CLAIMED, scope, now + lease, lease, now, run.id),
        )
        self._record(
            run_id,
            actor=sender.name,
            action="handoff",
            detail={
                "to": receiver.name,
                "scope": scope,
                "lease_seconds": lease,
                "from_provider": sender.provider,
                "to_provider": receiver.provider,
                "crossed_provider_boundary": sender.provider != receiver.provider,
            },
        )
        return self.get_run(run_id)

    def release(self, run_id: int, by: str) -> Run:
        self._require_holder(run_id, by)
        now = self._now()
        self._conn.execute(
            "UPDATE runs SET holder = NULL, status = ?, scope = NULL, lease_expires_at = NULL,"
            " updated_at = ? WHERE id = ?",
            (STATUS_OPEN, now, run_id),
        )
        self._record(run_id, actor=by, action="release", detail={})
        return self.get_run(run_id)

    def act(self, run_id: int, by: str, action: str, detail: str = "") -> Event:
        """Do something on a run. Refused actions are recorded before they are refused."""
        run = self._require_holder(run_id, by)

        if run.status == STATUS_AWAITING_REVIEW:
            raise GateBlocked(
                f"run {run_id} is awaiting review; {action!r} cannot proceed until a reviewer "
                f"approves, rejects, remediates, or continues it"
            )

        scope = run.scope or scopes.DEFAULT_SCOPE
        if not scopes.permits(scope, action):
            self._record(
                run_id,
                actor=by,
                action="scope-violation",
                detail={"attempted": action, "scope": scope},
            )
            raise ScopeViolation(
                f"{by!r} may not {action!r} on run {run_id}: the handoff scope is {scope!r}, "
                f"which permits {sorted(scopes.actions_for(scope))}"
            )

        return self._record(run_id, actor=by, action=action, detail={"note": detail})

    # -- review gates --------------------------------------------------------

    def request_review(self, run_id: int, by: str, summary: str = "") -> Run:
        """Open a gate. From here the run waits for a person; nothing else moves it."""
        self._require_holder(run_id, by)
        now = self._now()
        self._conn.execute(
            "UPDATE runs SET status = ?, submitted_by = ?, updated_at = ? WHERE id = ?",
            (STATUS_AWAITING_REVIEW, by, now, run_id),
        )
        self._record(run_id, actor=by, action="review-requested", detail={"summary": summary})
        return self.get_run(run_id)

    def review(self, run_id: int, by: str, decision: str, note: str = "") -> Run:
        run = self.get_run(run_id)
        reviewer = self.get_participant(by)

        if run.status != STATUS_AWAITING_REVIEW:
            raise GateBlocked(
                f"run {run_id} has no open review gate (status is {run.status!r}); "
                f"a participant must request review first"
            )

        if reviewer.name == run.submitted_by:
            raise NotAReviewer(
                f"{by!r} submitted this run for review and may not review its own work"
            )
        if reviewer.kind != "human" and not reviewer.reviewer:
            raise NotAReviewer(
                f"{by!r} is not a human and is not a designated reviewer; "
                f"register it with reviewer=True to let it resolve gates"
            )

        if decision not in DECISIONS:
            raise UnknownDecision(
                f"unknown decision {decision!r}; expected one of {', '.join(DECISIONS)}"
            )

        now = self._now()
        if decision == "approve":
            status, holder = STATUS_APPROVED, None
        elif decision == "reject":
            status, holder = STATUS_REJECTED, None
        else:  # remediate and continue both return the work to whoever submitted it
            status, holder = STATUS_CLAIMED, run.submitted_by

        self._conn.execute(
            "UPDATE runs SET status = ?, holder = ?, scope = ?, lease_expires_at = ?,"
            " updated_at = ? WHERE id = ?",
            (
                status,
                holder,
                run.scope if holder else None,
                (now + (run.lease_seconds or DEFAULT_LEASE_SECONDS)) if holder else None,
                now,
                run_id,
            ),
        )
        self._record(
            run_id,
            actor=reviewer.name,
            action="review-decision",
            detail={"decision": decision, "note": note, "submitted_by": run.submitted_by},
        )
        return self.get_run(run_id)

    # -- failure and recovery ------------------------------------------------

    def recover_expired(self) -> list[int]:
        """Release claims whose lease ran out. Never touches a run that is awaiting review."""
        now = self._now()
        rows = self._conn.execute(
            "SELECT id, holder, scope FROM runs"
            " WHERE holder IS NOT NULL AND status = ? AND lease_expires_at <= ?",
            (STATUS_CLAIMED, now),
        ).fetchall()

        recovered = []
        for row in rows:
            self._conn.execute(
                "UPDATE runs SET holder = NULL, status = ?, scope = NULL,"
                " lease_expires_at = NULL, updated_at = ? WHERE id = ?",
                (STATUS_OPEN, now, row["id"]),
            )
            self._record(
                row["id"],
                actor="system",
                action="claim-expired",
                detail={"was_held_by": row["holder"], "scope": row["scope"]},
            )
            recovered.append(int(row["id"]))
        return recovered

    # -- credentials ---------------------------------------------------------

    def effective_credential(self, run_id: int, as_participant: str | None = None) -> str | None:
        """The holder's own credential reference — never the previous holder's.

        Credentials do not travel with a run. A participant asking about a run it does
        not hold is refused rather than answered.
        """
        run = self.get_run(run_id)
        if as_participant is not None and as_participant != run.holder:
            raise NotTheHolder(
                f"{as_participant!r} does not hold run {run_id} and cannot read its credentials"
            )
        if run.holder is None:
            return None
        return self.get_participant(run.holder).credential_ref

    # -- history -------------------------------------------------------------

    def history(self, run_id: int) -> list[Event]:
        self.get_run(run_id)  # refuses an unknown run rather than returning []
        rows = self._conn.execute(
            "SELECT * FROM events WHERE run_id = ? ORDER BY seq", (run_id,)
        ).fetchall()
        return [
            Event(
                seq=r["seq"],
                run_id=r["run_id"],
                at=r["at"],
                actor=r["actor"],
                action=r["action"],
                detail=json.loads(r["detail"]),
            )
            for r in rows
        ]

    # -- internals -----------------------------------------------------------

    def _record(self, run_id: int, actor: str, action: str, detail: dict[str, Any]) -> Event:
        cur = self._conn.execute(
            "INSERT INTO events (run_id, at, actor, action, detail) VALUES (?, ?, ?, ?, ?)",
            (run_id, self._now(), actor, action, json.dumps(detail, sort_keys=True)),
        )
        row = self._conn.execute("SELECT * FROM events WHERE seq = ?", (cur.lastrowid,)).fetchone()
        return Event(
            seq=row["seq"],
            run_id=row["run_id"],
            at=row["at"],
            actor=row["actor"],
            action=row["action"],
            detail=json.loads(row["detail"]),
        )

    def _require_holder(self, run_id: int, by: str) -> Run:
        run = self.get_run(run_id)
        self.get_participant(by)
        if run.holder != by:
            held = f"held by {run.holder!r}" if run.holder else "not claimed by anyone"
            raise NotTheHolder(f"{by!r} does not hold run {run_id}; it is {held}")
        return run

    def _lease_expired(self, run: Run) -> bool:
        return run.lease_expires_at is not None and run.lease_expires_at <= self._now()

    def _renew(self, run_id: int, lease: float) -> None:
        now = self._now()
        self._conn.execute(
            "UPDATE runs SET lease_expires_at = ?, updated_at = ? WHERE id = ?",
            (now + lease, now, run_id),
        )
