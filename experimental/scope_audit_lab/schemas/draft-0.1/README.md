# Mathematical evidence schemas: draft 0.1

Status: Review draft, not adopted as a stable schema or implemented as a runtime validator. Independent development is authorized; Prototype 0.1 compatibility remains UNKNOWN, and voice work is deferred.

The owner requested draft schemas for equations, assumptions, derivations, observations, and assessments. This proposal supplies five record shapes in [evidence.schema.json](evidence.schema.json), with [synthetic example records](../../examples/schema-draft-0.1/records.json), [review cases](review-cases.md), and a limited [drafting-time structural review](drafting-review.md); it does not close the remaining design gates merely by making their choices concrete.

## What the schema can and cannot express

The file uses JSON Schema Draft 2020-12 as a declarative interchange proposal. It adds no runtime dependency or network requirement; `$schema`, `$id`, and `$ref` identify schemas and definitions, not instructions to download material.

A future validator would need either an explicitly authorized local implementation or an approved offline validation strategy. Python's standard-library `json` parser alone does not validate JSON Schema, and syntactic review of this file is not runtime validation or acceptance-test execution.

The schema constrains record shape, field vocabularies, explicit missingness, and a small set of conditional requirements. It cannot establish:

- **Reference integrity:** that a referenced record exists, has the expected type/version, or was actually inspected.
- **Evidence authenticity:** that a source, timestamp, instrument, or reported result is truthful or independent.
- **Mathematical validity:** that a derivation is sound, an equation is well-defined, or a numerical result proves a universal identity.
- **Physical adequacy:** that dimensions, units, system boundaries, uncertainty assumptions, or model scope are correct.
- **Ledger guarantees:** append-only behavior, ID uniqueness across records, conflict handling, immutable versions, or correction history.

Those need separate, named semantic checks and inspectable execution evidence. Unknown schema versions remain opaque input rather than automatically conforming to this version.

## Shared conventions

Each record carries schema identity/version, a namespace-scoped record ID, record type, declared record version or explicit absence, source references, recording time or explicit absence, producer attribution, relations, and a typed payload.

IDs identify records, not truth or authenticity. Proposed immutable records must be amended by new linked records; a `record_version` label is descriptive state information, not permission to overwrite an existing ID.

### Explicit absence

Text-bearing values use `{"status":"PRESENT","value":"..."}` or an absence object such as `{"status":"MISSING","reason":"not supplied"}`. An absent/invalid/not-applicable value cannot also carry a usable `value`; optional `raw_text` preserves a rejected representation without turning it into a valid input.

Numeric observations use a present finite JSON number plus `encoding: "json_number"`, or the same absence object. Zero remains valid; this first proposal does not settle precision, rational/decimal representation, arithmetic, or conversion rules. Do not treat this field choice as approval of a numerical backend.

Ordinary absence reasons are open text, not a hidden finite taxonomy. Literal sentinel strings must not be used to evade absence states; this semantic convention is not enforceable against all possible text by the schema alone.

### References and provenance

References state `record_id`, `expected_type`, and resolution status. A schema-valid `RESOLVED` field is only a recorded assertion until an actual resolver checks its target.

`source_refs: []` explicitly means source provenance is missing; it does not imply an independently confirmed origin. Artifact references, condition records, experiment records, execution events, verification events, and interpretation records remain external types whose schemas are not drafted here.

References can point to such external or unavailable records, but this schema neither invents those records nor validates them. Empty artifact/execution lists mean there is no linked artifact/execution evidence, not that no event occurred.

## Record responsibilities

### Equation

An equation record captures exact wording, its original representation and location, any transcription, statement kind, symbols, scope, assumptions, dependencies, and ambiguities. Recording a theorem claim or identity does not establish it.

Symbols retain mathematical type, domain, physical quantity, dimensions, units, and conventions separately. Empty symbol lists or missing declarations remain missing assessment inputs; a structurally valid but incompletely declared equation is not automatically ready for every analysis.

Scopes separate domain, included/excluded scope, regime, and boundary/initial conditions. `NOT_APPLICABLE` requires a reason; the absence of physical units in a purely mathematical example must not manufacture a physical quantity.

### Assumption

An assumption is a declaration with a role, applicability scope, and evidence/assessment links, not an established observation. `SOURCE_EXPLICIT` means explicitly stated by the attributed source, not verified in nature; absent sources require a provenance diagnostic rather than silently inventing a source.

The listed roles are non-exhaustive through `OTHER`. An assessor may propose a missing prerequisite, but it must be labeled `ASSESSOR_PROPOSED` rather than attributed to a publication that never stated it.

### Derivation

A derivation records ordered steps, their premises, prior-step dependencies, conclusions, operations, claimed relations, and required or introduced assumptions. `IMPLIES` runs from the listed premises to the conclusion; `EQUIVALENT` and `APPROXIMATES` are declared claims, not checked facts.

Step IDs are local to a derivation record; assessment selectors may identify them. A semantic checker must verify uniqueness, existence of prior steps, acyclic dependency/order rules, and assumption scope before evaluating a step. `COMPLETE_AS_RECORDED` describes the submitter's account, not a proof certificate.

Introduced assumptions are not silently established or discharged. Branches, changed domains, or non-equivalence must be preserved; proof-system integration, symbolic parsing, and formal proof checking are not provided.

### Observation

An observation distinguishes a physical measurement, numerical run, attributed report, and synthetic fixture. It records a value or explicit unavailability, quantity/units, method/instrument, calibration, resolution, uncertainty, conditions, time, trial, artifacts, execution evidence, and limitations.

Calculations do not become physical measurements by being stored here. A future calculated quantity belongs in a separate calculation record; an observation of a numerical run must retain the run's provenance.

This first payload is scalar-numeric; vector, tensor, field, time-series, qualitative-event, and structured uncertainty records are outside its present scope. Preserve such material as referenced artifacts and explicit unsupported/missing scalar values rather than coercing it into a scalar. Never infer independence, zero uncertainty, or calibration from a missing field.

### Assessment

An assessment is an attributed examination of a specified property on identified record states. It retains subject bindings, selectors, procedure identity/version, dependencies, per-criterion rules/results, evidence, missing inputs, interpretations, and limitations; it is neither an observation nor an automatic publication-support grade.

The vocabulary separates analytical, numerical, empirical, and structural examinations. Mixed examinations should be separate assessment records rather than one undifferentiated “verified” result.

`MET` or `NOT_MET` requires at least one evidence reference structurally. That is necessary but insufficient: unresolved references, absent procedure evidence, unversioned criteria, or unknown examined state may prevent a justified finding; such limitations require semantic checks and scoped reporting, not automatic promotion by shape validation.

`INDETERMINATE` records an examination that cannot establish the criterion result with the available evidence. `NOT_EVALUATED` records no completed evaluation; neither becomes failure merely to finish a report. A finding with incomplete state information must not be advertised as reusable version-bound verification.

## Compatibility and review boundaries

The proposed `equation`, `assumption`, `derivation`, and `assessment` types specialize the earlier evidence-contract concepts; they do not claim to replace generic claims, observations, interpretations, or verification events. Retain original source statements and explicit links rather than silently coercing old record types into these five.

This is not a storage-schema selection, runtime implementation, or completed migration of `assess.py`. Follow the [decision checklist](../../docs/decision-checklist.md): E-02/E-03 and verification/numerical/integration choices remain open pending review.

Review the [planned cases](review-cases.md) before implementing a validator. Examples are synthetic, include no real measurement or executed check, and deliberately leave the demonstration assessment NOT_EVALUATED.
