"""Shared fixtures. Every participant, run, and credential here is synthetic."""

import pytest

from runroom.room import Room


class FakeClock:
    """Deterministic clock. Tests move time explicitly; nothing moves on its own."""

    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def room(tmp_path, clock):
    room = Room.init(tmp_path / "room", clock=clock)
    yield room
    room.close()


@pytest.fixture
def staffed(room):
    """Two agent participants on two different providers, plus a human reviewer."""
    room.add_participant("worker", kind="agent", provider="provider-a", credential_ref="cred-a")
    room.add_participant("second", kind="agent", provider="provider-b", credential_ref="cred-b")
    room.add_participant("anna", kind="human")
    return room
