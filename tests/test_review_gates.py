"""A gate blocks until a human resolves it. It never times out into approval."""

import pytest

from runroom.errors import GateBlocked, NotAReviewer, UnknownDecision


def _gated(staffed):
    run = staffed.add_run("Deploy the auth fix")
    staffed.dispatch(run.id, to="worker")
    staffed.request_review(run.id, by="worker", summary="ready to deploy")
    return run.id


def test_requesting_review_parks_the_run(staffed):
    run_id = _gated(staffed)
    assert staffed.get_run(run_id).status == "awaiting_review"


def test_work_cannot_continue_while_a_gate_is_open(staffed):
    run_id = _gated(staffed)

    with pytest.raises(GateBlocked):
        staffed.act(run_id, by="worker", action="merge")


@pytest.mark.parametrize(
    ("decision", "status"),
    [
        ("approve", "approved"),
        ("reject", "rejected"),
        ("remediate", "claimed"),
        ("continue", "claimed"),
    ],
)
def test_all_four_review_outcomes(staffed, decision, status):
    run_id = _gated(staffed)
    staffed.review(run_id, by="anna", decision=decision, note="reviewed")

    assert staffed.get_run(run_id).status == status


def test_remediate_returns_the_run_to_the_worker_that_asked(staffed):
    run_id = _gated(staffed)
    staffed.review(run_id, by="anna", decision="remediate", note="add a regression test first")

    run = staffed.get_run(run_id)
    assert run.holder == "worker"
    assert run.status == "claimed"


def test_a_gate_never_expires_into_approval(staffed, clock):
    """The intended failure mode is a run that waits, not a run that ships itself."""
    run_id = _gated(staffed)

    clock.advance(60 * 60 * 24 * 30)
    staffed.recover_expired()

    run = staffed.get_run(run_id)
    assert run.status == "awaiting_review"
    assert run.holder == "worker"


def test_an_agent_cannot_review_unless_designated(staffed):
    run_id = _gated(staffed)

    with pytest.raises(NotAReviewer):
        staffed.review(run_id, by="second", decision="approve")


def test_a_designated_reviewing_agent_may_review(staffed):
    staffed.add_participant("auditor", kind="agent", provider="provider-c", reviewer=True)
    run_id = _gated(staffed)

    staffed.review(run_id, by="auditor", decision="approve")

    assert staffed.get_run(run_id).status == "approved"


def test_a_worker_cannot_approve_its_own_run(staffed):
    staffed.add_participant("selfapprover", kind="agent", provider="provider-a", reviewer=True)
    run = staffed.add_run("Deploy the auth fix")
    staffed.dispatch(run.id, to="selfapprover")
    staffed.request_review(run.id, by="selfapprover", summary="lgtm")

    with pytest.raises(NotAReviewer) as excinfo:
        staffed.review(run.id, by="selfapprover", decision="approve")

    assert "own" in str(excinfo.value).lower()


def test_an_unknown_decision_is_refused(staffed):
    run_id = _gated(staffed)

    with pytest.raises(UnknownDecision):
        staffed.review(run_id, by="anna", decision="probably-fine")


def test_review_outside_an_open_gate_is_refused(staffed):
    run = staffed.add_run("Deploy the auth fix")
    staffed.dispatch(run.id, to="worker")

    with pytest.raises(GateBlocked):
        staffed.review(run.id, by="anna", decision="approve")


def test_a_resolved_run_holds_no_scope(staffed):
    """An approved run is nobody's to act on, so it carries no lingering permission."""
    run_id = _gated(staffed)
    staffed.review(run_id, by="anna", decision="approve")

    run = staffed.get_run(run_id)
    assert run.holder is None
    assert run.scope is None


def test_a_remediated_run_keeps_the_scope_it_had(staffed):
    run = staffed.add_run("Deploy the auth fix")
    staffed.dispatch(run.id, to="worker")
    staffed.handoff(run.id, to="second", by="worker", scope="propose")
    staffed.request_review(run.id, by="second", summary="ready")
    staffed.review(run.id, by="anna", decision="remediate", note="one more thing")

    assert staffed.get_run(run.id).scope == "propose"
