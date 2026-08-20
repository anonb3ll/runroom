"""History is append-only. No feature, and no operator API, may edit or delete it."""

import sqlite3

import pytest

from runroom.errors import UnknownRun


def test_every_step_is_recorded_in_order(staffed):
    run = staffed.add_run("Fix the flaky auth test")
    staffed.dispatch(run.id, to="worker")
    staffed.handoff(run.id, to="second", by="worker", scope="propose")
    staffed.request_review(run.id, by="second", summary="proposed a fix")
    staffed.review(run.id, by="anna", decision="approve", note="ship it")

    actions = [e.action for e in staffed.history(run.id)]
    assert actions == [
        "run-created",
        "dispatch",
        "handoff",
        "review-requested",
        "review-decision",
    ]


def test_every_event_is_attributed_and_timestamped(staffed, clock):
    run = staffed.add_run("Fix the flaky auth test")
    clock.advance(5)
    staffed.dispatch(run.id, to="worker")

    events = staffed.history(run.id)
    assert all(e.actor for e in events)
    assert all(e.at > 0 for e in events)
    assert events[1].at == events[0].at + 5


def test_a_handoff_records_both_identities(staffed):
    run = staffed.add_run("Fix the flaky auth test")
    staffed.dispatch(run.id, to="worker")
    staffed.handoff(run.id, to="second", by="worker", scope="read-only")

    handoff = [e for e in staffed.history(run.id) if e.action == "handoff"][0]
    assert handoff.actor == "worker"
    assert handoff.detail["to"] == "second"
    assert handoff.detail["scope"] == "read-only"


def test_the_public_api_offers_no_way_to_edit_history(staffed):
    for forbidden in ("delete_event", "edit_event", "clear_history", "purge"):
        assert not hasattr(staffed, forbidden)


def test_direct_sql_update_of_history_is_rejected(staffed):
    run = staffed.add_run("Fix the flaky auth test")
    staffed.dispatch(run.id, to="worker")

    with pytest.raises(sqlite3.DatabaseError):
        staffed.connection.execute("UPDATE events SET actor = 'someone-else'")
        staffed.connection.commit()


def test_direct_sql_delete_of_history_is_rejected(staffed):
    run = staffed.add_run("Fix the flaky auth test")
    staffed.dispatch(run.id, to="worker")

    with pytest.raises(sqlite3.DatabaseError):
        staffed.connection.execute("DELETE FROM events")
        staffed.connection.commit()


def test_history_survives_reopening_the_room(tmp_path, clock):
    from runroom.room import Room

    room = Room.init(tmp_path / "room", clock=clock)
    room.add_participant("worker", kind="agent", provider="provider-a")
    run = room.add_run("Fix the flaky auth test")
    room.dispatch(run.id, to="worker")
    room.close()

    reopened = Room.open(tmp_path / "room", clock=clock)
    assert [e.action for e in reopened.history(run.id)] == ["run-created", "dispatch"]
    reopened.close()


def test_history_of_an_unknown_run_is_an_error_not_an_empty_list(staffed):
    with pytest.raises(UnknownRun):
        staffed.history(9999)
