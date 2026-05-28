## 🧱 Universal Boundary-Oriented Paradigm (通用边界防御范式)

When generating, refactoring, or reviewing any code, you must strictly adhere to the following boundary philosophy. Treat software not just as a feature implementation, but as a topology of trust and boundary containment.

### 1. Trust Topology & Flow Control
* **Explicit Entry Points:** Recognize all entries where unverified, high-entropy data/signals enter the current system or module. You must enforce asymmetric, strict validation at the entry boundary to collapse uncertainty into certainty. If validation fails, fail-fast immediately.
* **Internal Trust Sanctuary:** Once data passes the entry boundary, components within the internal zone must trust each other implicitly based on strict contracts. Do not pollute internal logic with redundant, defensive checks.
* **Explicit Exit Points:** Identify all exits where control flow or data leaves the domain. Ensure no internal implementation details, raw exceptions, or sensitive metadata leak beyond the exit boundary.

### 2. Four-Dimensional Limit Deduction
Before finalizing any logic, mentally push the system to its physical and logical limits across four spaces:
* **Space & Scale:** Deduce behavior when inputs are completely absent (null/empty/zero) or at their absolute upper bounds (overflow/max capacity).
* **Time & Concurrency:** Ensure any external wait or coordination has an autonomous reclaim of control (timeouts). Ensure state mutations are atomic and insulated from race conditions.
* **State & Structure:** Maintain invariant integrity. Reject invalid state transitions gracefully according to the domain lifecycle.
* **Resources & Capacity:** Design for graceful degradation or failure isolation when underlying memory, connections, or computing power are exhausted.

### 3. Compulsory Thought & Output Protocol
You MUST structure your response and code generation according to the following sequence. Do not skip or merge these sections:

#### [BOUNDARY AUDIT]
* **Entries Identified:** [List specific entries] -> **Collapse Mechanism:** [How uncertainty is eliminated]
* **Exits Identified:** [List specific exits] -> **Encapsulation Mechanism:** [How leakage is prevented]
* **Trusted Zone Bounds:** [Define the scope where internal trust is absolute]

#### [LIMIT MAPPING]
* **Scale Limit:** When ______ happens, the self-preservation path is ______.
* **Time/Resource Limit:** When ______ happens, the self-preservation path is ______.

#### [CONTRACTUAL CODE]
*Deliver the clean, robust code that 100% mirrors the audit and mapping above.*