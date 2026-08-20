"""An agent that dies mid-run must not hold the work hostage — and must not vanish from history."""

import pytest

from runroom.errors import AlreadyClaimed

LEASE = 900


def test_a_live_claim_blocks_others(staffed, clock):
    run = staffed.add_run("Long-running migration")
    staffed.dispatch(run.id, to="worker", lease=LEASE)

    clock.advance(LEASE - 1)
    staffed.recover_expired()

    with pytest.raises(AlreadyClaimed):
        staffed.dispatch(run.id, to="second")


def test_an_expired_claim_is_recovered(staffed, clock):
    run = staffed.add_run("Long-running migration")
    staffed.dispatch(run.id, to="worker", lease=LEASE)

    clock.advance(LEASE + 1)
    recovered = staffed.recover_expired()

    assert recovered == [run.id]
    assert staffed.get_run(run.id).holder is None
    assert staffed.get_run(run.id).status == "open"


def test_recovery_is_recorded_not_silent(staffed, clock):
    run = staffed.add_run("Long-running migration")
    staffed.dispatch(run.id, to="worker", lease=LEASE)
    clock.advance(LEASE + 1)
    staffed.recover_expired()

    expiries = [e for e in staffed.history(run.id) if e.action == "claim-expired"]
    assert len(expiries) == 1
    assert expiries[0].detail["was_held_by"] == "worker"


def test_a_crash_mid_handoff_leaves_the_full_trail(staffed, clock):
    run = staffed.add_run("Long-running migration")
    staffed.dispatch(run.id, to="worker", lease=LEASE)
    staffed.handoff(run.id, to="second", by="worker", scope="propose")

    clock.advance(LEASE + 1)
    staffed.recover_expired()

    actions = [e.action for e in staffed.history(run.id)]
    assert actions == ["run-created", "dispatch", "handoff", "claim-expired"]
    assert staffed.get_run(run.id).holder is None


def test_a_recovered_run_can_be_picked_up_again(staffed, clock):
    run = staffed.add_run("Long-running migration")
    staffed.dispatch(run.id, to="worker", lease=LEASE)
    clock.advance(LEASE + 1)
    staffed.recover_expired()

    staffed.dispatch(run.id, to="second")
    assert staffed.get_run(run.id).holder == "second"


def test_a_handoff_renews_the_lease(staffed, clock):
    run = staffed.add_run("Long-running migration")
    staffed.dispatch(run.id, to="worker", lease=LEASE)
    clock.advance(LEASE - 1)
    staffed.handoff(run.id, to="second", by="worker", scope="propose", lease=LEASE)

    clock.advance(LEASE - 1)
    assert staffed.recover_expired() == []
    assert staffed.get_run(run.id).holder == "second"
