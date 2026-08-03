---
description: Read your own Claude Code history and hand back a psychological read
argument-hint: "[here] [--days N] [--offline]"
---

`shrink` is on PATH once the plugin is enabled — call it directly, not by path.
Never read `~/.claude/projects/` directly. Everything goes through `shrink` so
the user needs one permission rule, not a prompt storm.

## 1. Plan, and confirm before spending

```
shrink digest --days 30
```

Report what it found: sessions, window, authored turns, coverage gap. The dry
tier is free; the panel costs tokens. **Confirm before going further.** If the
user passed `--offline`, stop after step 2.

If there are fewer than ~50 authored turns, say so plainly — "you have four
sessions, come back later" — and stop. A confident profile of nothing is worse
than no profile.

## 2. The sincere tier

```
shrink dry --days 30
```

Offline, no model calls. Show it. This stands alone and is the honest half.

## 3. Evidence

```
shrink packet --days 30 --out packet.json
```

Outliers plus a control set, identifiers pseudonymised on the way out.

## 4. The panel

Run the `shrink:freud`, `shrink:jung`, and `shrink:goffman` agents **in
parallel**. They hold `Bash(shrink excerpt:*)` and nothing else, so:

- **Paste the packet JSON into each prompt.** They cannot read files.
- **Their findings come back as their final message.** They cannot write files —
  you write the JSONL.

Give all three the *same* packet and no other context. Do not summarise it for
them and do not hand any of them an observation the others lack — a finding that
only exists because one theorist was primed will not reproduce on anyone else's
corpus.

Merge the three returned objects into one JSONL, one object per line.

## 5. The report

Run the `shrink:analyst` agent, pasting in the theorists' claims and the packet.
Its report comes back as its final message; you write it to a file. One voice,
second person, merged sections.

```
shrink render --packet packet.json --findings findings.jsonl \
              --analysis analysis.json
```

The renderer drops any claim with fewer than two citations, re-reads every
quote from source and drops it unless byte-exact, and warns on third-person
pronouns that may refer to the reader. Report the drop count — "3 of 15 claims
failed verification" is information about the run, not an error to hide.

## 6. Before they share it

```
shrink audit <report>            # what the owner's copy exposes
shrink render --share …          # pseudonyms kept
```

Tell them plainly: the report is overwritten by the next run, and `shrink purge`
wipes everything.
