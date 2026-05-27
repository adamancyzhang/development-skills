---
name: architecture-thinking
description: "MANDATORY before any code change: assess architectural impact, verify alignment, ensure progressiveness. Every edit must serve the architecture and enable future iteration."
version: 4.0.0
author: Adamancy Zhang
license: MIT
---

# Architecture Thinking

## Overview

Every line of code sits inside an architecture. A local change made without understanding that architecture is a bet against the design — and the design always wins, because the design is what every other line of code already assumes.

Architecture thinking is not a phase. It is a discipline applied before every change, at every scale.

**Core principle:** A change that solves the immediate problem but corrupts the architecture is not a solution. It is deferred damage.

## When to Use

**BEFORE ANY CODE CHANGE. No exceptions.**

- Before adding a function, class, or module
- Before modifying an existing function, class, or module
- Before fixing a bug
- Before refactoring
- Before adding a dependency
- Before choosing where to put a new file
- Before deleting any code
- Before writing a single line

The smallest change can introduce a dependency in the wrong direction, couple two concerns that should be separate, or bypass an interface that exists for a reason. Every change is an architectural act — whether you think about it or not.

## The Iron Law

```
DEPENDENCY DIRECTION MUST FOLLOW STABILITY
```

Dependencies must point from unstable (frequently changed) toward stable (rarely changed) code. Never the reverse.

If module A changes every sprint and module B hasn't changed in a year, B must never depend on A. If you find B importing from A, stop. Invert the dependency through an interface owned by B.

No exceptions: not for "it's just one import," not for "we'll fix it later," not for "the interface is stable even if the implementation isn't." A stable module depending on an unstable one is architectural rot. The rot spreads.

## Five Gates

Before touching any file, answer these five questions. If you cannot answer them, do not change the code.

**Gate 1: Where am I?**
Identify the architectural layer and module you're touching. Is this domain logic, infrastructure, application orchestration, or presentation? What is this module's single responsibility?

**Gate 2: What depends on this?**
Trace incoming dependencies. What modules, functions, or callers rely on this code's current behavior, signature, or contract? Changing this code means accepting consequences for every dependent.

**Gate 3: What does this depend on?**
Trace outgoing dependencies. Does this code already depend on stable or unstable modules? Will your change add a new dependency? In what direction will that dependency point?

**Gate 4: Does this change violate the architecture?**
Check against the core principles. Will this change:
- Create a circular dependency?
- Make a stable module depend on an unstable one?
- Mix a new concern into a module that already has one?
- Bypass an existing interface or abstraction?
- Add a hidden dependency (global state, service locator)?
- Introduce framework-specific code into domain logic?
- Couple two modules that change for different reasons?
- Reduce the system's capacity for future iteration?

If the answer to any of these is yes, the change is architecturally invalid. Do not proceed.

**Gate 5: What is the minimal architectural cost?**
Given the constraints, what is the smallest change that satisfies the requirement, respects the architecture, AND preserves future optionality? If the requirement itself conflicts with the architecture, the architecture may need to evolve — but that evolution must be explicit, intentional, and scoped before any implementation begins.

## Core Principles

### Separation of Concerns

A module should have exactly one reason to change. If two different stakeholders drive changes to the same module, the concerns are not separated.

The test: can you describe what a module does without using the word "and"? If not, split it.

### High Cohesion, Low Coupling

**Cohesion:** things that change together live together. If changing a business rule always requires editing two files in different directories, cohesion is broken.

**Coupling:** things that change for different reasons live apart. If changing the database schema forces changes to the UI layer, coupling is too high.

The test: pick a likely change. How many files must you touch? If the answer is more than the number of concerns directly affected by that change, the architecture is fighting you.

### Dependency Inversion

High-level policy must never depend on low-level details. Both must depend on abstractions. The abstraction is owned by the high-level policy, not by the low-level implementation.

### Interface-First Design

Design the contract before the implementation. The interface is the shared understanding between caller and callee. If the interface is wrong, both sides build on a broken foundation.

**Interface design checklist:**
- What does the caller need to know? Nothing more.
- What does the caller need to provide? Nothing more.
- What can go wrong, and how is it communicated?
- Can a caller use this interface incorrectly? If so, redesign until misuse is impossible or obvious.

A good interface makes the right thing easy and the wrong thing hard.

### Minimal Viable Architecture

Build only what you need now to support the decisions you've made. Do not build for hypothetical futures — every abstraction you add today carries a maintenance tax forever.

**The rule:** add architectural structure only when the absence of that structure is causing real, measurable pain right now. Not next sprint. Now.

