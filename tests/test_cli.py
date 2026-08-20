"""The CLI is the demo path. If these fail, the README lies."""

import json

import pytest

from runroom.cli import main


@pytest.fixture
def room_dir(tmp_path):
    return tmp_path / "room"


def run(argv, room_dir):
    return main(["--room", str(room_dir), *argv])


def test_init_creates_a_room(room_dir, capsys):
    assert run(["init"], room_dir) == 0
    assert (room_dir / "runroom.db").exists()
    assert "Runroom" in capsys.readouterr().out


def test_init_twice_is_refused_rather_than_clobbering(room_dir, capsys):
    run(["init"], room_dir)
    assert run(["init"], room_dir) == 1
    assert "already" in capsys.readouterr().err.lower()


def test_the_full_demo_path(room_dir, capsys):
    run(["init"], room_dir)
    capsys.readouterr()

    assert run(["agent", "add", "worker", "--provider", "provider-a"], room_dir) == 0
    assert run(["agent", "add", "second", "--provider", "provider-b"], room_dir) == 0
    assert run(["human", "add", "anna"], room_dir) == 0

    assert run(["task", "add", "Fix the flaky auth test"], room_dir) == 0
    out = capsys.readouterr().out
    run_id = int(out.strip().split()[-1])

    assert run(["dispatch", str(run_id), "--to", "worker"], room_dir) == 0
    assert run(
        ["handoff", str(run_id), "--to", "second", "--by", "worker", "--scope", "propose"],
        room_dir,
    ) == 0
    assert run(["submit", str(run_id), "--by", "second", "--summary", "fix ready"], room_dir) == 0
    assert run(["review", str(run_id), "--by", "anna", "--decision", "approve"], room_dir) == 0

    capsys.readouterr()
    assert run(["log", str(run_id)], room_dir) == 0
    log = capsys.readouterr().out
    for expected in ("run-created", "dispatch", "handoff", "review-requested", "review-decision"):
        assert expected in log


def test_log_as_json_is_machine_readable(room_dir, capsys):
    run(["init"], room_dir)
    run(["agent", "add", "worker", "--provider", "provider-a"], room_dir)
    run(["task", "add", "Fix the flaky auth test"], room_dir)
    capsys.readouterr()
    run(["dispatch", "1", "--to", "worker"], room_dir)
    capsys.readouterr()

    assert run(["log", "1", "--json"], room_dir) == 0
    events = json.loads(capsys.readouterr().out)
    assert [e["action"] for e in events] == ["run-created", "dispatch"]


def test_a_refused_command_exits_nonzero_with_a_readable_reason(room_dir, capsys):
    run(["init"], room_dir)
    run(["agent", "add", "worker", "--provider", "provider-a"], room_dir)
    run(["agent", "add", "second", "--provider", "provider-b"], room_dir)
    run(["task", "add", "Fix the flaky auth test"], room_dir)
    run(["dispatch", "1", "--to", "worker"], room_dir)
    capsys.readouterr()

    assert run(["dispatch", "1", "--to", "second"], room_dir) == 1
    err = capsys.readouterr().err
    assert "worker" in err
    assert "claimed" in err.lower()


def test_commands_against_a_missing_room_fail_clearly(room_dir, capsys):
    assert run(["task", "add", "anything"], room_dir) == 1
    assert "runroom init" in capsys.readouterr().err


def test_status_shows_who_holds_what(room_dir, capsys):
    run(["init"], room_dir)
    run(["agent", "add", "worker", "--provider", "provider-a"], room_dir)
    run(["task", "add", "Fix the flaky auth test"], room_dir)
    run(["dispatch", "1", "--to", "worker"], room_dir)
    capsys.readouterr()

    assert run(["status"], room_dir) == 0
    out = capsys.readouterr().out
    assert "worker" in out
    assert "claimed" in out
