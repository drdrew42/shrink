#!/bin/sh
# excerpt must stop at a compaction boundary and say that it stopped. A window
# that silently crosses one hands a theorist a stimulus that did not precede
# the response, which is worse than a short window.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d)
python3 "$ROOT/tests/make_fixture.py" "$TMP/projects" >/dev/null
OUT=$(CLAUDE_CONFIG_DIR="$TMP" "$ROOT/bin/shrink" excerpt \
  "aaaaaaaa-0000-4000-8000-000000000001:bbbbbbbb-0000-4000-8000-000000000003" \
  --before 1 --after 3 --raw)

echo "$OUT" | grep -q "truncated below: compaction boundary" \
  || { echo "FAIL: excerpt did not report the boundary"; echo "$OUT"; exit 1; }
echo "$OUT" | grep -q "post-compaction" \
  && { echo "FAIL: excerpt crossed the boundary"; echo "$OUT"; exit 1; }
echo "$OUT" | grep -q "pre-compaction message 3" \
  || { echo "FAIL: excerpt lost the target turn"; exit 1; }

rm -rf "$TMP"
echo "ok — excerpt stops at the compaction boundary and reports it"
