# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Minimum diff surface — but cover the full logical radius of each change.**

When editing existing code:
- Don't refactor things unrelated to the change.
- Match existing style, even if you'd do it differently.
- If you notice dead code unrelated to the change, mention it — don't delete it.

A bug rarely exists in isolation. When you identify one error, scan its logical radius — same root cause, same category of mistake, same faulty assumption — and fix them together. One well-scoped pass beats scattered follow-ups.

But don't confuse logical radius with physical proximity. Adjacent code that works correctly is not broken. Fix what shares a cause, not what shares a file.

When your changes create orphans, remove them. Don't leave behind imports with no usage or variables with no readers.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Context Panorama

**Map the full landscape before cutting. The symptom tells you where, not why.**

Before fixing any error:
- Trace the complete call chain from entry point to failure site.
- Distinguish the site of detection from the site of causation — they are rarely the same.
- Identify what invariants held at each boundary and where the first one was violated.

The cost of skipping panorama: you fix the symptom while the root cause survives elsewhere. You miss sibling code paths built on the same faulty assumption. You optimize a local expression of a systemic problem.

Panorama is the prerequisite to precision. The broader the map, the cleaner the cut.

## 6. Multi-Perspective Diagnosis

**No single lens reveals the whole fault. Investigate from multiple angles, in parallel.**

For non-trivial problems, deploy independent perspectives before concluding:
- Call chain topology — who calls whom, what propagates where.
- Data flow — where values originate, how they transform, where they diverge.
- Invariants and preconditions — what each layer assumes about its inputs, which assumption failed.
- Concurrency and state — what else could interleave, what state transitions are possible.
- Error propagation — where the error was born, caught, swallowed, or transformed.

Each perspective yields a hypothesis. Converging hypotheses yield a diagnosis. Single-perspective analysis yields a guess.

Dispatch in parallel, not sequentially. Synthesize before acting. A fix chosen from one angle is a fix that will need another fix tomorrow.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.