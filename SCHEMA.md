# SCHEMA.md — normalizer contract

M0 deliverable. What `shrink` assumes about Claude Code's on-disk format, why,
and how confident we are in each assumption.

Anthropic states the session JSONL format is internal and unstable and says not
to build a parser around it. There is no alternative — `/export` and
`claude -p --output-format json` operate on one session at a time, so bulk
history has no supported route. We parse anyway, knowingly. Everything below is
written to fail loudly on drift rather than quietly on assumption.

**Confidence tags:** `[doc]` official docs · `[obs]` community reverse-engineering
· `[measured]` verified locally on the reference corpus · `[assumed]`.

Reference corpus: 45 sessions, 9,723 user records, builds 2.1.200–2.1.220,
macOS, 2026-08-03.

---

## 1. Discovery

Sessions are `~/.claude/projects/<mangled-cwd>/<UUID>.jsonl`. The directory name
is the project cwd with separators replaced by `-`, so **names begin with `-`**
and every shell path needs a `./` prefix. `[measured]`

`~/.claude/projects/` is a **global store** — every project directory on the
machine, readable regardless of cwd. The default corpus is all projects. `[measured]`

### Safe glob

Top-level `<UUID>.jsonl` per project directory only. Excluded:

- `agent-*.jsonl` — flat subagent layout, older builds `[obs]`
- anything under `subagents/`, `tool-results/`, or a session-UUID subdirectory —
  current layout `[doc]`
- belt-and-braces: any record with `isSidechain: true`

A recursive `**/*.jsonl` ingests subagent transcripts as if the human wrote
them. On the reference machine that is 177 extra files against 45 real sessions
— a 4:1 contamination ratio. `[measured]`

