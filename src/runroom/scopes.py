"""Scopes are named, closed sets. A handoff must name one; there is no implicit default.

Adding a scope here is a governance decision, not a convenience. Keep the sets small
and keep the ordering obvious: every scope is a superset of the one above it.
"""

from runroom.errors import UnknownScope

SCOPES: dict[str, frozenset[str]] = {
    "read-only": frozenset({"comment", "submit"}),
    "propose": frozenset({"comment", "submit", "propose-change"}),
    "full": frozenset({"comment", "submit", "propose-change", "merge", "deploy"}),
}

#: What a participant may do on a run it was dispatched (not handed) — the default bound.
DEFAULT_SCOPE = "full"


def actions_for(scope: str) -> frozenset[str]:
    """Return the actions `scope` permits, or refuse if the scope is not defined."""
    try:
        return SCOPES[scope]
    except KeyError:
        known = ", ".join(sorted(SCOPES))
        raise UnknownScope(
            f"unknown scope {scope!r}; Runroom will not guess a default. Known scopes: {known}"
        ) from None


def permits(scope: str, action: str) -> bool:
    return action in actions_for(scope)
