# Scope Audit Lab: acceptance-test matrix

Status: Proposed; documentation only. Every row below has execution status **NOT RUN**; no row is implemented or passed by its inclusion here. This matrix interprets the [unchanged specification 0.2](../requirements/scope-audit-lab-0.2.md) into proposed tests and required evidence, without adding implementation claims.

Current scope: [S-01 and S-02](math-physics-focus.md#recorded-scope-decision) prioritize mathematical/physical evidence and assessment, and defer voice work. VOICE.01–07 and the voice-dependent G-08 remain NOT RUN and excluded from the current milestone; deferral is not a pass or a reason to claim full-baseline conformance.

## Reading the matrix

Test identifiers are planning references, not existing test functions. `FR-xx.nn` follows the acceptance-bullet order under each functional requirement; FR-11, evidence-model, and research-source rows map prose obligations into proposed tests, while `VOICE.nn` follows the seven voice acceptance bullets.

Artifact names below describe future outputs, not existing files. Each future execution should emit a structured result identifying the test, examined version or state, inputs, procedure and criteria versions, outcome, missing evidence, and output artifact references; a stdout statement that a test passed is not sufficient evidence by itself.

## Evidence-model contract

| Proposed test | Input or intervention | Required observable behavior | Planned evidence artifact |
|---|---|---|---|
| TYPE.01 | Claim, observation, calculation, interpretation, source, condition, intervention, artifact, verification event, and unknown fixtures | Types stay distinguishable; prohibited substitution does not silently coerce one into another | Round-trip records and validation diagnostics |
| TYPE.02 | Missing property, invalid measurement, uninstrumented property, and measured zero | Missing, invalid, uninstrumented, and zero remain distinct | Exported records and rendered report |

## Functional requirements

| Proposed test | Input or intervention | Required observable behavior | Planned evidence artifact |
|---|---|---|---|
| FR-01.01 | Identical claim wording from two sources | Distinct claim IDs and source links survive round trip | Claim export |
| FR-01.02 | Claim with absent source | Source-missing state is explicit | Claim record and diagnostic |
| FR-01.03 | Unverified claim repeated by another source | Repetition alone does not promote verification | Before/after claim and event records |
| FR-02.01 | Claim with no artifact references | No-artifact-support state remains explicit, not falsehood | Claim export and report |
| FR-02.02 | Broken or unavailable artifact reference | Reference is unresolved, not evidence the claim is false | Availability-check result |
| FR-02.03 | Existing artifact with invalid contents | Existence and content-validity results are separate | Artifact metadata and verification result |
| FR-03.01 | Pass on version A, followed by relevant change to B | A's result is not inherited as a pass for B | Dependency states and verification-applicability diagnostic |
| FR-03.02 | Verification with missing version information | Examined state remains unknown | Verification record and report |
| FR-03.03 | Old unchanged artifact, plus a new relevant-change case | Age alone does not make evidence stale; relevant change is reported | Paired verification-applicability results |
| FR-04.01 | Completed operation with zero exit status | Scientific validity is not inferred from exit code | Execution record and report |
| FR-04.02 | Generated file whose contents have not been inspected | Output existence does not establish content correctness | Artifact record and inspection state |
| FR-04.03 | Verbal assertion that a check passed without a check result | Assertion remains a claim, not a recorded verification pass | Claim and verification exports |
| FR-04.04 | Completion statement without execution evidence | Attempt, completion, exit status, output, inspection, criteria evaluation, and established result are not reconstructed | Execution-stage records and missing-evidence report |
| FR-05.01 | Model with missing assumptions | Absence is retained rather than default assumptions inserted | Model export |
| FR-05.02 | Model with explicitly excluded variable | Exclusion is not converted into irrelevance to reality | Scope record and report |
| FR-05.03 | Scoped model evaluated against declared purpose | Adequacy assessment names purpose, scope, evidence, and limits rather than assuming universal completeness | Scope-assessment record |
| FR-06.01 | Repeated trials with identical inputs | Trial identity remains distinct | Trial export |
| FR-06.02 | Control requested but never performed | No negative-control observation is manufactured | Control execution status and missing observation |
| FR-06.03 | Observational association without causal design evidence | No automatic causal label appears | Observation and interpretation records |
| FR-06.04 | Two explanations associated with one discrepancy | Both remain linked and unresolved | Observation-to-interpretation links |
| FR-07.01 | Missing predicted or observed value | Calculation is explicitly unavailable | Calculation record with missing-input references |
| FR-07.02 | Relative or normalized residual with zero denominator | Undefined operation is explicit, not silently zero or an ordinary numeric result | Calculation diagnostic |
| FR-07.03 | Incompatible units or quantities | No silent combination occurs | Compatibility result and original inputs |
| FR-07.04 | Nonzero residual with several plausible causes | Calculation does not select a cause | Calculation and unresolved interpretation records |
| FR-08.01 | Deliberately unsorted case series | Input ordering is preserved | Case IDs and adjacent-pair export |
| FR-08.02 | Below-threshold, at-threshold, and above-threshold cases | Declared inclusive/exclusive rule determines the result | Criterion version, boundary cases, and comparisons |
| FR-08.03 | Missing intermediate measurement | Missing value stays visible and is not zero-filled | Ordered cases and unavailable comparison |
| FR-08.04 | Genuine zero-valued output | Zero is retained and compared according to criteria | Comparison result with input references |
| FR-08.05 | Candidate transition between adjacent cases | Output traces to both cases and their measurements | Candidate-region record |
| FR-08.06 | Threshold crossing that could have several explanations | Label remains candidate region requiring investigation, not phase transition, causal boundary, regime change, or model failure | Candidate-region report |
| FR-09.01 | Add explanation B after explanation A | A is retained | Before/after links and ledger events |
| FR-09.02 | Interpretation assigned a predefined category | Category membership does not establish it | Interpretation state record |
| FR-09.03 | Explanation outside supplied categories | Custom explanation remains representable | Interpretation round trip |
| FR-09.04 | Multiple candidate explanations | None is automatically selected as root cause | Interpretation export and report |
| FR-10.01 | Record with source and experiment links | Trace traverses both links and reports gaps | Provenance trace |
| FR-10.02 | Correction superseding an earlier result | Both records survive with amendment link and ordering | Ledger export and correction trace |
| FR-10.03 | Missing provenance | Gap remains explicit | Provenance diagnostics |
| FR-10.04 | Structurally valid record with untested empirical content | Structural validity is reported separately from empirical support | Validation output and report |
| FR-11.01 | Fixture mixing observations, calculations, criteria, missing evidence, questions, interpretations, and limits | All seven report categories remain separately identifiable | Rendered report plus source record IDs |
| FR-11.02 | Unresolved criteria or questions | Report generation does not force success or failure | Report and retained unresolved states |

## Voice experiment

These tests concern event records and classification rules, not live platform behavior. Recorded or synthetic fixtures must be labeled accordingly; schema tests cannot establish that a live system exposes the needed events.

| Proposed test | Input or intervention | Required observable behavior | Planned evidence artifact |
|---|---|---|---|
| VOICE.01 | Pause between speech segments without completion annotation | Pause is not automatically a completed thought | Event sequence and completion state |
| VOICE.02 | Relevant system response before defined completion | Response event is retained regardless of content relevance | Annotated event sequence |
| VOICE.03 | System says it complied but observed trials violate instruction | Compliance is assessed from trial behavior, not its claim | Exact instruction and trial comparison |
| VOICE.04 | Trial lacks reliable completion annotation | Premature-response classification is indeterminate | Classification with missing-criterion diagnostic |
| VOICE.05 | Missing audio, timestamps, or logs | Missing material is not reconstructed as measured fact | Capability record and missing-evidence report |
| VOICE.06 | Interruption event without recovery-cost measurement | Recovery cost remains unmeasured; disruption is not inferred solely from interruption | Event, disruption-source, and recovery records |
| VOICE.07 | Partial instrumentation, including hidden endpoint decisions | Report states which defined events can and cannot be distinguished | Instrumentation capability report |

## Research-source audit

The research summary referenced in section 5 was not supplied with this specification. The following are proposed checks on source-audit behavior, not assertions that its quantitative claims have been gathered or verified.

| Proposed test | Input or intervention | Required observable behavior | Planned evidence artifact |
|---|---|---|---|
| SOURCE.01 | Quantitative claim from an uninspected research summary | Source-reported and unverified status remains explicit | Claim and source records |
| SOURCE.02 | Claim with value, study, date/version, tested population/system, sample/denominator, definition, evaluation limits, inspection status, and reproduction status | All supplied fields survive; missing fields stay missing | Structured source-audit export |
| SOURCE.03 | Results from different benchmarks or model variants without comparability analysis | No automatic combined ranking | Comparison refusal or unresolved comparability report |
| SOURCE.04 | Coding-agent finding attributed to a differently named product | Relationship requires evidence; attribution remains unresolved without it | Identity/relationship evidence record |
| SOURCE.05 | General endpointing result applied to the specified voice pattern | General result is not presented as direct evidence for that system/pattern | Scope and source-classification report |

## Global acceptance criteria

These are integration-level checks, not redundant declarations that the unit-level plans already pass. Each requires an inspected artifact from actual execution against an identified implementation state.

| Criterion | Planned test references | Required integration evidence |
|---|---|---|
| G-01: distinct claim, observation, calculation, interpretation | TYPE.01; FR-04.03; FR-11.01 | End-to-end export and report retain record types |
| G-02: evidence trace or explicit missing evidence | FR-01.02; FR-02.01–02; FR-10.01 | Supported-claim trace and missing-evidence counterexample |
| G-03: version-aware verification | FR-03.01–03 | Examined-state export and later-change applicability result |
| G-04: missing is never silently measured | TYPE.02; FR-06.02; FR-07.01; FR-08.03; VOICE.05 | Missing/invalid/zero cases through storage, calculation, and reporting |
| G-05: numerical difference is not a causal explanation | FR-06.03; FR-07.04; FR-09.04 | Residual report with multiple unresolved explanations |
| G-06: candidate transition is not an established boundary | FR-08.02; FR-08.05–06 | Boundary-case outputs retain candidate labels and input links |
| G-07: competing explanations coexist | FR-06.04; FR-09.01–04 | Add/correct/export sequence preserves alternatives |
| G-08: voice classifications depend on criteria and observable records | VOICE.01–07 | Synthetic event fixtures and capability-limited classification report |
| G-09: research claims retain source and verification status | SOURCE.01–05; FR-01.03 | Source-audit round trip with unverified/reproduced states kept distinct |
| G-10: structural validity is not empirical validity | FR-04.01–03; FR-10.04; FR-11.01–02 | Structurally valid but empirically unresolved report |

## Implementation-stage mapping and unresolved contracts

- **Stage A:** TYPE, FR-01–04, FR-09–10, and SOURCE fixtures first; establish the evidence contract before an execution engine.
- **Stage B:** FR-05–08 with synthetic numerical cases; retain FR-09–11 checks throughout.
- **Stage C:** deferred by S-02; the VOICE plans below remain baseline documentation, not active implementation work. Live instrumentation remains a separate unestablished capability.
- **Stage D:** consolidate reporting and adversarial integration tests, including conflicting observations and unsupported causes; this does not defer earlier-stage integrity tests.

Before writing tests, settle identifier namespaces, reference resolution, timestamp/clock semantics, verification-to-state bindings, dependency relevance, correction rules, unit compatibility, threshold inclusivity, residual denominators, uncertainty assumptions, and execution authorization. These are open design contracts, not decisions silently added to specification 0.2.

[Evidence contract proposal 0.1](evidence-contract.md) provides a separate draft for reviewing these choices, including additional proposed test cases. It does not change the requirements baseline or the NOT RUN status of this matrix.

For every future result, distinguish implementation-conformance evidence from empirical validation of the audited subject. Do not mark this matrix passed until actual tests produce inspectable artifacts and their limitations are reported.
