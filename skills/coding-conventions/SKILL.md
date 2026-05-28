---
name: coding-conventions
description: "Coding conventions for high-availability code: design pattern awareness, boundary-first validation, trusted internal logic, unified exception handling. Use when writing or reviewing any production code."
version: 2.0.0
author: Adamancy Zhang
license: MIT
---

# Coding Conventions

## Core Principle

```
BOUNDARIES VALIDATE, INTERNALS TRUST
```

Every value is either validated or trusted. There is no middle ground.

At system boundaries — protocol boundaries, user input, external service responses — every value must be validated before it enters the system. Once validated, that value is trusted throughout the internal execution path. Internal modules must not re-validate what the boundary has already certified.

If you find yourself checking for null inside a module that received its input from a trusted caller, either the boundary failed to validate, or you do not trust your own architecture. Both are defects — one in the code, one in the design.

## The Boundary Concept

A boundary is where untrusted input meets trusted execution. It is the gate through which external data enters the system.

**Boundaries exist at every level of abstraction:**
- **System boundary**: API endpoints, message consumers, scheduled jobs reading external sources
- **Module boundary**: Class constructors, public methods, function entry points
- **Method boundary**: The point where raw input is processed into validated context

**What is NOT a boundary:**
- A service calling another service within the same process
- A module importing from another module
- A function calling another function

Internal calls are trusted. They operate on data that has already been validated. Re-validating at every internal call site is not resilience — it is distrust in your own architecture.

## How to Identify Boundaries

Ask three questions:

1. **Where does external input enter?** — Any place where data crosses from outside your control to inside your control is a boundary.

2. **Where do trust levels change?** — When data moves from "might be wrong" to "must be right," that's a boundary.

3. **Where do abstraction layers meet?** — The interface between different levels of abstraction is a boundary.

## Boundary Validation

At the boundary, every value must be validated before it enters the system:
- Presence: does the required value exist?
- Type: is it the expected type?
- Range: does it fall within acceptable bounds?
- Format: does it conform to the expected structure?
- Consistency: do related values agree with each other?

Once validated, the value is wrapped in a type that guarantees its validity. Internal code operates on these guaranteed types, not on raw input.

## Trusted Internal Logic

Internal modules make decisions based on trusted data. They do not check for null, undefined, or invalid values that the boundary has already rejected.

**The discipline:** if a value could be null inside a trusted module, the boundary failed to validate it. Fix the boundary, not the module.

## Exception Handling

Exception handling is not a convenience feature. It is the mechanism that determines whether a system fails honestly or fails silently.

### Unified Exception Handling

All exceptions must be handled at the interaction boundary, not scattered throughout the internal execution path.

**The principle:** the interaction boundary — API endpoint, message consumer, scheduled job entry — is the single point where all exceptions are caught, classified, and converted into the protocol's error format. Internal code throws. The boundary catches.

**Classification at the boundary:**
- **System exceptions:** infrastructure failures, resource exhaustion, unexpected state. Logged with full context, converted to generic error responses.
- **Business exceptions:** domain rule violations, validation failures, authorization denials. Converted to specific error responses that the caller can act on.
- **Unknown exceptions:** anything not classified above. Treated as system exceptions with additional alerting.

### Error Premises

Every catch block must answer a critical question: after this catch, is the subsequent execution building on a true premise or a false one?

**The false premise problem:** an operation fails, the exception is caught, and execution continues. But the state has been corrupted. The code continues, operating on the assumption that the operation succeeded. Downstream logic produces results that are logically correct but factually wrong.

**The rule:** if catching an exception leaves the system in a state where subsequent operations would act on incorrect assumptions, the exception must propagate.

## Design Patterns

### Pattern Awareness

The 23 standard object-oriented design patterns exist to solve recurring structural problems. Knowing them is not optional — it is the vocabulary of software design.

**The obligation:** before inventing a structure, ask whether an existing pattern already solves the problem. If it does, use it. If it doesn't, understand why before inventing something new.

### Pattern Application Principles

**Fit the pattern to the problem, not the problem to the pattern.** A pattern applied where it doesn't belong creates accidental complexity.

**Patterns are structural vocabulary, not goals.** The codebase does not become better by using more patterns. It becomes better by using the right pattern for each problem — including no pattern when simplicity suffices.

## Simplicity and Forward Thinking

### No Over-Design

Build only what the current requirement demands. Every abstraction you add for a hypothetical future carries a maintenance cost that compounds daily.

**The test:** can you justify this structure with a requirement that exists today? If not, it is speculation.

### Forward Thinking Without Forward Building

You must think about how the system will evolve. You must not build for that evolution prematurely.

**The discipline:**
- Understand the likely directions of change
- Design your boundaries so those changes are possible without restructuring
- Do not implement the changes themselves
- Do not add abstractions that serve only hypothetical use cases

Forward thinking means your design does not block the future. It does not mean your code implements the future.

## Verification

Before approving any code, verify:

1. All external input is validated at the boundary before entering the system
2. Internal modules operate on trusted data without redundant checks
3. Every catch block has a clear purpose: re-throw, rollback, or convert to error response
4. Unified exception handling exists at the interaction boundary
5. No execution continues on a corrupted or uncertain premise
6. Design patterns are applied to solve existing problems, not hypothetical ones
7. Forward thinking informs boundary design, not premature implementation
