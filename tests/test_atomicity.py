"""Atomicity tests: state transitions and audit event records are atomic transactions."""

from unittest.mock import patch

import pytest

from runroom.errors import UnknownRun


def test_add_run_atomicity_on_crash(staffed):
    """If recording the run-created event fails, the run row is rolled back completely."""
    err = RuntimeError("simulated crash during event record")
    with (
        patch.object(staffed, "_record", side_effect=err),
        pytest.raises(RuntimeError, match="simulated crash"),
    ):
        staffed.add_run("Test atomic add_run")

    assert len(staffed.runs()) == 0
    with pytest.raises(UnknownRun):
        staffed.get_run(1)


def test_dispatch_atomicity_on_crash(staffed):
    """If recording dispatch fails, the claim update is rolled back."""
    run = staffed.add_run("Test dispatch atomicity")
    assert run.status == "open"
    assert run.holder is None

    err = RuntimeError("crash in dispatch record")
    with (
        patch.object(staffed, "_record", side_effect=err),
        pytest.raises(RuntimeError, match="crash in dispatch"),
    ):
        staffed.dispatch(run.id, to="worker")

    current = staffed.get_run(run.id)
    assert current.status == "open"
    assert current.holder is None
    assert current.scope is None


def test_handoff_atomicity_on_crash(staffed):
    """If recording handoff fails, holder and scope updates roll back to previous holder."""
    run = staffed.add_run("Test handoff atomicity")
    staffed.dispatch(run.id, to="worker")

    err = RuntimeError("crash in handoff record")
    with (
        patch.object(staffed, "_record", side_effect=err),
        pytest.raises(RuntimeError, match="crash in handoff"),
    ):
        staffed.handoff(run.id, to="second", by="worker", scope="read-only")

    current = staffed.get_run(run.id)
    assert current.holder == "worker"
    assert current.scope == "full"


def test_release_atomicity_on_crash(staffed):
    """If recording release fails, release rolls back and holder remains held."""
    run = staffed.add_run("Test release atomicity")
    staffed.dispatch(run.id, to="worker")

    err = RuntimeError("crash in release record")
    with (
        patch.object(staffed, "_record", side_effect=err),
        pytest.raises(RuntimeError, match="crash in release"),
    ):
        staffed.release(run.id, by="worker")

    current = staffed.get_run(run.id)
    assert current.holder == "worker"
    assert current.status == "claimed"


def test_request_review_atomicity_on_crash(staffed):
    """If recording review request fails, status rolls back from awaiting_review."""
    run = staffed.add_run("Test review request atomicity")
    staffed.dispatch(run.id, to="worker")

    err = RuntimeError("crash in review request record")
    with (
        patch.object(staffed, "_record", side_effect=err),
        pytest.raises(RuntimeError, match="crash in review request"),
    ):
        staffed.request_review(run.id, by="worker", summary="Ready for review")

    current = staffed.get_run(run.id)
    assert current.status == "claimed"
    assert current.submitted_by is None


def test_review_atomicity_on_crash(staffed):
    """If recording review decision fails, review state transition rolls back."""
    run = staffed.add_run("Test review atomicity")
    staffed.dispatch(run.id, to="worker")
    staffed.request_review(run.id, by="worker", summary="Please approve")

    err = RuntimeError("crash in review decision record")
    with (
        patch.object(staffed, "_record", side_effect=err),
        pytest.raises(RuntimeError, match="crash in review decision"),
    ):
        staffed.review(run.id, by="anna", decision="approve")

    current = staffed.get_run(run.id)
    assert current.status == "awaiting_review"


def test_recover_expired_atomicity_on_crash(staffed):
    """If recording claim-expired fails, expired claim recovery rolls back."""
    run = staffed.add_run("Test expired recovery atomicity")
    staffed.dispatch(run.id, to="worker", lease=10)

    # Fast-forward time past lease
    base_time = staffed._clock()
    staffed._clock = lambda: base_time + 100

    err = RuntimeError("crash in claim-expired record")
    with (
        patch.object(staffed, "_record", side_effect=err),
        pytest.raises(RuntimeError, match="crash in claim-expired"),
    ):
        staffed.recover_expired()

    current = staffed.get_run(run.id)
    assert current.holder == "worker"
    assert current.status == "claimed"
