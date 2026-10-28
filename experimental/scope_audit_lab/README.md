# Scope Audit Lab

Status: Experimental; includes a narrow offline evidence-integrity checker, draft schemas, documentation, and scoped verification artifacts. Complete specification 0.2 conformance is not established. No runtime experiment runner, physics validator, ledger backend, or live voice instrumentation is supplied here.

Scope Audit Lab is proposed as an experimental auditing instrument for scoped mathematical models and computational agents. It should preserve claims, conditions, observations, artifacts, verification events, unknowns, and competing interpretations without silently choosing a conclusion.

The [criterion-to-conclusion mappings](docs/criterion-conclusion-mappings.md) are a draft contract separating mathematical validity, dimensional compatibility, numerical agreement, and empirical support. A [worked October 27, 2026 theoretical-study run](reviews/tolman-vi-2026-10-27/README.md) exercises bounded offline checks with recorded passing results, a candidate discrepancy, unresolved provenance, and preserved correction history; it is not a general inference engine or full-paper validation.

The [phase-to-probability follow-up](reviews/tolman-vi-phase-trace-0.1/README.md) separately examines global versus partial phase reversal, mixing-angle-dependent averages, and response-kernel assumptions. Its conditional mathematical results do not establish empirical detectability or an adopted correction to the published model.

## Start here

- **Active focus:** [Mathematics and physics scope decision](docs/math-physics-focus.md) records the owner's prioritization of evidence and assessment for mathematics, equations, and physics. Voice work is deferred; mathematical and physical judgment procedures remain proposals rather than implemented capabilities.
- **Offline integrity checker:** [Usage and verification limits](docs/offline-integrity-checker.md) covers the implemented stdlib-only checker for snapshot references, exact version bindings, anchor-condition coverage, and [explicit assessment-subject relevance](docs/assessment-link-relevance.md). Matching metadata does not establish scientific support; this is not a mathematical/empirical validator.

- **Requirements:** [Specification 0.2](requirements/scope-audit-lab-0.2.md) preserves the specification supplied by the project owner, including its proposed baseline and implementation order.
- **Acceptance matrix:** [Requirement-to-test mapping](docs/acceptance-matrix.md) assigns documentation identifiers to proposed baseline checks. Their full procedures remain planned and not run; the narrow integrity suite is recorded separately rather than claimed as complete baseline coverage.
- **Evidence contract:** [Draft proposal 0.1](docs/evidence-contract.md) separates proposed design choices from unchanged specification 0.2, covering typed records, missingness, verification, amendments, numerical rules, execution authorization, and voice observability. It is not an implemented or stable interface.
- **Decision checklist:** [Pre-implementation review](docs/decision-checklist.md) records E-01 APPROVED for independent development, with Prototype 0.1 compatibility UNKNOWN. Voice items are DEFERRED; other design items remain OPEN.
- **Draft evidence schemas:** [Five mathematical evidence record types](schemas/draft-0.1/README.md) propose equations, assumptions, derivations, scalar observations, and property-specific assessments, with synthetic examples and planned review cases. These are not a runtime validator, an approved stable interface, or mathematical/empirical validation.
- **Physics-case review:** [Dimensional, balance, and approximation cases](reviews/physics-cases/README.md) examine the draft against eight scoped cases, with reproducible synthetic arithmetic and authoring-only structural probes. Proposed extensions are not adopted schema changes or lab acceptance-test results.
- **Scoped physics extension draft:** [Draft 0.2](schemas/draft-0.2/README.md) proposes six additive supporting record types, with sourced energy, momentum, and entropy reference anchors, explicit applicability gates, and synthetic examples. This does not replace draft 0.1 or establish implementation/conformance to requirements specification 0.2.
- **Parent toolkit:** [study-aperture](../../README.md) remains the publication-appraisal and decision-record layer; this folder does not replace or extend its recorder.

## Boundary decision

Keep this subproject in `experimental/scope_audit_lab/` with an independent future schema and test suite. The lab would record what a specified procedure established about an examined state; the parent toolkit would record how that evidence bears on a publication claim or decision.

Initially prefer explicit JSON exchange over shared mutable state. An imported test pass must not automatically promote a publication claim to supported, convert an interpretation to an observation, or establish empirical validity.

## What has not been established

- **Prototype baseline:** independent development is authorized under E-01. Prototype 0.1 was not supplied or inspected; compatibility is UNKNOWN, and the listed baseline modules are requirements context rather than inherited or verified files.
- **Research summary:** the summary referenced in section 5 was not supplied with the specification. No quantitative claims from it have been checked or reproduced.
- **Voice access:** no audio stream, endpoint event, response-onset instrumentation, or platform-level silence control has been demonstrated.
- **Implementation:** a read-only evidence-integrity checker and its stdlib test suite are implemented. A full audit engine, storage backend, schema-validation engine, and mathematical/physical assessor remain unimplemented; draft schemas remain proposals rather than approved stable interfaces.

## Proposed next steps

Proceed independently without waiting for Prototype 0.1. Review the draft evidence contract and settle its remaining open implementation choices before treating them as interface commitments; inspect an identified prototype version only if a later compatibility assessment is requested.

Use the decision checklist to record approvals, deferrals, decision makers, and their scope. Prioritize evidence and verification for mathematical and physical claims; settle numerical representation and uncertainty rules before implementing calculations. Voice work remains deferred until explicitly resumed.

Keep the supplied Stage A through D order as the unchanged baseline, but exclude Stage C voice work from the current scoped milestone. Run relevant adversarial and report checks alongside each active stage rather than interpreting Stage D as permission to delay evidence-integrity tests; a milestone excluding voice cannot claim complete specification 0.2 conformance.

The acceptance matrix is a planning artifact, not an execution log or proof of coverage by working tests. Passing future tests would establish the specified software behaviors within their tested scope, not universal correctness of audited models, agents, or voice interactions.
