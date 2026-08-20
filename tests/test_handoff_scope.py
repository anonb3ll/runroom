"""A handoff transfers work AND states the bound. The receiver gets neither more nor less."""

import pytest

from runroom.errors import NotTheHolder, ScopeViolation, UnknownScope


def test_handoff_transfers_the_claim(staffed):
    run = staffed.add_run("Review the retry backoff change")
    staffed.dispatch(run.id, to="worker")
    staffed.handoff(run.id, to="second", by="worker", scope="read-only")

    run = staffed.get_run(run.id)
    assert run.holder == "second"
    assert run.scope == "read-only"


def test_only_the_holder_may_hand_off(staffed):
    run = staffed.add_run("Review the retry backoff change")
    staffed.dispatch(run.id, to="worker")

    with pytest.raises(NotTheHolder):
        staffed.handoff(run.id, to="anna", by="second", scope="read-only")


def test_receiver_may_perform_an_action_inside_its_scope(staffed):
    run = staffed.add_run("Review the retry backoff change")
    staffed.dispatch(run.id, to="worker")
    staffed.handoff(run.id, to="second", by="worker", scope="read-only")

    staffed.act(run.id, by="second", action="comment", detail="looks fine to me")

    assert any(e.action == "comment" for e in staffed.history(run.id))


def test_receiver_may_not_exceed_its_scope(staffed):
    run = staffed.add_run("Review the retry backoff change")
    staffed.dispatch(run.id, to="worker")
    staffed.handoff(run.id, to="second", by="worker", scope="read-only")

    with pytest.raises(ScopeViolation) as excinfo:
        staffed.act(run.id, by="second", action="merge")

    assert "read-only" in str(excinfo.value)


def test_a_refused_action_is_still_recorded(staffed):
    """A blocked attempt is evidence. Silently dropping it would hide the interesting case."""
    run = staffed.add_run("Review the retry backoff change")
    staffed.dispatch(run.id, to="worker")
    staffed.handoff(run.id, to="second", by="worker", scope="read-only")

    with pytest.raises(ScopeViolation):
        staffed.act(run.id, by="second", action="merge")

    refusals = [e for e in staffed.history(run.id) if e.action == "scope-violation"]
    assert len(refusals) == 1
    assert refusals[0].actor == "second"


def test_a_non_holder_cannot_act_at_all(staffed):
    run = staffed.add_run("Review the retry backoff change")
    staffed.dispatch(run.id, to="worker")

    with pytest.raises(NotTheHolder):
        staffed.act(run.id, by="second", action="comment")


def test_unknown_scope_is_refused_rather_than_defaulted(staffed):
    run = staffed.add_run("Review the retry backoff change")
    staffed.dispatch(run.id, to="worker")

    with pytest.raises(UnknownScope):
        staffed.handoff(run.id, to="second", by="worker", scope="whatever-you-think-best")
