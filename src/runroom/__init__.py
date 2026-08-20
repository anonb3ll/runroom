"""Runroom — governed handoffs between AI agents and humans.

A shared room for one run: two agents, one human, one task ledger, full history.
"""

from runroom.errors import RunroomError
from runroom.room import Event, Participant, Room, Run

__version__ = "0.0.1"
__all__ = ["Event", "Participant", "Room", "Run", "RunroomError"]
