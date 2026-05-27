# Reference C: Deleting Features

Deletion is not the inverse of addition. Adding code creates new dependencies. Deleting code breaks existing dependencies, leaves gaps in abstraction layers, and orphans utilities that were shared across features. Deletion without architectural assessment is amputation without understanding the circulatory system.

## Core Principles

**Map all dependents before deletion.**
Before deleting anything, trace every incoming dependency on the code you plan to remove. What imports from this module? What calls this function? What relies on this return type or exception? What configuration references this feature? If you cannot confidently enumerate every dependent, do not delete.

**Identify the abstraction role.**
What role does this code play in the architecture?
- **Leaf node:** nothing depends on it. Safest to delete.
- **Implementation behind an interface:** other code depends on the interface, not this code. Delete the implementation, keep or remove the interface based on whether it still serves a purpose.
- **Shared dependency:** multiple modules depend on this code. Deletion requires providing an alternative or verifying all dependents are also being removed.
- **Architectural load-bearing wall:** this module is the stable dependency that others organize around. Deletion means architectural restructuring of its dependents.

**Check for abstraction gaps.**
If you delete an implementation behind an interface, verify: does that interface still have at least one implementation? An interface with zero implementations is dead code. If the interface is no longer needed, delete it too. A missing implementation is a runtime failure waiting to happen.

**Trace configuration and infrastructure.**
Deletion of a feature often leaves behind: environment variables, database tables or columns, API endpoints, scheduled jobs, feature flags, documentation. Each of these is a hidden dependency. The code is gone but the system still acts as if it exists.

**Verify no orphaned utilities.**
Code that was shared between the deleted feature and remaining features may become truly dead (delete it), now single-use (move it into the remaining caller), or still shared (keep it, verify its location still makes sense).

**Simplify, don't just shrink.**
Deletion should make the architecture simpler, not just smaller. After deletion: are there fewer modules? Fewer interfaces? Fewer dependencies? Is the dependency graph simpler or more fragmented? Can any abstraction layers be collapsed now that a use case is gone? If the system is smaller but more confusing, the deletion was surgical rather than architectural.

**Progressiveness is mandatory.**
Deletion of a feature should leave the architecture cleaner, not wounded. The remaining system should still tell a coherent story.
