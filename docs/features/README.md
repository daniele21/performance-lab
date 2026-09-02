# Feature documentation

Use this directory only for durable shipped behavior that needs explanation beyond code/tests and the architecture/evidence references.

Rules:

- one feature document owns one stable user/system behavior;
- describe current behavior, invariants, states and externally meaningful contracts rather than implementation progress;
- link to the canonical owner instead of copying architecture, evidence or design-system truth;
- active implementation plans belong in `../workstreams/`, not here;
- completed workstream history belongs in Git history, not feature docs;
- update a feature document in the same change when the shipped behavior it describes changes;
- create a new feature document only when durable non-obvious behavior is not sufficiently discoverable from code, public contracts, tests, architecture or focused operational references;
- delete a feature document when it no longer has an independent durable purpose.

Current operational references at `docs/` root remain canonical for CLI/config/evidence topics until a feature-specific split is justified.
