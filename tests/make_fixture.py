#!/usr/bin/env python3
"""Build a synthetic session containing a compact boundary.

Why synthetic: on the reference machine auto-compact has never fired -- a
session climbed to 996,517 tokens of a 1,000,000 window across 1,407 turns and
ended there without emitting a single boundary. Zero `compact_boundary` records
exist in 48 sessions spanning builds 2.1.200-2.1.220. Users who let compaction
run will hit segment breaks constantly, so the code path cannot go untested
merely because one corpus cannot produce it.

The record shape is taken from community observation (type:system /
subtype:compact_boundary, logicalParentUuid, compactMetadata) and has NOT been
verified against a real boundary. This fixture therefore tests shrink's
handling, not the accuracy of the shape. If the shape is wrong, the handling is
still correct for the shape we believe in -- and SCHEMA.md records the
uncertainty.
"""
import datetime
import json
import pathlib
import sys

SID = "aaaaaaaa-0000-4000-8000-000000000001"
BASE = datetime.datetime(2026, 8, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)


def uid(n):
    return f"bbbbbbbb-0000-4000-8000-{n:012d}"


def ts(i):
    return (BASE + datetime.timedelta(minutes=i)).isoformat().replace("+00:00", "Z")


def build(dest: pathlib.Path):
    proj = dest / "-fixture-project"
    proj.mkdir(parents=True, exist_ok=True)
    rows, prev = [], None
    for i in range(1, 4):
        rows.append({"type": "user", "uuid": uid(i), "parentUuid": prev, "timestamp": ts(i),
                     "userType": "external", "version": "2.1.220",
                     "message": {"role": "user", "content": f"pre-compaction message {i}"}})
        prev = uid(i)
        rows.append({"type": "assistant", "uuid": uid(100 + i), "parentUuid": prev,
                     "timestamp": ts(i), "version": "2.1.220",
                     "message": {"role": "assistant",
                                 "content": [{"type": "text", "text": f"reply {i}"}]}})
        prev = uid(100 + i)
    rows.append({"type": "system", "subtype": "compact_boundary", "uuid": uid(500),
                 "parentUuid": None, "logicalParentUuid": prev, "timestamp": ts(10),
                 "version": "2.1.220",
                 "compactMetadata": {"trigger": "auto", "preTokens": 180000}})
    prev = None
    for i in range(4, 7):
        rows.append({"type": "user", "uuid": uid(i), "parentUuid": prev, "timestamp": ts(10 + i),
                     "userType": "external", "version": "2.1.220",
                     "message": {"role": "user", "content": f"post-compaction message {i}"}})
        prev = uid(i)
        rows.append({"type": "assistant", "uuid": uid(100 + i), "parentUuid": prev,
                     "timestamp": ts(10 + i), "version": "2.1.220",
                     "message": {"role": "assistant",
                                 "content": [{"type": "text", "text": f"reply {i}"}]}})
        prev = uid(100 + i)
    (proj / f"{SID}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return proj / f"{SID}.jsonl"


if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/shrink-fixture")
    print(build(out))
