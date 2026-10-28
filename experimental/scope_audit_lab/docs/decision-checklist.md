# Scope Audit Lab: pre-implementation decision checklist

Status: Draft for review; no design decisions approved by this checklist. The [evidence contract 0.1](evidence-contract.md) is a proposal beneath [requirements 0.2](../requirements/scope-audit-lab-0.2.md), and this checklist does not change either document.

Use this checklist to distinguish a recommendation from an authorized choice and a design approval from demonstrated implementation behavior. All items initially began OPEN; the owner has since prioritized mathematics/physics assessment, deferred voice work, and approved an independent start. E-01 is APPROVED, W-01 through W-03 are DEFERRED, and the remaining design choices stay OPEN.

## How to record a decision

For each item, record `ID`, `status`, `chosen option or exact decision`, `rationale`, `scope`, `decision maker`, `approval reference`, and `affected tests`. Use `OPEN`, `APPROVED`, `DEFERRED`, or `REJECTED`; a deferred item also needs a reason and a revisit trigger.

Approval references can identify a project-owner message or reviewed repository artifact; a contributor's draft or commit alone does not establish owner approval. Corrections retain the previous decision and explain what supersedes it.

Approving an item permits only the work within its stated scope. Do not implement a recommended default merely because nobody objected, and do not treat design approval as a passed acceptance test.

## Evidence gate

This gate concerns the common evidence model before Stage A schemas and storage behavior. Later domain-specific choices can stay open when they do not affect that common contract.

| ID / status | Decision required | Recommended starting choice | Check before approval |
|---|---|---|---|
| E-01 / APPROVED | What baseline is being adapted? | Proceed independently; Prototype 0.1 compatibility is UNKNOWN. No baseline modules or interfaces are assumed inherited. | Owner approval is recorded below; no compatibility test or implementation result is implied. |
| E-02 / OPEN | Which types, IDs, and reference rules are required? | Typed records, ledger-scoped opaque IDs, explicit unresolved references, and no identity inferred from repeated wording. | Same wording/different sources, missing targets, duplicate-ID conflicts, and wrong target types have defined outcomes. |
| E-03 / OPEN | How are values and missingness represented? | Separate present, missing, invalid, and not-applicable states; measured zero remains present. | Define absent fields, nulls, raw invalid values, and legacy sentinel handling without silent coercion. |
| E-04 / OPEN | What storage, correction, and privacy policy is acceptable? | Standard-library SQLite is a candidate, not a selection; require transactional logical appends and linked corrections whichever backend is chosen. | Resolve concurrent writes, conflicting successors, consent-sensitive material, and deletion/tombstone policy without promising tamper-proof retention. |

### E-01 approval record

- **Status:** APPROVED.
- **Exact decision:** “Proceed independently; mark Prototype 0.1 compatibility unknown”.
- **Decision maker:** project owner.
- **Approval reference:** the project-owner reply to the baseline decision question in the study-aperture planning conversation, quoted above.
- **Rationale:** the owner selected independent development rather than waiting for Prototype 0.1 inspection.
- **Scope:** remove Prototype 0.1 inspection as a prerequisite for independent work; do not claim inherited modules, interface compatibility, migration support, or baseline validation.
- **Compatibility state:** UNKNOWN, not compatible and not incompatible. Revisit only after obtaining an identified prototype state and performing explicitly scoped comparisons.
- **Affected tests:** future baseline compatibility tests are not available or run; planned requirements-conformance tests remain NOT RUN and cannot establish prototype compatibility by themselves.
- **Supersedes:** E-01's previous OPEN state; the original specification's baseline wording is retained unchanged as historical requirements context.

This approval does not choose the other evidence-contract proposals or approve an executor, storage backend, numerical method, or live voice capability.

## Verification gate

Review this gate before implementing verification bindings or any executor. A recorder-only milestone does not require permission to run arbitrary audited code.

| ID / status | Decision required | Recommended starting choice | Check before approval |
|---|---|---|---|
| V-01 / OPEN | What exactly does a verification result cover? | Bind subject, examined state, property, procedure, criteria version, and declared dependencies. | Old pass/new state, unknown version, and incomplete dependency information cannot silently inherit a pass. |
| V-02 / OPEN | How are results and later applicability expressed? | Per-criterion met/not-met/indeterminate/not-evaluated outcomes, separate from structure, execution, support, and later applicability. | Define when missing evidence makes a result indeterminate rather than not-met; retain conflicting examination results. |
| V-03 / OPEN | Will the first milestone record checks or execute them? | Recorder-only initially; any later executor requires separate scoped authorization. | Decide command/input boundaries, working directories, side effects, timeouts, output capture, network restrictions, and secret handling before enabling execution. |

