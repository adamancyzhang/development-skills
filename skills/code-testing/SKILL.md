---
name: code-testing
description: "The internal philosophy (内功心法) of software testing — why a test exists, what makes one trustworthy, what to verify, and how to keep a suite alive. Consult it whenever you write, review, judge, or plan tests, or decide whether code is even testable. This is the philosophy of testing; pair it with test-driven-development for the test-first ritual. Use it for any 'how should I test this', 'is this a good test', 'what should I assert', or 'why is this so hard to test' question — even when the word 'test' is never spoken."
version: 1.0.0
author: Adamancy Zhang
license: MIT
---

# Code Testing — The Internal Discipline (内功心法)

## Overview

A test exists to convert a belief into evidence. "It works" is a hope until something independent of you can fail the moment it stops working. Untested code is not working code — it is a hypothesis wearing the costume of a fact.

And a test answers a sharper question than people assume. Not "what does this code do?" — the code answers that tautologically. A test answers "what *should* this code do?" That distinction is the entire discipline: the expectation must be decided and fixed *before* the implementation exists to bias it, or the test will quietly agree with whatever the code happens to do, bugs and all.

This skill is the philosophy — the *why* and the *what*. It prescribes no ritual. For the disciplined practice that enacts it — writing the test first, watching red turn green, governing the suite over time — see the `test-driven-development` skill. Philosophy without practice is talk; practice without philosophy is ritual. Hold both.

These principles carry no language, framework, or worked example on purpose. They are meant to hold on the first project and the thousandth.

## The Iron Law

```
A TEST EARNS TRUST ONLY BY FAILING WHEN THE BEHAVIOR BREAKS
```

A test that cannot fail protects nothing. A test you have never watched fail has never shown that it *can*. And a test that fails for reasons other than broken behavior — a renamed symbol, a reshuffled internal — is failing at the wrong thing. Trust is never granted by a green result; it is earned by a red one, at the right moment, for the right reason.

## 1. Trust is the whole game

A test you cannot trust is worse than no test at all. No test is honest ignorance — you know that you do not know. An untrustworthy test is false confidence — it tells you that you are safe and stops you from looking. The most dangerous test in any suite is the one that stays green while the system burns.

Three habits keep trust intact:

- **Watch it fail before you trust it to pass.** A green you never saw turn red proves nothing — it may be testing the wrong thing, asserting nothing, or never reaching the code at all. The failure is the only evidence that the test is wired to the behavior. See it fail for the expected reason; only then does its passing carry meaning.
- **Distrust the test that has never failed.** A test that has been green its whole life has never demonstrated that it can catch anything. It is a smoke detector no one has ever held a flame to.
- **Let errors surface.** A test that defensively swallows the unexpected silences the very alarm it exists to raise. An error reaching the surface is signal, not noise. Catch one only to assert that it was the *right* error, raised for the *right* reason.

## 2. Verify behavior, not structure

Assert on what an outside observer can see: returned results, changes to observable state, effects on the world, errors raised. Never assert on internal mechanics — how many times something was called, which private step ran, what an intermediate value was that no observer outside the code could ever witness.

The litmus is simple: change the implementation without changing the behavior. If the test breaks, it was bound to the wrong thing. A test tied to structure shatters the instant someone improves the code — so it punishes improvement and teaches the team to stop refactoring. A test tied to behavior survives every rewrite that keeps the promise and fails the moment a promise is broken. That is exactly the test worth having.

## 3. Exercise the real thing

A test that runs a *copy* of the logic verifies the copy, not the system. The copy and the original drift apart silently; the test stays green while the real code rots. A passing test of a duplicated truth is worse than no test — it certifies a ghost.

Every substitute for a real dependency — every double, stub, or fake — is a deliberate lie inserted into the test. A lie can be justified, but it must *be* justified, out loud:

- Substitute only at the **outermost boundary**, where the real thing is genuinely slow, costly, or nondeterministic — never an internal collaborator you simply find inconvenient.
- Substitute only when a **contract** is the real thing under test: "given this input, expect a response of this shape." The contract is what you verify; the substitute stands in for everything beyond it.
- The justification must name **what still covers the truth elsewhere** — the wider test, the real exercise, the external guarantee. If you cannot name it, you have not isolated a boundary; you have hidden a gap.

No justification, no substitute. An unjustified stand-in is a hole in the evidence that you can no longer see.

## 4. Push to the limits — the happy path is the smallest truth

The middle of the input space is where code is easy and bugs are rare. Verification lives at the edges. Before trusting any behavior, deduce it at its limits across four dimensions:

