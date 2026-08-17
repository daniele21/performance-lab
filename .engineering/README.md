# Engineering command contract

`commands.json` is the canonical repo-template-sw operating command map for the mixed Python + browser product.

Use the native Python/npm commands declared there rather than inventing parallel wrappers. `frontend/package-lock.json` is the dependency-resolution source for browser setup and `requirements/ci-constraints.txt` remains the constrained Python CI source.

`REL-UI-001` owns the later built-product lifecycle work such as final build identity, packaging, smoke ownership and artifact promotion. `UIF-001` establishes deterministic frontend setup/check/test/build gates without claiming that release packaging is complete.
