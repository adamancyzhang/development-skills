# Reference A: New Feature Development — Designing Architecture

When building something new, you are creating the foundation that future changes will build upon. Your primary obligation is to establish clear boundaries, clean interfaces, and a coherent conceptual model.

## The New Feature Architecture Protocol

**Step 1 — Define the domain before the software.**
What concepts exist in the problem space? What are their relationships? The code will model these concepts. If the domain model is wrong, no amount of clean code will fix it. Name the concepts. Draw their relationships. Verify with a domain expert if available.

**Step 2 — Identify the seams.**
Where do different rates of change exist in this domain? Which concepts will evolve independently? These are your module boundaries. A seam is not where the framework suggests a split — it is where the domain naturally separates concerns that change for different reasons.

**Step 3 — Design interfaces from the caller's perspective.**
For each module boundary, define the interface that callers will use. Ask: "If I were writing code that needs this capability, what would I want the call to look like?" The interface exists to serve callers, not to expose the implementation.

**Step 4 — Establish dependency direction.**
Map the dependencies between your new modules. Every arrow should point from higher-volatility toward lower-volatility. If two arrows point at each other, redraw the boundary. If a low-volatility module depends on a high-volatility one, invert through an interface.

**Step 5 — Verify against existing architecture.**
Does this new feature fit within the existing architectural patterns? If it introduces a new pattern, is that pattern explicitly chosen as an architectural evolution, or is it an accidental divergence? Accidental divergence is how a system accumulates multiple personalities.

**Step 6 — Design the evolution path.**
Ask: "After this feature ships, what are the three most likely follow-up requests?" Your design should not build for those requests, but it should not block them either. The seams you've drawn should make those likely changes possible without restructuring.

**Step 7 — Write the test from the outside.**
Before implementing, write a test that exercises the new feature through its public interface at the highest appropriate level. This test is your first caller — it validates that the interface is usable. If writing this test is painful, the interface needs redesign before implementation begins.

**Step 8 — Implement behind the interface.**
With the interface defined and validated, implement the internals. The implementation can be messy initially — the interface protects the rest of the system from that mess. Refactor the internals before merging, but ship the interface first.

## New Feature Checklist

- [ ] Domain concepts are clearly named and modeled
- [ ] Module boundaries follow domain seams, not framework conventions
- [ ] Interfaces are designed from the caller's perspective
- [ ] Dependency arrows point toward stability
- [ ] The feature fits within (or explicitly evolves) the existing architectural patterns
- [ ] Likely follow-up features are possible without restructuring
- [ ] At least one test exercises the public interface before implementation
- [ ] The new code adds new capabilities without modifying existing module boundaries
