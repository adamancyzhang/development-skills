# Reference C: Deleting Features — Contracting Architecture

Deletion is not the inverse of addition. Adding code creates new dependencies. Deleting code breaks existing dependencies, leaves gaps in abstraction layers, and orphans utilities that were shared across features. Deletion without architectural assessment is amputation without understanding the circulatory system.

## The Deletion Protocol

**Step 1 — Map all dependents.**
Before deleting anything, trace every incoming dependency on the code you plan to remove. Use static analysis, grep, and the test suite. Ask:
- What imports from this module?
- What calls this function?
- What relies on this return type or exception?
- What configuration references this feature?
- What documentation describes this behavior?
- What external systems (APIs, databases, message queues) interact with this code?

If you cannot confidently enumerate every dependent, do not delete.

**Step 2 — Identify the abstraction role.**
What role does this code play in the architecture?
- **Leaf node:** nothing depends on it. Safest to delete.
- **Implementation behind an interface:** other code depends on the interface, not this code. Delete the implementation, keep or remove the interface based on whether it still serves a purpose.
- **Shared dependency:** multiple modules depend on this code. Deletion requires providing an alternative or verifying all dependents are also being removed.
- **Architectural load-bearing wall:** this module is the stable dependency that others organize around. Deletion means architectural restructuring of its dependents.

**Step 3 — Check for abstraction gaps.**
If you delete an implementation behind an interface, verify: does that interface still have at least one implementation? An interface with zero implementations is dead code. If the interface is no longer needed, delete it too.

If you delete the only implementation of a shared abstraction, and other code still depends on that abstraction, you must either provide a replacement or remove the abstraction and all its dependents. A missing implementation is a runtime failure waiting to happen.

**Step 4 — Trace configuration and infrastructure.**
Deletion of a feature often leaves behind:
- Environment variables and configuration keys that are now unused
- Database tables, columns, or migrations that are now orphaned
- API endpoints that return errors or empty results
- Scheduled jobs or event handlers that still fire
- Feature flags that gate nothing
- Documentation that describes deleted behavior

Each of these is a hidden dependency. The code is gone but the system still acts as if it exists.

**Step 5 — Verify no orphaned utilities.**
Code that was shared between the deleted feature and remaining features may become:
- **Truly dead:** no remaining callers. Delete it.
- **Now single-use:** the only remaining caller is another module. Move it into that module — shared code with one consumer is not shared.
- **Still shared:** other features genuinely depend on it. Keep it, but verify its location still makes sense.

**Step 6 — Assess architectural simplification.**
Deletion should make the architecture simpler, not just smaller. After deletion:
- Are there fewer modules? Fewer interfaces? Fewer dependencies?
- Is the dependency graph simpler or more fragmented?
- Can any abstraction layers be collapsed now that a use case is gone?
- Does the remaining system still tell a coherent story?

If the system is smaller but more confusing, the deletion was surgical rather than architectural. Go back and clean up the structural remnants.

**Step 7 — Run the full test suite.**
Deletion tests nothing directly (you removed the code that would be tested), but it can break tests that indirectly relied on the deleted code. Run every test. Investigate every failure. A passing test that should have failed (because it depended on deleted behavior) is a test that was never valid.

## Deletion Checklist

- [ ] All incoming dependencies on the deleted code are mapped and resolved
- [ ] The abstraction role of the deleted code is identified (leaf, implementation, shared, load-bearing)
- [ ] No interfaces left with zero implementations (unless also deleted)
- [ ] Configuration, database, API, and documentation references are cleaned up
- [ ] Orphaned utilities are deleted, moved, or confirmed as still shared
- [ ] Remaining architecture is simpler, not just smaller
- [ ] Full test suite passes with no tests relying on deleted behavior
- [ ] The system's conceptual integrity is improved, not fractured