- **Scale** — the absent, the empty, the zero, the single; and the opposite extreme, the maximum, the overflow, the flood.
- **Time and concurrency** — what waits, what arrives out of order, what happens twice at once, what never arrives at all.
- **State and structure** — the forbidden transition, the out-of-order step, the operation invoked when the system is in a state that should make it impossible.
- **Resources and capacity** — what happens as memory, connections, or capacity run dry, and whether the system degrades gracefully or shatters.

For every behavior, ask: what is the smallest case, the largest, the absent, the simultaneous, the forbidden? Each is a truth the happy path will never reveal — and each is where real systems actually fail.

## 5. A hard test is a design diagnosis

When a test is painful to write, the pain is not a property of testing — it is the design confessing a flaw. The instinct to answer it with more doubles, deeper stubs, and heavier setup is the wrong instinct: it muffles the confession instead of acting on it.

| The pain | What it confesses |
| --- | --- |
| You don't know how to test it | the interface is unclear |
| The test grows enormous | the unit is doing too much |
| You must fake everything to reach it | the code is too tightly coupled |
| The setup dwarfs the assertion | an abstraction is missing |

The cure is always to change the design — decompose the responsibility, expose a seam, invert a dependency until the real thing can be reached directly — never to bend the test around the flaw. Beneath this sits a chain that holds at every scale: if you cannot test it, you cannot trust it; if you cannot trust it, you cannot change it. Testability is the design telling you, in advance, whether it is still alive or already fossilized.

## 6. Discipline of the suite

Individual tests can each be sound and the suite still rot. Four disciplines keep it honest:

- **Each test stands alone.** A test whose outcome depends on what ran before it is not a verification — it is a coincidence, a lie waiting for the day the order changes. Each test raises its own world and razes it afterward; nothing mutable crosses the boundary between tests.
- **Match the net to the catch.** Not every change needs the whole suite, but misjudging the radius is how regressions slip through. The blast radius of a change sets the scope of verification: touch a shared foundation, verify broadly; touch one isolated internal, verify locally; cross a boundary, verify the boundary itself. When the radius is unclear, widen the net — minutes of over-verifying are always cheaper than one regression in production.
- **Coverage is a map, not the territory.** Coverage records which lines executed, not whether anything was checked — a line can be fully covered by a test that asserts nothing. High coverage over weak assertions is confidence with no foundation. Aim at verified behavior and let coverage follow as its shadow. Never aim at the shadow.
- **The goal defines done.** "Make it work" cannot be verified; "reproduce the failure, then make it pass" can. Turn every task into a verifiable goal before writing code, and the test becomes the executable definition of done. A fault declared fixed without a test that first reproduced it has not been shown to be fixed at all.

## 7. Tests are a living asset — curate, don't hoard

A test suite is not a write-once archive; it is a garden that rots when untended. Left ungoverned, tests silt up into a graveyard — one-off experiments, explorations abandoned half-finished, tests that passed once and were never read again. First the team stops trusting the suite, then stops running it, then stops writing tests at all.

The cure is curation, and it begins with a single distinction:

- A **permanent behavioral lock** guards an invariant whose loss would matter. It earns its place by declaring what behavior it protects and why that behavior is critical.
- A **temporary scaffold** supports active construction and has not yet proven lasting worth. It is retired on a clock — when the work stabilizes or its window closes — not kept forever out of sentiment.

Every test that survives must answer one question: *what behavior do I protect, and would its loss matter?* A test that cannot answer is not an asset; it is clutter that makes the real signals harder to hear. A curated suite is a library. An uncurated one is a junk drawer.

## Failure modes

Each of these is a way trust quietly dies:

- The test that has never once failed — a detector never met with smoke.
- The test bound to call counts and private steps, that shatters the moment someone renames a symbol.
- The test that exercises a copied paragraph of logic and certifies a ghost.
- The substitute with no recorded justification — a lie on the record with no one to vouch for it.
- The suite that has never met an empty input, a maximum, or a forbidden transition.
- The test that passes only because its neighbor happened to run first.
- Coverage worshipped as a number while the assertions verify nothing.
- The graveyard suite, so untrusted that a green run means nothing to anyone.
- The "fixed" fault with no test that ever reproduced it.

## Final Rule

```
A test unseen to fail              → not yet a test
A test bound to structure          → a brake on change
A substitute with no justification → a lie on the record
A suite no one curates             → a graveyard
Behavior verified at its limits    → the only real green
```
