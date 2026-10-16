# development-skills

A collection of reusable Claude Code skills. Each skill is a self-contained directory under `skills/` with a `SKILL.md` definition; structure and frontmatter conventions are documented in `CLAUDE.md`.

## Verifying a skill is live

A skill only takes effect if it appears in a session's available-skills list. After adding a skill or changing its `name` / `description`:

1. Start a new Claude Code session and confirm the skill's name appears in the available-skills list.
2. If it is missing, the skill has not reached the location Claude Code loads skills from — check that install / sync step.
3. `description` is the trigger surface used by skill matching. After changing it, re-check that the skill still appears, and that it triggers on the tasks it is meant to serve.
