"""Concurrency tests: verify race conditions are prevented with atomic conditional updates."""

import concurrent.futures

from runroom import Room
from runroom.errors import AlreadyClaimed, GateBlocked, NotTheHolder


def test_concurrent_dispatch_exclusivity(staffed):
    """Two concurrent dispatch attempts produce exactly one winner and one AlreadyClaimed."""
    run = staffed.add_run("Concurrent claim test")

    def try_claim(participant):
        r = Room.open(staffed.path, clock=staffed._clock)
        try:
            return r.dispatch(run.id, to=participant)
        finally:
            r.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(try_claim, "worker")
        f2 = executor.submit(try_claim, "second")
        results = [f1, f2]

    successes = []
    errors = []
    for f in results:
        try:
            successes.append(f.result())
        except Exception as e:
            errors.append(e)

    assert len(successes) == 1
    assert len(errors) == 1
    assert isinstance(errors[0], AlreadyClaimed)


def test_concurrent_review_exclusivity(staffed):
    """Two concurrent reviews of the same gate produce exactly one winner and one GateBlocked."""
    staffed.add_participant("reviewer2", kind="human")
    run = staffed.add_run("Concurrent review test")
    staffed.dispatch(run.id, to="worker")
    staffed.request_review(run.id, by="worker", summary="Review me")

    def try_review(reviewer):
        r = Room.open(staffed.path, clock=staffed._clock)
        try:
            return r.review(run.id, by=reviewer, decision="approve")
        finally:
            r.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(try_review, "anna")
        f2 = executor.submit(try_review, "reviewer2")
        results = [f1, f2]

    successes = []
    errors = []
    for f in results:
        try:
            successes.append(f.result())
        except Exception as e:
            errors.append(e)

    assert len(successes) == 1
    assert len(errors) == 1
    assert isinstance(errors[0], GateBlocked)


def test_concurrent_handoff_and_release(staffed):
    """If handoff and release race, exactly one wins and the loser is NotTheHolder."""
    run = staffed.add_run("Concurrent handoff and release")
    staffed.dispatch(run.id, to="worker")

    def try_handoff():
        r = Room.open(staffed.path, clock=staffed._clock)
        try:
            return r.handoff(run.id, to="second", by="worker", scope="read-only")
        finally:
            r.close()

    def try_release():
        r = Room.open(staffed.path, clock=staffed._clock)
        try:
            return r.release(run.id, by="worker")
        finally:
            r.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(try_handoff)
        f2 = executor.submit(try_release)
        results = [f1, f2]

    successes = []
    errors = []
    for f in results:
        try:
            successes.append(f.result())
        except Exception as e:
            errors.append(e)

    assert len(successes) == 1
    assert len(errors) == 1
    assert isinstance(errors[0], NotTheHolder)
