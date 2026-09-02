# Campaign lifecycle and recommendation

Status: active
Document type: feature
Owner: campaign application boundary
Canonical scope: feature.campaign-lifecycle
Read when: changing automatic campaign execution, campaign recovery or best-fit recommendation semantics

## Outcome

A reviewed `Find best setup` plan can be launched as one bounded Campaign. A Campaign groups immutable Runs; it never replaces Run identity and it never owns model loading or serving-runtime lifecycle.

## Launch invariant

The browser sends the planning choices plus the exact reviewed `plan_digest`. Performance Lab recomputes the plan at launch. If the digest changed, launch is rejected and the user must review the new plan.

Each campaign matrix entry maps to one candidate and one frozen run configuration. The canonical native runner executes the selected versioned benchmark suite and publishes the resulting Run through the existing immutable Run store.

## Lifecycle

Campaign state is persisted separately from Run evidence and is explicitly one of queued, running, cancelling, succeeded, failed, cancelled or interrupted. Progress is reconnectable by campaign ID. Manual evaluation and Campaign execution share one bounded local evaluation-capacity owner, so they cannot execute concurrently.

Cancellation stops the active run and prevents queued campaign entries from starting. Process shutdown/restart marks unfinished Campaign/entries as interrupted; retained partial state never masquerades as completed benchmark evidence.

## Results and decision policy

Campaign results join the persisted Campaign with immutable completed Runs. Compatibility is established per quality/capability, runtime and resource dimension before conclusions are surfaced. Missing runtime/resource measurements remain unavailable rather than becoming zero.

The initial versioned decision policy is `strict-quality-dominance@1.0.0`. It recommends a candidate only when comparable quality evidence shows that candidate is no worse on every reported quality metric and strictly better on at least one metric against every alternative. It uses no hidden metric weights, normalization or universal score.

If no candidate strictly dominates every alternative, the product reports that there is no single recommended winner and leaves the separate evidence trade-offs inspectable. Performance and resource evidence stay separate and are not used as undocumented tie-breakers.

Campaign Results can also enumerate retained benchmark case identities and hand one exact task/sample identity to the [same-case candidate comparison](same-case-candidate-comparison.md) read path. That drill-down reuses immutable Run/sample evidence and canonical capability compatibility; it does not alter Campaign recommendation semantics.
