# shrink

Reads your own Claude Code session history and hands back a psychological read
of you: a dry statistical tier that is sincere, and a panel of theorists who
over-read it on purpose.

Everything runs locally. Model calls use your own tokens. Nothing leaves the
machine.

**Status: pre-release.** M1 — extractor and denoiser. The panel does not exist yet.

## Try it

```sh
./bin/shrink digest --days 30
```

No model calls, no network. Prints what it found, what it discarded, and why.

## What it reads

| source | what | retention |
|---|---|---|
| `~/.claude/projects/*/<UUID>.jsonl` | full stimulus→response | swept at 30 days by default |
| `~/.claude/history.jsonl` | every prompt you've typed | kept until you delete it |

Two tiers because they answer different questions. Anything about *change over
time* needs the long baseline — "slope" is not a meaningful word across 30 days.
Anything about *how you respond to failure* needs the recent tier, because only
it has what the machine said back.

The tool joins them and tells you its own coverage gap rather than profiling a
month and calling it you.

Your typed words are about 1% of what's on disk. The other 99% is tool output,
file dumps, and the assistant's own text. `shrink` throws that away, which is
why a corpus that looks enormous is actually small enough to reason about whole.

## What it doesn't do

- Leave the machine. No telemetry, no upload, no comparison to other users.
- Read `CLAUDE.md`. How you instruct a machine to treat you is the most loaded
  artifact on disk and it is deliberately out of scope for v1.
- Diagnose. The panel over-reads *behavior* — what you re-ask after it's been
  answered, where politeness drops. It does not have opinions about your mother.
- Invent quotes. Every quote is looked up from source at render time and
  verified byte-exact, or it is dropped.

## Install

Not yet. When it ships it will be a plugin marketplace entry, installed from
this repo directly — it will not be listed in the Anthropic software directory,
because directory policy §1.F bars listed software from reading chat history.

## Layout

```
bin/shrink              single binary, stdlib only, all subcommands
commands/shrink.md      slash-command front door
agents/                 aggregator + panel definitions (M4+)
SCHEMA.md               normalizer contract — read this before touching bin/
eval/                   hand-labeled denoiser eval set (gitignored: real prompts)
```

## Development

`SCHEMA.md` is the contract. It records what is documented, what is community
observation, and what was measured locally — and the JSONL format is officially
undocumented and unstable, so the distinction matters. Anything that surprises
you about the parser is probably explained there.

```sh
./bin/shrink sample -n 200      # emit a stratified labeling set
$EDITOR eval/labels.jsonl       # set "label" on each row
./bin/shrink eval               # score precision against target (>= 0.95)
```

MIT.

### Labeling

```sh
./bin/shrink label                    # loopback, http://127.0.0.1:7331
./bin/shrink label --host 0.0.0.0     # reachable over LAN/VPN
```

Keys: `a` `t` `m` `e` `u` to label, `j`/`k` or arrows to move, `?` reveals what
the rule guessed. Every choice writes through to `eval/labels.jsonl`
immediately — close the tab whenever.

The prediction is hidden by default on purpose. Seeing it first anchors the
labeler to the rule being tested, which is how a denoiser eval quietly grades
itself.
