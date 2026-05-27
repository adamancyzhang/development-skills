# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a collection of reusable Claude Code custom skills. Each skill is a self-contained directory under `skills/` with a `SKILL.md` file that defines the skill's behavior, rules, and methodology.

## Skill Structure

```
skills/<skill-name>/
  SKILL.md    # Skill definition (YAML frontmatter + markdown body)
```

## SKILL.md Frontmatter Convention

Every `SKILL.md` starts with YAML frontmatter:

```yaml
---
name: kebab-case-name
description: "One-line summary of what the skill does and when to use it."
version: X.Y.Z
author: Adamancy Zhang
license: MIT
---
```

The `name` and `description` fields are used by Claude Code for skill matching and triggering. Keep the description specific about both the skill's purpose and its trigger conditions.

## Creating or Modifying Skills

Use the `skill-creator` skill for creating new skills, editing existing ones, or running evaluations. Do not manually copy-paste skill boilerplate without it.

## Skills in This Repo

- **architecture-thinking** — Mandatory pre-change architectural assessment: Five Gates must be passed before any code modification. Covers dependency direction, separation of concerns, interface-first design, evaluation criteria, trade-off analysis, and anti-pattern detection. No code change without architectural impact assessment first.
- **code-review-guidelines** — Enforces strict review rules: no silent fallbacks, no copy-paste test logic, fail loud on configuration errors, structural decomposition for testability.
- **test-driven-development** — Enforces RED-GREEN-REFACTOR with mandatory verification at each phase, test governance (core vs scratch classification), and mock trust-justification requirements.

## No Build/Tests

This repo has no build system, package manager, or test suite. Skills are markdown documents consumed directly by Claude Code.
