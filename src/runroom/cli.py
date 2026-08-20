"""The `runroom` command line. This is the demo path, so it stays boring on purpose.

Every refusal prints why it was refused and exits 1. Nothing here decides anything
on your behalf.
"""

import argparse
import json
import sys
from pathlib import Path

from runroom.errors import RunroomError
from runroom.room import Room

DEFAULT_ROOM = ".runroom"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="runroom",
        description="Governed handoffs between AI agents and humans.",
    )
    parser.add_argument(
        "--room",
        default=DEFAULT_ROOM,
        help=f"path to the room directory (default: {DEFAULT_ROOM})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create a room here")
    sub.add_parser("status", help="show every run and who holds it")

    agent = sub.add_parser("agent", help="manage agent identities").add_subparsers(
        dest="agent_command", required=True
    )
    agent_add = agent.add_parser("add", help="register an agent participant")
    agent_add.add_argument("name")
    agent_add.add_argument("--provider", required=True, help="which provider this agent runs on")
    agent_add.add_argument("--credential-ref", default=None, help="a name, never a secret value")
    agent_add.add_argument(
        "--reviewer", action="store_true", help="allow this agent to resolve review gates"
    )

    human = sub.add_parser("human", help="manage human participants").add_subparsers(
        dest="human_command", required=True
    )
    human_add = human.add_parser("add", help="register a human participant")
    human_add.add_argument("name")

    task = sub.add_parser("task", help="manage runs").add_subparsers(
        dest="task_command", required=True
    )
    task_add = task.add_parser("add", help="create a run")
    task_add.add_argument("title", nargs="+")

    dispatch = sub.add_parser("dispatch", help="assign a run to a participant")
    dispatch.add_argument("run_id", type=int)
    dispatch.add_argument("--to", required=True)
    dispatch.add_argument("--lease", type=float, default=None, help="claim lifetime in seconds")

    handoff = sub.add_parser("handoff", help="pass a run on with an explicit scope")
    handoff.add_argument("run_id", type=int)
    handoff.add_argument("--to", required=True)
    handoff.add_argument("--by", required=True)
    handoff.add_argument("--scope", required=True, help="read-only | propose | full")

    act = sub.add_parser("act", help="perform an action on a run you hold")
    act.add_argument("run_id", type=int)
    act.add_argument("--by", required=True)
    act.add_argument("--action", required=True, help="comment | propose-change | merge | deploy")
    act.add_argument("--note", default="")

    submit = sub.add_parser("submit", help="open a review gate on a run")
    submit.add_argument("run_id", type=int)
    submit.add_argument("--by", required=True)
    submit.add_argument("--summary", default="")

    review = sub.add_parser("review", help="resolve a review gate")
    review.add_argument("run_id", type=int)
    review.add_argument("--by", required=True)
    review.add_argument("--decision", required=True, help="approve|reject|remediate|continue")
    review.add_argument("--note", default="")

    log = sub.add_parser("log", help="print a run's audit history")
    log.add_argument("run_id", type=int)
    log.add_argument("--json", action="store_true", help="machine-readable output")

    recover = sub.add_parser("recover", help="release claims whose lease has expired")
    recover.add_argument("--json", action="store_true")

    return parser


def _open(path: Path) -> Room:
    return Room.open(path)


def _dispatch_command(args: argparse.Namespace) -> int:  # noqa: C901 - a flat command table
    room_path = Path(args.room)

    if args.command == "init":
        Room.init(room_path).close()
        print(f"Runroom initialised at {room_path}")
        print("Next: runroom agent add <name> --provider <provider>")
        return 0

    room = _open(room_path)
    try:
        if args.command == "agent":
            p = room.add_participant(
                args.name,
                kind="agent",
                provider=args.provider,
                credential_ref=args.credential_ref,
                reviewer=args.reviewer,
            )
            role = "reviewing agent" if p.reviewer else "agent"
            print(f"Registered {role} {p.name} on {p.provider}")

        elif args.command == "human":
            p = room.add_participant(args.name, kind="human")
            print(f"Registered human reviewer {p.name}")

        elif args.command == "task":
            run = room.add_run(" ".join(args.title))
            print(f"Created run {run.id}")

        elif args.command == "dispatch":
            kwargs = {} if args.lease is None else {"lease": args.lease}
            run = room.dispatch(args.run_id, to=args.to, **kwargs)
            print(f"Run {run.id} claimed by {run.holder} (scope: {run.scope})")

        elif args.command == "handoff":
            run = room.handoff(args.run_id, to=args.to, by=args.by, scope=args.scope)
            print(f"Run {run.id} handed from {args.by} to {run.holder} with scope {run.scope}")

        elif args.command == "act":
            event = room.act(args.run_id, by=args.by, action=args.action, detail=args.note)
            print(
                f"Run {args.run_id}: {event.action} by {event.actor} recorded (event {event.seq})"
            )

        elif args.command == "submit":
            run = room.request_review(args.run_id, by=args.by, summary=args.summary)
            print(f"Run {run.id} is awaiting review. It will wait until a reviewer resolves it.")

        elif args.command == "review":
            run = room.review(args.run_id, by=args.by, decision=args.decision, note=args.note)
            print(f"Run {run.id}: {args.decision} by {args.by} -> status {run.status}")

        elif args.command == "log":
            events = room.history(args.run_id)
            if args.json:
                print(
                    json.dumps(
                        [
                            {
                                "seq": e.seq,
                                "at": e.at,
                                "actor": e.actor,
                                "action": e.action,
                                "detail": e.detail,
                            }
                            for e in events
                        ],
                        indent=2,
                    )
                )
            else:
                for e in events:
                    detail = json.dumps(e.detail, sort_keys=True) if e.detail else ""
                    print(f"{e.seq:>4}  {e.actor:<12} {e.action:<18} {detail}")

        elif args.command == "recover":
            recovered = room.recover_expired()
            if args.json:
                print(json.dumps(recovered))
            elif recovered:
                print(f"Released expired claims on: {', '.join(str(i) for i in recovered)}")
            else:
                print("No expired claims.")

        elif args.command == "status":
            runs = room.runs()
            if not runs:
                print("No runs yet.")
            for run in runs:
                holder = run.holder or "-"
                scope = run.scope or "-"
                print(f"{run.id:>4}  {run.status:<16} {holder:<12} {scope:<10} {run.title}")

        return 0
    finally:
        room.close()


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return _dispatch_command(args)
    except RunroomError as exc:
        print(f"runroom: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
