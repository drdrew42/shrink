---
description: Read your own Claude Code history and hand back a psychological read
argument-hint: "[here] [--days N] [--offline]"
---

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

Run `freud`, `jung`, and `goffman` **in parallel**, each with the same packet
and no other context. Do not summarise the packet for them and do not hand any
of them an observation the others lack — a finding that only exists because you
primed one theorist will not reproduce on anyone else's corpus.

Each writes findings JSON. Merge into one JSONL, one object per theorist.

## 5. The report

Run `analyst` over the theorists' claims plus the packet. It writes the report:
one voice, second person, merged sections.

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