Subagent transcripts are **not** swept by `cleanupPeriodDays` (#58154), so they
accumulate indefinitely and are stale as well as wrong. `[obs]`

---

## 2. Retention — why the corpus is two-tier

`~/.claude/projects/` is swept at startup, default 30 days, keyed to **file
mtime**. `[doc]` for the period, `[obs]` for the mtime keying, `[measured]`
locally (exact cliff at 29 days, `.last-cleanup` stamped at launch).

Because mtime is what the reaper reads, a session *started* long ago and
*resumed* recently survives with its old content intact — so content spans can
exceed the window. `[measured]`

`~/.claude/history.jsonl` is **not** on that clock — documented "kept until you
delete." No size cap, rotation, or truncation. `[doc]` Reference corpus:
9,909 prompts over ~8 months against 1,007 authored turns over 30 days. `[measured]`

| tier | source | span | content | missing |
|---|---|---|---|---|
| long baseline | `history.jsonl` | months | authored prompts, pre-denoised | responses, outcomes, errors |
| recent depth | `projects/*.jsonl` | 30 days | full stimulus→response | anything older |

Time-series claims (slope, drift, curve) run on the long baseline — "slope" is
not meaningful across 30 days. Stimulus-response claims (repair, abandonment,
register shift) run on recent depth. `sessionId` appears in both, so the tool
**joins them and reports its own coverage gap** rather than profiling a month
and calling it the user.

Gap sources to detect, not assume away: `CLAUDE_CODE_SKIP_PROMPT_HISTORY`
suppresses writes entirely, and `claude project purge` (v2.1.124+) filters
`history.jsonl` per project. `[doc]`

Never recommend `cleanupPeriodDays: 0` — rejected by validation now, and in
builds ≤ v2.1.34 it silently disabled all transcript persistence (#23710). `[obs]`

---

## 3. The authored-turn rule

The denoiser's only job: is this text something the human typed?

```
authored  ⟺  type == "user"
          ∧  toolUseResult is absent        ← carries 86% of the discrimination
          ∧  isMeta is falsy
          ∧  content is a string or text block (not tool_result)
          ∧  userType == "external"         ← inert guard, see below
          ∧  isSidechain is false           ← inert guard
          ∧  text is non-empty after wrapper stripping
```

Measured on 9,723 user records:

| kind | n | share |
|---|---|---|
| tool_result | 8,401 | 86.4% |
| authored | 1,083 | 11.1% |
| empty (wrappers only) | 132 | 1.4% |
| meta | 104 | 1.1% |
| unrecognized | 3 | 0.0% |

**`userType` and `isSidechain` are inert on top-level session files.** `userType`
is present on all 9,716 records and always `"external"`; `isSidechain` is always
`false`, because sidechains live in separate files by construction. `[measured]`
They are kept as free guards — they become load-bearing only if a future version
inlines sidechains — but they are not the safety margin. `toolUseResult` is.

There is no documented flag meaning "the human typed this." `[obs]`

### Wrapper stripping

`<system-reminder>`, `<command-name>`, `<command-message>`, `<command-args>`,
`<local-command-stdout>` and friends are injected **into** authored turns, not
sent as separate records. `[doc for the mechanism, measured for the tags]`

So a turn is **stripped, never discarded**, for containing one — a reminder
appended to something you typed does not make it not-yours. Discarding on
presence would drop every session-start message. Turns that are *only* wrapper
content fall out as `empty` (132 observed).

Unclosed variants occur when output was truncated mid-write; the stripper
handles a dangling open tag to end-of-string.

### Pastes

Flagged, not dropped: `len >= 1500 ∧ lines >= 20 ∧ mean line < 120 chars`.
43 of 1,007 turns flagged. `[measured]` The eval set adjudicates whether the
threshold is right — a hand-labeled corpus is the arbiter, not the heuristic.

Median authored turn is 236 chars against a mean of 1,181. The distribution is
severely right-skewed, which is exactly why paste handling matters and why any
statistic over turn length must be a median.

---

## 4. Ordering and segments

`parentUuid` does **not** reconstruct a single linear order. `[obs]`

- multiple null-parent roots exist (first line, each sidechain root, each
  compact boundary)
- compaction emits `type:"system"` / `subtype:"compact_boundary"` carrying
  `logicalParentUuid` — the real pre-compaction pointer
- `/fork` and `/subtask` start new files with no backlink to the branch point

The tool therefore treats compact boundaries and orphan roots as **hard segment
breaks**, orders within a segment by `timestamp` (line position as tiebreak
only), and **never crosses a boundary silently**.

This matters most for `excerpt`: repair sequences are the likeliest thing to
span a compaction, and a silently-wrong excerpt is worse than a short one — it
hands a theorist a stimulus that did not precede the response. `excerpt` must
report truncation at a boundary rather than returning the wrong neighbours.

> **Open:** zero `compact_boundary` records in the reference corpus despite
> `autoCompactEnabled: true`. Either no session reached the threshold, or the
> subtype is named differently in 2.1.2xx. Probe before relying on the break
> detection.

---

## 5. Token and cost data — mostly unusable

`message.usage` on assistant records: `input_tokens`, `output_tokens`,
`cache_creation_input_tokens`, `cache_read_input_tokens`, plus nested
`cache_creation.ephemeral_{5m,1h}_input_tokens`. No session-total field. `[obs]`

Two traps:

1. **`input_tokens`/`output_tokens` are streaming placeholders** — 0 or 1 in
   ~75% of entries, undercounting 100–174×; output excludes thinking tokens.
   Only the **cache fields** are accurate. `[obs]`
2. **Duplicated usage** — one API response emits multiple `assistant` lines,
   each carrying a copy of the same `usage`, sharing a `requestId`. Naive
   summation over-counts ~2.3×. Dedup by `requestId`. `[obs]`

Consequence for the dry tier: **cache-read ratio and paste-to-speech ratio are
reportable; median tokens is not.** If real token or cost numbers are ever
wanted they come from `stats-cache.json` or the statusline payload, never the
transcript.

---

## 6. Record types

Whitelisted as known: `user`, `assistant`, `system`, `attachment`,
`last-prompt`, `mode`, `permission-mode`, `queue-operation`, `ai-title`,
`bridge-session`, `file-history-snapshot`, `file-history-delta`, `pr-link`,
`summary`, `progress`, `custom-title`, `agent-name`.

Anything else is **counted and reported, never dropped**. Zero unknowns on the
reference corpus. `[measured]`

`attachment` is the highest-volume type by count and carries injected context —
hook output, task reminders, IDE file-open events, skill listings, permission
changes — **not authored prose**. Skipped for personality signal. One-time audit
for paste/image payloads is still owed. `[obs]`

`bridge-session` and `queue-operation` semantics are undocumented and
unconfirmed by any community source. Both are ignored; neither is assumed empty.

Records carry no schema-version field. The per-line `version` field names the
build that wrote them — the reference corpus spans 2.1.200 through 2.1.220
across 45 sessions, so **a single corpus routinely mixes builds** and the
normalizer cannot assume one shape per run. `[measured]`

---

## 7. Archaeologist posture

Non-negotiable, because the format is explicitly unstable:

- tolerant line parsing — skip bad lines, never throw
- whitelist known types, **archive unknowns raw** rather than dropping
- stamp every ingested line with its per-line `version`
- `SUMMARY_VERSION` on derived data so drift can be backfilled
- `toWellFormed()` at ingestion — older builds truncated tool output by byte
  length, leaving lone UTF-16 surrogates mid-emoji `[obs]`
- strip base64 image payloads, keep a `has_image` shape
- dedup by `uuid` across files, excluding the session being indexed (self-match
  dedup silently deletes a whole session). Zero replays observed locally, but
  the guard is free `[measured]`

---

## 8. Identifier barrier

No raw identifier crosses into a model call, by any path — packet **or**
`excerpt` output. Pseudonymize repos to stable opaque labels; the renderer
re-hydrates real names locally at render time, the same mechanism already used
for quotes-by-ID.

Order is **verify → redact → render**. Verification anchors to the
pre-redaction string; redacting first makes byte-exact verification
unsatisfiable.

Exact on structured fields (paths, hostnames, emails, key-shaped strings, known
project names). Best-effort on prose — "the dainamiq linker" typed mid-sentence
is caught by a proper-noun pass seeded with known repo names, and "most" is the
honest word. The tool claims what it can verify, never "nothing sensitive
leaves."

---

## 9. Probes still owed

Folded into M1's test suite rather than run as a separate pass.

1. `compact_boundary` subtype naming in 2.1.2xx — see §4
2. `history.jsonl` `display`: pre- or post-slash-command expansion
3. whether queued prompts are written once or twice
4. exact wrapper-tag set in the current build (the stripper's list is
   observational)
5. `bridge-session` / `queue-operation` record shape
6. `.last-cleanup` semantics — does it gate the sweep to once per day
7. whether one `Bash(shrink:*)` rule suppresses all first-run prompts
8. `attachment` audit for paste/image payloads carrying authored text