**Exceptions (the only valid reasons to add structure early):**
- You have built this exact thing before and know from experience where the seams must go
- The cost of adding it later is existential (data migration that would require downtime)
- A hard external constraint requires it (compliance, security boundary, third-party contract)

If none of these apply, defer. Structure added without evidence of need is speculation. Most speculation is wrong.

### Progressiveness

```
EVERY CHANGE MUST LEAVE THE SYSTEM EASIER TO ITERATE, NOT HARDER
```

Today's feature is tomorrow's legacy code. Every change you make either opens options for the next developer or closes them. Architecture that only serves the current requirement is incomplete — it must also preserve and expand the system's capacity for future change.

**The Progressiveness Test — after your change, ask:**
1. **Pattern consistency:** Does this change follow the existing architectural patterns, or does it introduce a new pattern? If new, is the new pattern explicitly justified as an architectural evolution?
2. **Optionality:** Does this change open options or close them? A change that makes a future direction impossible should require explicit approval.
3. **Conceptual integrity:** After this change, does the system still look like it was designed by one mind? Or does it read like a series of disconnected fixes?
4. **Abstraction quality:** If you added an abstraction, is it based on a real pattern in the domain, or is it a convenience wrapper? Convenience abstractions leak. Domain abstractions endure.
5. **Complexity budget:** Did this change add more complexity than the problem warrants? Every conditional branch, every configuration option, every new concept in the codebase is a tax on every future change.

**Progressiveness is not prediction.** You are not guessing what features will be needed. You are ensuring that whatever features are needed, the system can accommodate them without architectural surgery.

## Evaluation Criteria

Judge every architectural decision against these six criteria. A decision that improves one at the expense of another requires explicit justification.

### Testability

Can each component be tested in isolation, without standing up the entire system?

**Signs of good testability:**
- Business logic can be tested without a database, network, or filesystem
- Dependencies can be substituted with test doubles at the boundary
- Tests are fast (milliseconds, not seconds) because they don't cross process boundaries
- Testing a component requires no knowledge of its internal implementation

**If you can't test it, you can't trust it. If you can't trust it, you can't change it.**

### Changeability (Adaptability)

When requirements change, how much code must change with them?

**Signs of good changeability:**
- Adding a new feature means adding new code, not modifying existing code (Open/Closed Principle)
- Changing a business rule touches one location
- Changing a technology choice (database, message queue, UI framework) is contained within an adapter layer
- The most frequently changed parts of the system have the fewest dependents

**Architecture is insurance.** The premium is paid in upfront design. The payout is cheap changes later.

### Understandability

Can a new developer read a module and understand what it does and how it connects?

**Signs of good understandability:**
- The module name describes its responsibility precisely
- The public interface tells you everything you need to know to use it
- Reading the top-level structure reveals the system's purpose without reading implementation details
- Dependencies are explicit in constructors or function signatures, not hidden in global state or service locators

**Code is read far more than written. Architecture is communication to future maintainers.**

### Composability

Can components be rearranged to solve new problems without modifying the components themselves?

**Signs of good composability:**
- Components are self-contained: they don't assume what surrounds them
- Data flows are explicit (input → transform → output) rather than implicit (side effects, global state)
- Components communicate through well-defined interfaces, not shared mutable state
- The system can be understood as a composition of smaller systems

**Composability is the difference between a toolkit and a monolith.** A toolkit lets you build things the original designer never imagined. A monolith only does what it was built to do.

### Explicit Boundaries

Every boundary in the system must be intentional and justified. A boundary without a reason is accidental complexity.

**Valid reasons for a boundary:**
- Different rates of change on each side
- Different teams own each side
- Different deployment lifecycles
- Different testing strategies
- A natural seam in the domain model

**Invalid reasons for a boundary:**
- "This is how frameworks structure things"
- "We might need to split this later"
- "It feels cleaner"

Boundaries have a cost: they add indirection, they make cross-cutting changes harder, they require translation layers. Every boundary must earn its keep.

### Progressiveness (Temporal Criterion)

Does the architecture enable or resist future iteration? This criterion evaluates architecture across time, not just at a single point.

**Signs of progressive architecture:**
- Each iteration builds on the previous one without undoing or working around it
- The system's conceptual model is stable even as implementations evolve
- Established patterns are reinforced, not undermined, by new additions
- The cost of adding the Nth feature in a domain is lower than the cost of adding the (N-1)th
- Deletion of a feature leaves the architecture cleaner, not wounded

**Signs of regressive architecture:**
- Each new feature requires a workaround for a previous design choice
- The codebase contains fossil layers — abandoned patterns superseded by newer ones but never removed
- The same problem is solved differently in different parts of the system
- New developers are told "don't look at module X, we do it differently now"
- Removing a feature requires delicate surgery because its dependencies are tangled

