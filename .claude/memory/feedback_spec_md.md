---
name: SPEC.md as living reference
description: How to treat SPEC.md — useful first reference but not a rigid contract
type: feedback
---

Treat SPEC.md as a strong first reference for the project (architecture, dependencies, platform notes, etc.), but not as an immutable contract. Avoid changing it unnecessarily, but it can be updated when the design genuinely evolves.

**Why:** The spec reflects early design decisions that may shift as implementation progresses. It should guide, not constrain.

**How to apply:** Consult SPEC.md first when starting any task. Flag when implementation diverges from it rather than silently working around it. Propose spec updates only when there's a real, confirmed design change — not as a first reaction to friction.