## Numerical gate

Review this gate before Stage B calculations and transition probing. Approving an evidence schema does not settle numerical conventions implicitly.

| ID / status | Decision required | Recommended starting choice | Check before approval |
|---|---|---|---|
| N-01 / OPEN | Which numeric representation and compatibility rules apply? | Explicit representation/rounding; exact quantity and unit matching initially; unsupported conversions remain unavailable. | Decide non-finite input handling, tolerance domains, and whether conversion rules are needed at all. |
| N-02 / OPEN | How are residuals and uncertainties calculated? | Observed-minus-predicted residual; explicitly named relative/normalization denominators; no default covariance or independence assumption. | Define zero denominators, missing uncertainty, uncertainty type, and covariance absence; retain valid residuals even when uncertainty is unavailable. |
| N-03 / OPEN | What does a transition criterion mean? | Preserve supplied order, compare adjacent cases, declare threshold inclusivity and quantity, and emit candidate regions only. | Define below/at/above behavior, irregular spacing, zero, missing intermediate cases, and several changing conditions. |

## Voice gate

This gate is deferred by the project owner in [S-02](math-physics-focus.md#recorded-scope-decision), to prioritize mathematics/physics evidence and assessment. The revisit trigger is an explicit owner request to resume voice work, not completion of another milestone. No voice schema/classification or live instrumentation work is in the current scope.

| ID / status | Decision required | Recommended starting choice | Check before approval |
|---|---|---|---|
| W-01 / DEFERRED | What events are observable for each trial? | Explicit capability records; unavailable endpoint decisions remain unknown. | Identify audio/event access, system/mode/version, timestamp sources, and what cannot be observed. |
| W-02 / DEFERRED | What establishes completion and premature response? | Attributed completion annotation plus comparable response timing; ambiguous timing yields indeterminate classification. | Define clock alignment, annotation reliability, timing uncertainty, backchannels, and instruction-compliance criteria. |
| W-03 / DEFERRED | How are disruption, recovery, consent, and retention handled? | Record attributed reports/measurements separately; never infer recovery cost from interruption alone. | Define measurement procedure, consent, allowed sharing, retention, and redaction before collecting real participant material. |

## Integration gate

Review these choices before building reporting/export behavior, and execute the mapped tests before any conformance claim. A decision to adopt a test plan is not evidence that the tests ran.

| ID / status | Decision required | Recommended starting choice | Check before approval |
|---|---|---|---|
| I-01 / OPEN | What evidence must accompany an implementation claim? | Requirement-linked test executions with examined versions, criteria, inspectable artifacts, failures, and limitations. | Include adversarial cases at every stage; documentation checks cannot stand in for runtime tests. |
| I-02 / OPEN | How will lab evidence enter study-aperture? | Explicit JSON exchange with retained IDs, schemas, states, methods, sources, and limitations; assessor review before any claim-grade or decision change. | Unknown schema handling, round-trip missingness, and no automatic pass-to-support or pass-to-resolution promotion. |
| I-03 / OPEN | How will research claims and reports preserve uncertainty? | Source-reported claims remain unverified until examined; keep observations, calculations, criteria, gaps, questions, interpretations, and limits separate. | Cross-benchmark comparisons and product identity need evidence; voice generalizations must retain their tested scope. |

## Smallest next approval request

E-01 is resolved for an independent start. The recommended next review is **E-02 through E-04**, plus **V-01 through V-03** for a recorder-only Stage A slice. Also settle I-01's required execution evidence and I-02's exchange envelope before making implementation claims or exposing an interchange interface.

Voice gates are deferred under S-02. Numerical conventions remain OPEN and are active review priorities for the mathematics/physics focus: N-01 and N-02 must be settled before implementing calculations, and N-03 before transition probing. No approval is being requested for a live voice collector, network-dependent runtime, benchmark ranking, or automatic causal diagnosis.

### Decision-entry template

```text
ID:
Status: OPEN
Chosen option / exact decision: Not selected
Rationale: Not recorded
Scope / permitted work: Not authorized
Decision maker: Not recorded
Approval reference: Not recorded
Affected tests:
Deferral reason and revisit trigger, if applicable:
Supersedes, if applicable:
```

## Review completion

A gate is ready only when its blocking choices are explicitly approved, or the relevant work is excluded through an explicit deferral with dependencies recorded. Partial approval remains partial; it must not be reported as approval of the whole contract.

After implementation, report design decisions, software conformance results, and empirical findings as three distinct things. Neither completing this checklist nor passing future software tests establishes that all audited claims, models, or voice interactions are correct.
