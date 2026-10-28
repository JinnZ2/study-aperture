# Scope Audit Lab: proposed evidence contract 0.1

Status: Draft proposal for review; not implemented, adopted as a stable interface, or validated. This document proposes interpretations and design choices beneath [requirements specification 0.2](../requirements/scope-audit-lab-0.2.md); it does not amend that specification or establish compatibility with the uninspected Prototype 0.1.

The contract describes what a future implementation would record and what it would refuse to infer. “Require,” “reject,” and “must” below describe proposed behavior to implement and test, not capabilities already present in this repository.

The subsequent [scope decision](math-physics-focus.md) prioritizes mathematics/physics evidence and assessment, with voice work deferred. The voice provisions remain a future proposal rather than an active milestone dependency; no other design choice in this contract is approved solely by that prioritization.

The later [E-01 approval](decision-checklist.md#e-01-approval-record) authorizes an independent start with Prototype 0.1 compatibility UNKNOWN. It does not establish compatibility or adopt this contract's remaining implementation choices.

[Draft mathematical evidence schemas](../schemas/draft-0.1/README.md) make five proposed record shapes concrete for review. They do not by themselves close design gates or provide a runtime validator, proof checker, or empirical assessment engine.

## Contract boundary

The instrument records evidence and explicitly specified calculations. It may establish that a declared criterion was met for an identified subject state, but it does not thereby establish general correctness, causality, truth, or suitability for an action.

- **Record validity:** conformance to a particular schema and its validation rules.
- **Evidence completeness:** availability of the inputs needed for a particular examination; always relative to that examination.
- **Criterion result:** the outcome of an identified procedure and criterion applied to an identified state.
- **Interpretation:** an attributed explanation or assessment, linked to evidence without becoming an observation.

These dimensions remain separate. A valid record can describe missing evidence, a failed criterion, conflicting observations, or an interrupted execution; none of those makes the record itself invalid.

## Common record envelope

Propose immutable, typed records with the following common fields. A JSON encoding is the initial exchange target; no storage backend is selected by this document.

| Field | Proposed meaning |
|---|---|
| `schema_id`, `schema_version` | Explicit contract for this record type; unknown schema versions remain inspectable as opaque data but cannot be claimed structurally valid under a known schema |
| `record_id` | Globally scoped identifier consisting of ledger namespace and opaque local ID; never inferred from wording |
| `record_type` | An explicit type from the type table below |
| `source_refs` | Zero or more typed source links; empty means provenance is absent, not that the instrument independently established the content |
| `recorded_at` | Acquisition/recording time when available, with clock metadata; not interchangeable with the time the described event occurred |
| `producer` | Recorded process, assessor, or instrument identity and version where available; reported identity is not authenticated identity |
| `payload` | Type-specific fields, with explicit missingness where required |
| `relations` | Typed links such as `amends`, `supersedes`, `derived_from`, and `about`; meaning is not inferred from proximity |

Missing mandatory fields cause structural rejection with named diagnostics. That rejected submission may still be preserved as an ingestion artifact plus a rejection event; it is not admitted as a structurally valid instance of the requested type.

### Type-specific responsibilities

| Record type | Required distinction or content |
|---|---|
| `claim` | Exact wording, attributed source or explicit source absence, scope, and links to examinations; repeated wording never shares identity automatically |
| `source` | Recorded origin, locator, source kind, version/date if known, and direct-inspection status; a locator is not proof that its content was read |
| `condition` | A stated or observed circumstance and its provenance; distinguish reported conditions from independently measured ones |
| `intervention` | Intended change, target conditions, and execution evidence; intending a change does not establish that it occurred |
| `observation` | Recorded measurement/event, instrument or reporting channel, conditions, validity/missingness, units and timing where relevant |
| `artifact` | Inspectable-object reference, type, acquisition metadata, recorded provenance, and available integrity information |
| `verification_event` | Subject/state, property, procedure, criteria, inputs, outputs, execution references, and result |
| `interpretation` | Attributed explanation with supporting and challenging links, scope, and unresolved alternatives; no automatic root-cause designation |
| `unknown` | Property not established, the subject it concerns, and what is missing; no numerical value manufactured for it |
| `calculation` | Derived quantity, input record IDs, method/version, mathematical prerequisites, result or explicit unavailability |
| `model` | Purpose, target, representation, scope, assumptions, boundaries, variables/units/dependencies, interactions, operating regime, outputs/tolerances, provenance/state |
| `experiment` | Trial identity, conditions/inputs/interventions, expected and observed measurement references, missing data, and execution references |
| `execution_event` | Evidence about a requested/attempted/completed/interrupted operation; not a verification result by itself |

Calculations, models, experiments, and execution events are proposed supporting types, not replacements for specification 0.2's evidence objects. A human statement about an observation is recorded as a report with attribution; it is not silently upgraded to an independently instrumented measurement.

## Values, references, and missingness

For a value-bearing field, propose an explicit object with `status`, plus `value` only where that status permits it. Initial statuses are `PRESENT`, `MISSING`, `INVALID`, and `NOT_APPLICABLE`; the record retains the reason and any raw artifact reference.

- **Measured zero:** `{"status":"PRESENT","value":0}` remains an ordinary value, not a missing-data marker.
- **Missing value:** `{"status":"MISSING","reason":"not_measured"}` carries no substituted number; other reasons may describe unavailable inputs, failed acquisition, or an uninstrumented property.
- **Invalid measurement:** retain the raw value or artifact and the rule that invalidated it, without using that value as a valid calculation input.
- **Not applicable:** require an attributed reason tied to the examined property, not a default used to hide missing work.

A null, absent field, empty string, and literal sentinel string are not silently interchangeable. A legacy importer must name its conversion rules, retain the original input, and report unresolved cases.

Reference resolution has a separate state: `NOT_CHECKED`, `RESOLVED`, `UNRESOLVED`, or `TYPE_MISMATCH`. Allow unresolved references in evidence records when explicitly marked; operations requiring those references remain blocked or indeterminate rather than inventing their targets. Never silently fetch a locator during local operation.

## Ledger order, amendments, and concurrency

Propose an append-only logical event stream with transactional append operations, unique event IDs, a ledger namespace, and a strictly increasing local sequence number. Sequence numbers order acceptance into that ledger, not necessarily real-world event occurrence.

Corrections create new records linked by `amends` or `supersedes`, retain the earlier record, and name the author/process and reason. Supersession is a recorded relationship, not deletion or proof that the successor is true; conflicting successors remain visible, and no “latest wins” rule silently chooses an evidentiary conclusion.

Reject duplicate IDs with different content as conflicts. Reimporting the same identified record with identical stored content may be idempotent, but any equivalence or canonicalization rule must be declared; identical wording alone does not establish identity.

Atomic append semantics must prevent concurrent writers from silently losing records. Interrupted writes, damaged storage, and unknown reference targets produce integrity diagnostics; the report must not hide those gaps by presenting an apparently complete sequence.

Append-only application behavior is not tamper-proof storage. Deletion/redaction for consent or sensitive material requires an explicit policy and visible tombstone where permissible; do not promise immutable retention and unrestricted deletion simultaneously.

## Time and examined state

Preserve event time, acquisition time, and recording time separately when available. Timestamp metadata should include clock source, timezone/offset, precision, and uncertainty where known; use monotonic timing for within-process intervals where available.

Do not compare intervals across clocks without a recorded alignment method and sufficient timing precision. Equal, missing, or ambiguous times do not justify inventing an order; ledger sequence only establishes local recording order.

A subject-state record names the examined model/code/configuration/input versions and available content digests. A missing version stays unknown even when a locator or filename exists.

Verification is bound to:

```text
(subject reference, examined state reference, tested property,
 procedure identity/version, criteria identity/version, dependency references)
```

Later changes do not erase the original event or retroactively change its result. A separate applicability assessment proposes `SAME_DECLARED_STATE`, `RELEVANT_CHANGE_RECORDED`, or `APPLICABILITY_UNKNOWN`, with evidence and assessor attribution; the first means only that the declared state matches, not that all real-world influences are known unchanged.

Dependency relevance must be declared and reviewed. Age alone is not staleness; an unreviewed change or incomplete dependency graph does not warrant inheriting a pass or declaring the underlying science failed.

## Execution and verification

Record these stages separately: request, attempt, completion/interruption, exit status, output production, artifact inspection, criteria evaluation, and criterion result. An absent later stage is missing evidence, not an implied success; a zero exit code establishes only the recorded process exit condition.

A verification event uses `MET`, `NOT_MET`, `INDETERMINATE`, or `NOT_EVALUATED` per criterion. Record the criterion's exact subject/property and expected evidence; absence can establish `NOT_MET` only when a declared criterion explicitly tests absence and the procedure has sufficient evidence to evaluate it.

Distinguish declared operator assertions from captured check outputs. Multiple examinations can disagree without overwriting each other, and aggregating per-criterion results requires an explicitly versioned aggregation rule; do not emit a universal `verified: true` field.

Structural schema checking produces a validation event about the record's structure. It must not set a claim's empirical support or change an interpretation into an observation.

### Local execution authorization

Default to recording supplied artifacts and check results, not executing code found in them. Any future execution mode requires explicit authorization scoped to the procedure, command, inputs, working directory, and intended side effects, plus timeout/interruption handling and output capture.

Use argument lists rather than implicit shell evaluation, do not auto-install dependencies or access the network, and do not capture secrets into logs. Local execution is not a security sandbox; procedures that cannot be executed safely within available controls remain unexecuted with the reason recorded.

## Numerical method contract

Every calculation identifies compatible quantities, input records, exact method/version, units, operating domain, and any uncertainty assumptions. Start with exact declared quantity/unit compatibility; reject or defer unsupported conversions rather than implementing an implicit universal units engine.

- **Signed residual:** observed minus predicted, when both inputs are valid and compatible.
- **Absolute residual:** absolute value of that signed residual, retaining units and input references.
- **Relative residual:** specify the denominator and its sign/absolute-value convention; a zero denominator makes this quantity unavailable, even if the absolute residual is defined.
- **Combined uncertainty:** state whether inputs represent standard uncertainties, variances, intervals, or something else; do not mix them silently.
- **Normalized residual:** define its normalization explicitly; require a valid, nonzero denominator and identify whether the result is dimensionless.

For a declared variance-based method on compatible variables, the residual variance may be calculated as
\[
\operatorname{Var}(y-\hat y)=\operatorname{Var}(y)+\operatorname{Var}(\hat y)-2\operatorname{Cov}(y,\hat y).
\]
Missing covariance is not zero covariance. Use an explicitly justified and attributed independence assumption or report that uncertainty calculation unavailable; retain the possibility that the ordinary residual is still calculable.

Specify numeric representation and rounding before implementation. The initial JSON exchange should not emit nonstandard NaN/Infinity numeric literals; non-finite inputs/results require explicit diagnostic status and, where available, raw provenance rather than silent zero substitution.

User-specified tolerances belong to a named criterion and domain. Numerical agreement within tolerance establishes that criterion only; it does not identify a discrepancy's cause or prove the model generally correct.

## Ordered cases and candidate regions

Preserve supplied case order and compare adjacent case references; sorting, interpolation, smoothing, or bridging across missing cases requires a separate declared transformation, not silent preprocessing. Each comparison names its input measurements and changed conditions, including unknown changes.

Threshold criteria must declare the quantity being compared, absolute/signed/relative convention, units, inclusive/exclusive operator, and boundary handling. Test below, at, and above the threshold; zero is a valid measurement unless a particular mathematical operation makes it unusable.

Output a candidate region with both case IDs, the comparison calculation, criterion/version, and limitations. An irregularly spaced pair indicates an interval between observed cases, not a precisely located boundary; varying several conditions cannot assign causality to one condition automatically.

## Interpretations, voice, and research sources

Interpretations can coexist, overlap in category, and be uncategorized. New evidence may support, challenge, or motivate a revision, but no category, repeated claim, missing alternative, or nonzero residual automatically establishes a root cause.

### Voice-event capability boundary

Each trial needs a capability record naming available audio/events, timestamp precision, clock alignment, annotation method, exact instruction, mode, system version where known, trial order, and consent/retention constraints. Endpoint decisions unavailable to the instrument remain unknown even if response onset is observable.

Premature response requires a reliable completion criterion and sufficiently comparable onset/completion times. Overlapping timing uncertainty yields indeterminate classification; a pause alone is not a completion point, and a response's relevance does not erase its onset event.

Record backchannels separately from other spoken responses. Attribute speaker-reported disruption and recovery cost to their reporting or coding procedure; neither is inferred solely from an interruption.

Assess instruction compliance across specified observed trials, not from the system's assertion. A synthetic sequence validates schema/classification behavior only; it does not demonstrate live instrumentation or establish a particular system's turn-taking behavior.

### Research-source boundary

Record exact quantitative claims, study/version/date, tested system/population, sample and denominator, operational definition, evaluation method/limits, direct inspection, and independent reproduction separately. A source saying it replicated a result is not evidence that this instrument reproduced it.

Uninspected claims stay source-reported and unverified. Cross-benchmark ranking and product/model attribution require explicit comparability or identity evidence; general endpointing results do not establish the specified voice system's behavior.

## Reporting, exchange, and review gates

Reports separate observations, calculations, criteria/results, missing evidence, unresolved questions, interpretations, and verification limits. Include record/state references and a report-generation version, so corrections can regenerate a view without erasing the earlier report artifact.

Export identifiers, type/schema versions, evidence links, missingness, examined states, procedures/criteria, results, and limitations. Imports into study-aperture initially remain explicit assessor-reviewed transfers; no lab result automatically changes a publication-support grade or resolves a decision.

Source fields record provenance assertions, not verified provenance. Artifact hashes can support comparison with recorded bytes but do not independently authenticate origin, establish truth, or prevent a privileged actor rewriting the entire local ledger.

### Proposed review gates

The [pre-implementation decision checklist](decision-checklist.md) records these gates as review items with explicit approval status and scope. All choices remain proposed until separately approved; creating that checklist is not approval.

- **Evidence gate:** review typed records, missingness, reference rules, immutable identity, correction semantics, and privacy requirements before implementing Stage A.
- **Verification gate:** settle subject-state binding, relevant-change assessments, execution authorization, and per-criterion result vocabulary.
- **Numerical gate:** settle numeric representation, units, covariance assumptions, threshold operators, and unavailable-result semantics before Stage B.
- **Voice gate:** settle event capabilities, clock/annotation uncertainty, and consent before Stage C; live access requires its own demonstrated capability.
- **Integration gate:** connect every implemented behavior to executed acceptance tests and inspectable artifacts before claiming conformance; documentation checks are not implementation tests.

## Traceability to the planned matrix

This table links proposal areas to existing planned tests; it does not assert that the matrix exhaustively tests this contract. The additional contract-specific cases below remain proposed extensions, not silent edits to requirements 0.2.

| Contract area | Existing planned checks |
|---|---|
| Types, missingness, references | TYPE.01–02; FR-01.01–03; FR-02.01–03; FR-10.01–04 |
| State-bound verification and execution | FR-03.01–03; FR-04.01–04 |
| Models, trials, numerical methods | FR-05.01–03; FR-06.01–04; FR-07.01–04 |
| Ordered comparisons and explanations | FR-08.01–06; FR-09.01–04 |
| Voice and research sources | VOICE.01–07; SOURCE.01–05 |
| Reporting and integration | FR-11.01–02; G-01–10 |

Additional tests will be needed for duplicate-ID conflicts, concurrent append/interrupted writes, competing supersessions, unknown schema versions, clock alignment and overlapping timing uncertainty, covariance absence, non-finite numeric inputs, execution authorization, and consent-sensitive redaction. Their exact fixtures and accepted outcomes require review before implementation; none has been run here.
