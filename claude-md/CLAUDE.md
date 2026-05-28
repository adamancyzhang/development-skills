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

> See also: `architecture-thinking` (Minimal Viable Architecture, no premature generalization), `coding-conventions` (No Over-Design, Forward Thinking Without Forward Building).

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

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

> See also: `test-driven-development` for the full RED-GREEN-REFACTOR methodology with test governance and mock discipline.

## 5. Boundary-Oriented Paradigm

When generating, refactoring, or reviewing any code, treat software as a topology of trust and boundary containment.

### 5.1 Trust Topology & Flow Control

**Principle:** Validate at boundaries, trust internally, encapsulate at exits. Every value is either validated or trusted — there is no middle ground.

For detailed rules on boundary identification, validation protocol, trusted internal logic, and unified exception handling, invoke `coding-conventions`.

### 5.2 Four-Dimensional Limit Deduction

Before finalizing any logic, mentally push the system to its physical and logical limits across four spaces:

- **Space & Scale:** Deduce behavior when inputs are completely absent (null/empty/zero) or at their absolute upper bounds (overflow/max capacity).
- **Time & Concurrency:** Ensure any external wait or coordination has an autonomous reclaim of control (timeouts). Ensure state mutations are atomic and insulated from race conditions.
- **State & Structure:** Maintain invariant integrity. Reject invalid state transitions gracefully according to the domain lifecycle.
- **Resources & Capacity:** Design for graceful degradation or failure isolation when underlying memory, connections, or computing power are exhausted.

### 5.3 Compulsory Thought & Output Protocol

Structure your response and code generation according to the following sequence. Do not skip or merge these sections:

#### [BOUNDARY AUDIT]
- **Entries Identified:** [List specific entries] → **Collapse Mechanism:** [How uncertainty is eliminated]
- **Exits Identified:** [List specific exits] → **Encapsulation Mechanism:** [How leakage is prevented]
- **Trusted Zone Bounds:** [Define the scope where internal trust is absolute]

#### [LIMIT MAPPING]
- **Scale Limit:** When ______ happens, the self-preservation path is ______.
- **Time/Resource Limit:** When ______ happens, the self-preservation path is ______.

#### [CONTRACTUAL CODE]
*Deliver the clean, robust code that 100% mirrors the audit and mapping above.*

## 6. Skill Routing

When a task involves a specific domain, invoke the corresponding skill instead of duplicating its rules:

| When you... | Invoke |
|---|---|
| Write or review any production code | `coding-conventions` |
| Review any code change before commit | `code-review-guidelines` |
| Write new features, fix bugs, or refactor | `test-driven-development` |
| Before ANY code change (assess impact) | `architecture-thinking` |

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
