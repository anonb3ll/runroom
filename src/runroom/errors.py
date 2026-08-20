"""Every refusal has its own type, so callers can tell *why* they were stopped."""


class RunroomError(Exception):
    """Base class for every refusal Runroom issues."""


class RoomNotFound(RunroomError):
    """No room exists at the given path."""


class RoomExists(RunroomError):
    """A room already exists at the given path; Runroom will not overwrite it."""


class UnknownParticipant(RunroomError):
    """No participant by that name is registered in this room."""


class UnknownRun(RunroomError):
    """No run by that id exists in this room."""


class AlreadyClaimed(RunroomError):
    """The run is held by another participant and the claim has not expired."""


class NotTheHolder(RunroomError):
    """The acting participant does not hold this run."""


class UnknownScope(RunroomError):
    """The named scope is not defined. Runroom will not guess a default."""


class ScopeViolation(RunroomError):
    """The action exceeds the bound stated when the run was handed off."""


class GateBlocked(RunroomError):
    """A review gate is open (or absent) and the requested action cannot proceed."""


class NotAReviewer(RunroomError):
    """The acting participant may not resolve this gate."""


class UnknownDecision(RunroomError):
    """The review decision is not one of approve/reject/remediate/continue."""
