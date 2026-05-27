# Reference A: New Feature Development

When building something new, you are creating the foundation that future changes will build upon. Your primary obligation is to establish clear boundaries, clean interfaces, and a coherent conceptual model.

## Core Principles

**Domain before software.**
The code must model the domain, not the other way around. If the domain model is wrong, no amount of clean code will fix it. Name the concepts. Understand their relationships. The domain defines the architecture, not the framework.

**Seams follow rates of change.**
Module boundaries exist where different rates of change exist. Which concepts will evolve independently? These are your boundaries. A seam is not where the framework suggests a split — it is where the domain naturally separates concerns that change for different reasons.

**Interfaces serve callers.**
Design the contract from the caller's perspective. The interface exists to serve callers, not to expose the implementation. If writing a test against the interface is painful, the interface needs redesign before implementation begins.

**Dependencies point toward stability.**
Map the dependencies between new modules. Every arrow should point from higher-volatility toward lower-volatility. If two arrows point at each other, redraw the boundary. If a low-volatility module depends on a high-volatility one, invert through an interface.

**Fit or explicitly evolve.**
Does this new feature fit within the existing architectural patterns? If it introduces a new pattern, is that pattern explicitly chosen as an architectural evolution, or is it an accidental divergence? Accidental divergence is how a system accumulates multiple personalities.

**Design for likely follow-up.**
After this feature ships, what are the three most likely follow-up requests? Your design should not build for those requests, but it should not block them either. The seams you've drawn should make those likely changes possible without restructuring.

**Progressiveness is mandatory.**
Every new feature must leave the system easier to iterate, not harder. The next developer building a similar feature should find their job easier than you found yours.
