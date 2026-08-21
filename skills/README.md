# siri-cli agent skill

Portable [Agent Skill](https://code.claude.com/docs/en/skills) for driving the
**real macOS Siri** from any CLI agent. Lets an agent read/act on macOS system
data (Notes, Calendar, Messages, Weather, Reminders, Timers/Alarms) through
Siri's natural-language surface — no third-party APIs or extra installs beyond
the `siri` command.

The skill lives at [`siri-cli/SKILL.md`](siri-cli/SKILL.md). It is format-agnostic:
any agent that reads a `SKILL.md` directory (name/description/version frontmatter)
can load it, and it carries an `openclaw` install spec for the `siri-cli` brew
formula.

## Install

The only real dependency is the `siri` command itself:

```bash
brew tap Pasithea0/homebrew-siri-cli
brew trust --formula pasithea0/siri-cli   # one-time (Homebrew 6+ third-party tap)
brew install siri-cli
siri status                                # all lines OK?
```

Then point your agent at the skill directory (symlinks work):

| Agent | Location |
|-------|----------|
| **OpenClaw** | `~/.openclaw/workspace/skills/` (or `clawhub install Pasithea0/siri-cli`) |
| **Claude Code** | `~/.claude/skills/` (or project `.claude/skills/`) |
| **Hermes** | `~/.hermes/skills/` |
| **VS Code / Copilot** | project `.github/skills/` |
| **Goose / other** | `npx agent-skills-cli add Pasithea0/siri-cli` |

E.g. Claude Code:

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/skills/siri-cli" ~/.claude/skills/siri-cli
```

## Notes

- **One-shot only** — a single `siri "query"` per call; no follow-ups yet.
- **Short responses** — AX-tree capture truncates long content at "Show More";
  optimized for short answers, not bulk extraction.
- Requires **macOS 27** and Accessibility (plus Screen Recording for `siri status`).
  See the main [README](../README.md) for permissions and troubleshooting.