**The progressive architecture mandate:** after your change, the next developer facing a related task should find their job easier than you found yours. If you are making their job harder, you are creating architectural debt — even if your change works perfectly.

## Anti-Patterns

- **God object / god module** — a class or module that knows about everything and does everything. Split along responsibility boundaries.
- **Circular dependencies** — A depends on B, B depends on A. The two modules are actually one module. Merge them or extract a shared contract.
- **Leaky abstraction** — the abstraction exposes implementation details the caller must understand to use it correctly. The abstraction has failed.
- **Premature generalization** — building a framework for one use case. "We might need it later" is not a requirement. Abstract only after the second concrete case.
- **Shotgun surgery** — a single change requires editing files across many modules. The modules are coupled on an invisible axis. Find the missing abstraction.
- **Hidden dependencies** — global state, service locators, singletons reached through static methods. A dependency not visible in the constructor is a lie.
- **Inappropriate intimacy** — modules that know about each other's internal data structures. They will break together.
- **Architecture by framework** — letting the framework dictate module boundaries. The framework serves the architecture, not the reverse.
- **Speculative architecture** — adding structure for requirements that don't exist. Every speculative abstraction is a bet against the future. Most lose.
- **Symmetric but wrong** — treating everything the same way (every entity gets a repository, every service gets an interface) without considering whether each needs it. Architecture must be asymmetric where the domain is asymmetric.
- **Local fix, global rot** — a quick change that solves the immediate bug but violates a dependency rule, bypasses an abstraction, or couples unrelated concerns. This is how architecture dies — one "just this once" at a time.
- **Fossil layers** — the codebase contains multiple architectural patterns because each era introduced a new one without retiring the old. New developers must learn all of them. Pick one pattern per concern and migrate or retire the rest.
- **Completion over progressiveness** — a feature that works but makes the system harder to change. The pressure to ship is real, but a "complete" feature that blocks the next three features is a net loss. If you must take on architectural debt to ship, document it, schedule its repayment, and never let it compound silently.

## Red Flags — Stop and Reassess

If any of these appear in a design or change, stop and fix before coding:

- A module that imports from a module that imports from it (circular dependency)
- A constructor with more than 4-5 parameters (too many responsibilities or missing abstraction)
- A class name containing "Manager", "Handler", "Processor", or "Util" (vague responsibility)
- A module whose public interface changes every time you add a feature elsewhere (unstable abstraction)
- Configuration or business logic duplicated across modules (missing single source of truth)
- A change to an "infrastructure" detail (database, framework, protocol) requiring changes to business logic files (leaky abstraction)
- A module that cannot be tested without a running database, message queue, and external API (missing boundaries)
- An interface with only one implementation (either the interface is unnecessary or you found the wrong abstraction)
- Two modules that always change together (they are one module — merge or find the real seam)
- Framework types or annotations appearing in domain logic files (framework has leaked into the core)
- A proposal to bypass an existing abstraction "just for this one case"
- A change that introduces a new pattern without retiring or reconciling the old one (fossil layer in progress)
- A feature implementation that the implementer cannot explain the architectural rationale for (code without architectural intent)
- "We'll fix this in the next iteration" without a concrete plan (deferred architecture is abandoned architecture)
- Deletion of code without tracing its dependents (amputation without diagnosis)
- An existing architectural pattern being ignored rather than explicitly evolved (passive architecture degradation)

## Verification Checklist

Before approving any change:

- [ ] Five Gates passed: Where am I? What depends on this? What does this depend on? Does this violate the architecture? What is the minimal cost?
- [ ] The change belongs in the module I'm touching (correct concern, correct layer)
- [ ] No new circular dependency introduced
- [ ] No new dependency from a stable module toward an unstable module
- [ ] No existing interface or abstraction bypassed
- [ ] Progressiveness assessed: this change does not make future iteration harder
- [ ] Dependencies point from unstable toward stable modules
- [ ] Each module has exactly one reason to change
- [ ] High-level policy does not depend on low-level details
- [ ] Interfaces are designed from the caller's perspective
- [ ] Each component can be tested in isolation
- [ ] The design makes the next likely change easier, not harder

Cannot check all boxes? The change is not ready. Do not proceed.

## Final Rule

```
Before any code change  → Five Gates passed
Dependency direction    → toward stability, never toward volatility
Module boundary         → at the seam where rates of change differ
Interface design        → from the caller's need, not the implementation's shape
Abstraction             → only after the second concrete case
Simplicity              → exactly enough design, nothing more
Progressiveness         → every change makes the next change easier, not harder
Local fix, global rot   → blocked
Otherwise               → architectural debt, compounding daily
```
