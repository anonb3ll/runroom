"""Participants are identities, not models. A handoff must not carry credentials across."""

import json

import pytest

from runroom.errors import NotTheHolder


def test_participants_keep_their_own_provider(staffed):
    assert staffed.get_participant("worker").provider == "provider-a"
    assert staffed.get_participant("second").provider == "provider-b"


def test_a_handoff_does_not_copy_the_sender_credential(staffed):
    run = staffed.add_run("Cross-provider handoff")
    staffed.dispatch(run.id, to="worker")
    staffed.handoff(run.id, to="second", by="worker", scope="read-only")

    assert staffed.get_participant("second").credential_ref == "cred-b"
    assert staffed.effective_credential(run.id) == "cred-b"


def test_no_credential_is_ever_written_into_history(staffed):
    run = staffed.add_run("Cross-provider handoff")
    staffed.dispatch(run.id, to="worker")
    staffed.handoff(run.id, to="second", by="worker", scope="read-only")
    staffed.request_review(run.id, by="second", summary="done")
    staffed.review(run.id, by="anna", decision="approve")

    serialized = json.dumps([e.detail for e in staffed.history(run.id)])
    assert "cred-a" not in serialized
    assert "cred-b" not in serialized


def test_a_participant_cannot_read_another_participant_credential(staffed):
    run = staffed.add_run("Cross-provider handoff")
    staffed.dispatch(run.id, to="worker")

    with pytest.raises(NotTheHolder):
        staffed.effective_credential(run.id, as_participant="second")

    assert staffed.effective_credential(run.id, as_participant="worker") == "cred-a"


def test_the_provider_boundary_crossing_is_recorded(staffed):
    run = staffed.add_run("Cross-provider handoff")
    staffed.dispatch(run.id, to="worker")
    staffed.handoff(run.id, to="second", by="worker", scope="read-only")

    handoff = [e for e in staffed.history(run.id) if e.action == "handoff"][0]
    assert handoff.detail["from_provider"] == "provider-a"
    assert handoff.detail["to_provider"] == "provider-b"
    assert handoff.detail["crossed_provider_boundary"] is True


def test_a_same_provider_handoff_is_marked_as_such(staffed):
    staffed.add_participant(
        "sibling", kind="agent", provider="provider-a", credential_ref="cred-a2"
    )
    run = staffed.add_run("Same-provider handoff")
    staffed.dispatch(run.id, to="worker")
    staffed.handoff(run.id, to="sibling", by="worker", scope="read-only")

    handoff = [e for e in staffed.history(run.id) if e.action == "handoff"][0]
    assert handoff.detail["crossed_provider_boundary"] is False
