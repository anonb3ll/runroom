"""A claim is exclusive. Two agents must never silently work the same run."""

import pytest

from runroom.errors import AlreadyClaimed, NotTheHolder, UnknownParticipant


def test_dispatch_claims_the_run(staffed):
    run = staffed.add_run("Fix the flaky auth test")
    staffed.dispatch(run.id, to="worker")

    run = staffed.get_run(run.id)
    assert run.holder == "worker"
    assert run.status == "claimed"


def test_second_dispatch_to_a_different_participant_is_refused(staffed):
    run = staffed.add_run("Fix the flaky auth test")
    staffed.dispatch(run.id, to="worker")

    with pytest.raises(AlreadyClaimed) as excinfo:
        staffed.dispatch(run.id, to="second")

    assert "worker" in str(excinfo.value)
    assert staffed.get_run(run.id).holder == "worker"


def test_redispatch_to_the_same_holder_is_idempotent(staffed):
    run = staffed.add_run("Fix the flaky auth test")
    staffed.dispatch(run.id, to="worker")
    staffed.dispatch(run.id, to="worker")

    assert staffed.get_run(run.id).holder == "worker"


def test_release_frees_the_run_for_someone_else(staffed):
    run = staffed.add_run("Fix the flaky auth test")
    staffed.dispatch(run.id, to="worker")
    staffed.release(run.id, by="worker")

    assert staffed.get_run(run.id).holder is None
    assert staffed.get_run(run.id).status == "open"

    staffed.dispatch(run.id, to="second")
    assert staffed.get_run(run.id).holder == "second"


def test_a_non_holder_cannot_release(staffed):
    run = staffed.add_run("Fix the flaky auth test")
    staffed.dispatch(run.id, to="worker")

    with pytest.raises(NotTheHolder):
        staffed.release(run.id, by="second")


def test_dispatch_to_an_unknown_participant_is_refused(staffed):
    run = staffed.add_run("Fix the flaky auth test")

    with pytest.raises(UnknownParticipant):
        staffed.dispatch(run.id, to="ghost")
