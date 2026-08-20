#!/usr/bin/env bash
# The Runroom demo, end to end, in one file.
#
# Two agents on two providers, one human reviewer, one run: dispatch, a bounded
# handoff, a refused action, a review gate, a remediation, and an approval —
# with the full history at the end.
#
# Everything here is synthetic. It touches only a temporary directory.

set -euo pipefail

ROOM="$(mktemp -d)/demo-room"
run() { runroom --room "$ROOM" "$@"; }
step() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

step "1. Create a room"
run init

step "2. Register two agents on two different providers, and a human reviewer"
run agent add worker --provider provider-a --credential-ref worker-key
run agent add second --provider provider-b --credential-ref second-key
run human add anna

step "3. Create a run and dispatch it"
run task add "Fix the flaky auth test"
run dispatch 1 --to worker

step "4. Hand it to the second agent, read-only"
run handoff 1 --to second --by worker --scope read-only

step "5. The second agent tries to merge. Its scope does not allow that."
if run act 1 --by second --action merge; then
    echo "UNEXPECTED: the merge was allowed" >&2
    exit 1
fi
echo "refused, as intended — and the attempt is now in the history"

step "6. Attach CI evidence, then open a review gate"
run act 1 --by second --action comment --note "CI run 4821 green: 54 passed"
run submit 1 --by second --summary "auth test fixed; CI 4821 green"
step "7. The human asks for a change first"
run review 1 --by anna --decision remediate --note "add a regression test"

step "8. ...then approves"
run submit 1 --by second --summary "regression test added"
run review 1 --by anna --decision approve --note "ship it"

step "9. The full history"
run log 1

step "10. Where things stand"
run status

printf '\n\033[1mDemo complete.\033[0m Room was at %s\n' "$ROOM"
