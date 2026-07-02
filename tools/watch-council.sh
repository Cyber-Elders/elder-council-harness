#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
#
# Watch an Elder Council deliberate in REALTIME — one tmux pane per lens.
#
#   tools/watch-council.sh <council> "<question>" [extra convene args…]
#   e.g. tools/watch-council.sh eng-team "build the new checkout flow per TICKET-42" --lane open
#
# What it does (nothing clever — the harness does the real work):
#   * runs `eldercouncil convene <council> --orchestrate` in the main pane
#     (your pinned models; the tool lens runs real checks; tally + audit as usual)
#   * opens one pane per lens tailing its live transcript in .council/last-run/
# So you SEE every voice deliberating in parallel, and still get the fail-closed
# verdict + hash-chained record at the end. Requires tmux + the [orchestrator]
# extra. Transcripts are redacted like every persisted artifact.
set -euo pipefail

command -v tmux >/dev/null 2>&1 || { echo "watch-council: tmux is required"; exit 1; }
command -v eldercouncil >/dev/null 2>&1 || { echo "watch-council: eldercouncil not on PATH"; exit 1; }

COUNCIL="${1:?usage: watch-council.sh <council> \"<question>\" [convene args…]}"
QUESTION="${2:?a question is required}"
shift 2

DIR="${COUNCIL_DIR:-$PWD/.council}/last-run"
mkdir -p "$DIR"

# Lens slugs from the council's own task-pack (stdlib python; no jq dependency).
SLUGS=$(eldercouncil convene "$COUNCIL" --question "$QUESTION" --no-audit 2>/dev/null \
  | python3 -c "import sys,json,re; \
[print(re.sub(r'[^a-z0-9]+','-',t['role'].lower()).strip('-')) for t in json.load(sys.stdin)['tasks']]")
[ -n "$SLUGS" ] || { echo "watch-council: could not read the council's lens list"; exit 1; }
for s in $SLUGS; do printf '⋯ waiting for the run to start\n' > "$DIR/$s.md"; done

SESSION="council-$$"
Q_ESC=$(printf '%q' "$QUESTION")
ARGS_ESC=""
for a in "$@"; do ARGS_ESC+=" $(printf '%q' "$a")"; done

tmux new-session -d -s "$SESSION" -n council \
  "eldercouncil convene $COUNCIL --orchestrate --question $Q_ESC$ARGS_ESC; \
   printf '\n── council finished — press Enter to close ──\n'; read -r _"
for s in $SLUGS; do
  tmux split-window -t "$SESSION:council" "tail -f '$DIR/$s.md'"
  tmux select-layout -t "$SESSION:council" tiled
done
tmux select-pane -t "$SESSION:council.0"
exec tmux attach -t "$SESSION"
