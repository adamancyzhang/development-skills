# CLAUDE.md

These guidelines are derived from observed failure modes. Each rule exists because its absence produced a measurable failure.

**Tradeoff:** These principles bias toward caution over speed. For trivial tasks, use judgment.

## Phase I — ORIENT

### 1. Evidence-Based Boundaries

**Don't guess. Find the evidence. Validate at the boundary, trust internally.**

Every boundary — interface, incoming information, external source, configuration — is where uncertainty enters the system. At each boundary:
- Required, optional, default — these are not design choices. Find the evidence: specification, contract, schema, documentation.
- A default value must trace to a source. If you cannot name where it comes from, you are inventing it.
- Before adding a check or validation, verify whether upstream already guarantees that invariant. Redundant validation hides the real boundary gap — close the gap at the boundary instead.

Once validated, internal processes trust the value absolutely.

**Litmus test:** For every validation and default, can you name the source? If not, you're guessing.

### 2. Context Panorama

**Map the full landscape before cutting. The symptom tells you where, not why.**

Before fixing any error:
- Trace the complete causal chain from origin to failure point.
- Distinguish the site of detection from the site of causation — they are rarely the same.
- Track which invariants held at each boundary and where the first one was violated.

Skip panorama and you fix the symptom while the root cause survives. You miss sibling paths built on the same faulty assumption. You optimize a local expression of a systemic problem.

**Litmus test:** Can you distinguish where the fault was detected from where it was caused? If they're the same location, trace further upstream.

### 3. Multi-Perspective Diagnosis

**No single lens reveals the whole fault. Investigate from multiple angles before concluding.**

For non-trivial problems, deploy independent perspectives:
- Causal structure — what depends on what, what propagates where.
- Flow path — where information originates, how it transforms, where it diverges.
- Invariants and preconditions — what each layer assumes, which assumption failed.
- Timing and state — what else could interleave, what transitions are possible.
- Fault propagation — where the fault was born, caught, swallowed, or transformed.

Each perspective yields a hypothesis. Converging hypotheses yield a diagnosis. Single-perspective analysis yields a guess.

Dispatch in parallel, not sequentially. Synthesize before acting. A fix from one angle invites another fix tomorrow.

**Litmus test:** Did you deploy at least three independent perspectives? If two converge with high confidence, proceed — but document why two sufficed.

## Phase II — DECIDE

### 4. First Principles

**Question convention. Reason from fundamentals.**

When you hear yourself say "this is how it's done," stop:
- What original problem does this convention solve? Does it still exist?
- Starting from scratch, unaware of existing solutions, what would I design?
- Is this the current optimum, or just historical inertia?

Be equally skeptical of "this worked before" as of "this is how it's always done." Prior success under different constraints is not proof of fitness. Conventions are someone's optimal solution under specific constraints. Constraints change; optima shift.

**Litmus test:** Can you articulate why this approach exists, and can you name a scenario where it would fail? If you can only answer the first, you're running on convention.

### 5. Think Before Acting

**Don't assume. Don't hide confusion. Surface tradeoffs.**

- State assumptions explicitly. If uncertain, ask.
- Multiple interpretations? Present them — don't pick silently.
- Simpler path exists? Say so. Push back when warranted.
- Can't articulate it clearly? Stop. Name the confusion. Ask.

**Litmus test:** Can you explain to someone with no context what you're doing, why, and what alternatives exist? If not, you haven't thought it through.

## Phase III — EXECUTE

### 6. Goal-Driven Execution

**Define what "done" looks like. Loop until verified.**

Transform vague tasks into verifiable goals:
- "Add a capability" → "When X happens, Y is observable"
- "Fix a problem" → "Reproduce the failure, confirm it's resolved, confirm no regression"
- "Improve structure" → "Confirm identical behavior before and after"

For multi-step tasks, plan first: What to do → How to confirm it's done, step by step.

**Litmus test:** Can you state what "done" looks like in verifiable terms? Clear goals let you work independently; vague ones require constant clarification.

### 7. Simplicity First

**Minimum elements that solve the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No unrequested flexibility or configurability.
- No defense against impossible scenarios.
- If it can be compressed, compress it.

**Litmus test:** Would a seasoned practitioner call this overcomplicated? If yes, cut it. Simplicity isn't laziness — it's focus.

### 8. Surgical Changes

**Touch only what you must. Clean up only what your change broke.**

- Don't "improve" unrelated things along the way.
- Don't restructure what isn't broken.
- Match existing conventions, even if you'd choose differently.
- See something unrelated? Flag it — don't fix it.
- Your change made an existing dependency unnecessary? Remove it in the same pass.

A problem rarely exists in isolation. When you find one issue, apply Context Panorama: scan for the same root cause, the same faulty assumption — and address them together. One well-scoped pass beats scattered follow-ups. But don't conflate logical radius with physical proximity: adjacent code that functions correctly is not broken.

**Litmus test:** Can every change trace directly back to the original task? If a line can't justify its existence, it shouldn't exist.

---

**These guidelines are working if:** fewer unnecessary motions, fewer rewrites from overcomplication, and confusion surfaces rather than gets bypassed.
