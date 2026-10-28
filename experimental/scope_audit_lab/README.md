# Scope Audit Lab

Status: Proposed; documentation only. Specification 0.2 is not implemented or validated by this addition. No experiment runner, executable schemas, live voice instrumentation, or acceptance-test results are supplied here.

Scope Audit Lab is proposed as an experimental auditing instrument for scoped mathematical models and computational agents. It should preserve claims, conditions, observations, artifacts, verification events, unknowns, and competing interpretations without silently choosing a conclusion.

## Start here

- **Active focus:** [Mathematics and physics scope decision](docs/math-physics-focus.md) records the owner's prioritization of evidence and assessment for mathematics, equations, and physics. Voice work is deferred; the proposed procedures are not implemented capabilities.

- **Requirements:** [Specification 0.2](requirements/scope-audit-lab-0.2.md) preserves the specification supplied by the project owner, including its proposed baseline and implementation order.
- **Acceptance matrix:** [Requirement-to-test mapping](docs/acceptance-matrix.md) assigns documentation identifiers to proposed checks, inputs, and inspectable artifacts. Every check is planned and not run.
- **Evidence contract:** [Draft proposal 0.1](docs/evidence-contract.md) separates proposed design choices from unchanged specification 0.2, covering typed records, missingness, verification, amendments, numerical rules, execution authorization, and voice observability. It is not an implemented or stable interface.
- **Decision checklist:** [Pre-implementation review](docs/decision-checklist.md) records E-01 APPROVED for independent development, with Prototype 0.1 compatibility UNKNOWN. Voice items are DEFERRED; other design items remain OPEN.
- **Draft evidence schemas:** [Five mathematical evidence record types](schemas/draft-0.1/README.md) propose equations, assumptions, derivations, scalar observations, and property-specific assessments, with synthetic examples and planned review cases. These are not a runtime validator, an approved stable interface, or mathematical/empirical validation.
- **Parent toolkit:** [study-aperture](../../README.md) remains the publication-appraisal and decision-record layer; this folder does not replace or extend its recorder.

## Boundary decision

Keep this subproject in `experimental/scope_audit_lab/` with an independent future schema and test suite. The lab would record what a specified procedure established about an examined state; the parent toolkit would record how that evidence bears on a publication claim or decision.

Initially prefer explicit JSON exchange over shared mutable state. An imported test pass must not automatically promote a publication claim to supported, convert an interpretation to an observation, or establish empirical validity.

## What has not been established

- **Prototype baseline:** independent development is authorized under E-01. Prototype 0.1 was not supplied or inspected; compatibility is UNKNOWN, and the listed baseline modules are requirements context rather than inherited or verified files.
- **Research summary:** the summary referenced in section 5 was not supplied with the specification. No quantitative claims from it have been checked or reproduced.
- **Voice access:** no audio stream, endpoint event, response-onset instrumentation, or platform-level silence control has been demonstrated.
- **Implementation:** no runtime audit engine, storage backend, validator, or test framework has been selected or implemented in this folder. Declarative draft schemas are now available for review; their presence does not establish any runtime capability.

## Proposed next steps

Proceed independently without waiting for Prototype 0.1. Review the draft evidence contract and settle its remaining open implementation choices before treating them as interface commitments; inspect an identified prototype version only if a later compatibility assessment is requested.

Use the decision checklist to record approvals, deferrals, decision makers, and their scope. Prioritize evidence and verification for mathematical and physical claims; settle numerical representation and uncertainty rules before implementing calculations. Voice work remains deferred until explicitly resumed.

Keep the supplied Stage A through D order as the unchanged baseline, but exclude Stage C voice work from the current scoped milestone. Run relevant adversarial and report checks alongside each active stage rather than interpreting Stage D as permission to delay evidence-integrity tests; a milestone excluding voice cannot claim complete specification 0.2 conformance.

The acceptance matrix is a planning artifact, not an execution log or proof of coverage by working tests. Passing future tests would establish the specified software behaviors within their tested scope, not universal correctness of audited models, agents, or voice interactions.
