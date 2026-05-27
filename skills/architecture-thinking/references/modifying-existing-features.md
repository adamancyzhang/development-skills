# Reference B: Modifying Existing Features — Evolving Architecture

When modifying existing code, you are working inside an architecture that already has a shape. Your primary obligation is to understand that shape, respect its intent, and either work within it or evolve it explicitly.

## The Existing Feature Modification Protocol

**Step 1 — Read before writing.**
Understand the module you're touching. Read its interface, its dependents, its dependencies. Read the tests — they document expected behavior. Read the commit history — it reveals what changes have been made and why. Do not modify code you haven't understood.

**Step 2 — Identify the architectural intent.**
Why is this module structured the way it is? What problem was the original designer solving? The current structure may be accidental, but assume it was intentional until proven otherwise. If you can't discern the intent, find it before modifying.

**Step 3 — Determine: fit or evolve?**
Does the required change fit within the existing architecture, or does it require architectural evolution? This is the critical decision:

| The change... | Action |
|--------------|--------|
| Fits within the existing module's responsibility | Implement in-place. No architectural change needed. |
| Fits within the existing module boundary but adds a new responsibility | The module now has two reasons to change. Split it before adding. |
| Crosses an existing module boundary | The boundary may be wrong. Evaluate whether to move the boundary or create a new integration path — but do so explicitly. |
| Conflicts with an existing architectural pattern | Evolve the pattern first. Update all existing code that follows the old pattern, or explicitly document the transition. Do not create a second pattern alongside the first. |

**Step 4 — Preserve conceptual integrity.**
After your change, the system should look like it was designed with this modification in mind. If your change reads as a special case bolted onto a general mechanism, redesign until it reads as part of the mechanism. Special cases are how architecture dies.

**Step 5 — Audit the ripple.**
A change to an existing module can break its dependents in three ways:
- **Interface change:** signature, return type, or contract modification
- **Behavioral change:** same interface, different observable behavior
- **Assumption violation:** the caller relied on an undocumented behavior that you changed

The first is visible to the compiler/type checker. The second is visible to tests. The third is invisible to both — it surfaces in production. When modifying behavior, assume callers may rely on that behavior unless you can prove otherwise.

**Step 6 — Clean up what your change orphans.**
If your modification makes a parameter unused, a function dead, an import unnecessary, or a test obsolete — remove them. Leaving orphans is how codebases accumulate dead weight. Your change, your cleanup responsibility.

**Step 7 — Verify the progressive impact.**
After your change:
- Is the system easier or harder to understand?
- Is the module's responsibility clearer or more blurred?
- Will the next similar change be simpler or more complex?
- Have you strengthened or weakened the existing patterns?

## Modification Checklist

- [ ] Understood the module's current architecture, intent, and history before modifying
- [ ] Determined whether the change fits or requires architectural evolution
- [ ] If evolution is needed, it is explicit and scoped before implementation
- [ ] No new special cases bolted onto general mechanisms
- [ ] Dependents audited for interface, behavioral, and assumption impacts
- [ ] Orphaned code (unused imports, dead functions, obsolete tests) removed
- [ ] Progressive impact assessed: the system is no harder to iterate than before
