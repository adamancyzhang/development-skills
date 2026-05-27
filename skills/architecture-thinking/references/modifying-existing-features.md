# Reference B: Modifying Existing Features

When modifying existing code, you are working inside an architecture that already has a shape. Your primary obligation is to understand that shape, respect its intent, and either work within it or evolve it explicitly.

## Core Principles

**Read before writing.**
Understand the module you're touching. Read its interface, its dependents, its dependencies. Read the tests — they document expected behavior. Do not modify code you haven't understood. The current structure may be accidental, but assume it was intentional until proven otherwise.

**Fit or evolve — decide explicitly.**
Does the required change fit within the existing architecture, or does it require architectural evolution? This is the critical decision:
- If it fits within the module's responsibility, implement in-place.
- If it adds a new responsibility, split the module before adding.
- If it crosses an existing boundary, evaluate whether to move the boundary or create a new integration path.
- If it conflicts with an existing pattern, evolve the pattern first. Do not create a second pattern alongside the first.

**Preserve conceptual integrity.**
After your change, the system should look like it was designed with this modification in mind. If your change reads as a special case bolted onto a general mechanism, redesign until it reads as part of the mechanism. Special cases are how architecture dies.

**Audit the ripple.**
A change to an existing module can break its dependents in three ways:
- **Interface change:** signature, return type, or contract modification
- **Behavioral change:** same interface, different observable behavior
- **Assumption violation:** the caller relied on an undocumented behavior that you changed

The first is visible to the compiler. The second is visible to tests. The third is invisible to both — it surfaces in production. When modifying behavior, assume callers may rely on that behavior unless you can prove otherwise.

**Clean up what your change orphans.**
If your modification makes a parameter unused, a function dead, an import unnecessary, or a test obsolete — remove them. Leaving orphans is how codebases accumulate dead weight. Your change, your cleanup responsibility.

**Progressiveness is mandatory.**
After your change, is the system easier or harder to understand? Is the module's responsibility clearer or more blurred? Will the next similar change be simpler or more complex? Have you strengthened or weakened the existing patterns?
