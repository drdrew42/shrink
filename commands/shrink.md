---
description: Read your own Claude Code history and hand back a psychological read
argument-hint: "[here] [--days N]"
---

Run `shrink digest` and interpret the result for the user.

- Bare `/shrink` covers every project on the machine.
- `/shrink here` narrows to the current project.
- `--days N` overrides the window (default 30, which is what a default-config
  user actually has on disk).

Print the resolved plan — sessions, date span, authored KB — and confirm before
spending anything. The dry tier costs nothing; the panel does.

Do not read `~/.claude/projects/` directly. Everything goes through `bin/shrink`
so there is one permission surface instead of a prompt storm.
