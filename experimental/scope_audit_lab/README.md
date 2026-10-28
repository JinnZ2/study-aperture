# Scope Audit Lab

Status: Proposed; documentation only. Specification 0.2 is not implemented or validated by this addition. No experiment runner, executable schemas, live voice instrumentation, or acceptance-test results are supplied here.

Scope Audit Lab is proposed as an experimental auditing instrument for scoped mathematical models and computational agents. It should preserve claims, conditions, observations, artifacts, verification events, unknowns, and competing interpretations without silently choosing a conclusion.

## Start here

- **Requirements:** [Specification 0.2](requirements/scope-audit-lab-0.2.md) preserves the specification supplied by the project owner, including its proposed baseline and implementation order.
- **Acceptance matrix:** [Requirement-to-test mapping](docs/acceptance-matrix.md) assigns documentation identifiers to proposed checks, inputs, and inspectable artifacts. Every check is planned and not run.
- **Parent toolkit:** [study-aperture](../../README.md) remains the publication-appraisal and decision-record layer; this folder does not replace or extend its recorder.

## Boundary decision

Keep this subproject in `experimental/scope_audit_lab/` with an independent future schema and test suite. The lab would record what a specified procedure established about an examined state; the parent toolkit would record how that evidence bears on a publication claim or decision.

Initially prefer explicit JSON exchange over shared mutable state. An imported test pass must not automatically promote a publication claim to supported, convert an interpretation to an observation, or establish empirical validity.

## What has not been established

- **Prototype baseline:** Prototype 0.1 is named by the supplied specification but was not supplied or inspected for this addition. The listed baseline modules are requirements context, not verified files in this repository.
- **Research summary:** the summary referenced in section 5 was not supplied with the specification. No quantitative claims from it have been checked or reproduced.
- **Voice access:** no audio stream, endpoint event, response-onset instrumentation, or platform-level silence control has been demonstrated.
- **Implementation:** no runtime code, storage backend, schemas, or test framework has been selected or implemented in this folder.

## Proposed next steps

Review Prototype 0.1 before adapting its modules. Then settle an evidence contract covering typed identities and references, version-bound verification, corrections and supersession, declared numerical methods, and observable-event capabilities.

Use the supplied Stage A through D order as the baseline. Run adversarial checks and report checks alongside each implementation stage rather than interpreting Stage D as permission to delay evidence-integrity tests.

The acceptance matrix is a planning artifact, not an execution log or proof of coverage by working tests. Passing future tests would establish the specified software behaviors within their tested scope, not universal correctness of audited models, agents, or voice interactions.
