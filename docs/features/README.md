# Feature documentation

Use this directory only for durable shipped behavior that needs explanation beyond code/tests and the architecture/evidence references.

Rules:

- one feature document owns one stable user/system behavior;
- describe current behavior, invariants, states and externally meaningful contracts rather than implementation progress;
- link to the canonical owner instead of copying architecture, evidence or design-system truth;
- active implementation plans belong in `../workstreams/`, not here;
- completed workstream history belongs in Git history, not feature docs;
- update or delete a feature document when shipped behavior changes or the document no longer has an independent purpose.

Current operational references at `docs/` root remain canonical for CLI/config/evidence topics until a feature-specific split is justified.
