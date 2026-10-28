# Draft 0.2 authoring review

Status: Executed structural review of a proposed additive schema, not implementation of Scope Audit Lab or its acceptance matrix. Read the [schema guide](../../schemas/draft-0.2/README.md) for the proposed workflow and scope constraints.

## Examined artifacts and results

- **Schemas:** The frozen draft 0.1 and the proposed draft 0.2 extension schema both passed JSON Schema Draft 2020-12 meta-schema checks in the authoring reviewer.
- **Examples:** All 14 records in the mixed-version synthetic bundle and the original five records were structurally accepted. None is an empirical measurement, and the example applicability/comparison remains unknown/not evaluated.
- **Adversarial probes:** All 31 probes matched their declared structural expectations, including explicit cases that demonstrate semantic checks were not performed.
- **Offline behavior:** Both schema URNs were registered locally and unregistered retrieval was explicitly blocked. The reviewer used no runtime/project dependency installation or remote schema fetch.
- **Original artifacts:** The baseline requirements, draft 0.1 schema, and original example hashes remain respectively `50a1bf3d5b556cdb08c4367b5e442cdd512b7f2fbda9498383645b4c8e57a10d`, `db9d9902bd943e80cdccc660b22dbb12192732adc5bfcd5aecb0c4f801975775`, and `4d152cf48c629ff0e96857fe40716844669ef445f6f6d472fcac57c5192e9f90`.

The [machine-readable review](review-results.json) preserves exact procedure/schema/example hashes, reviewer versions, input records, expected acceptance, observed acceptance, and error paths. This local record is authored evidence of the reported review, not an independently authenticated attestation.

The original `assess.py selftest` and all four vendored-script selftests also returned `SELFTEST OK`. They exercise the existing parent toolkit, not the proposed lab components or physical reference laws.

## What the probes establish

The schema rejects zero dimension-exponent denominators, wrong dimension-vector lengths, scalar/vector shape contradictions, zero/negative unit scales in the declared convention, and negative standard uncertainty. It also rejects a present result for an unexecuted calculation, a missing definition for an explicitly chosen denominator extension, unsupported definitive labels without assessment references, and a law-consistency verdict when applicability is unknown or out of scope.

Missing dimensions, quantity kinds, versions, and numerical inputs remain representable. Explicit numerical zero remains a value, including a zero tolerance or uncertainty; representation of zero uncertainty does not authorize division by it.

These are structural statements only. No unit algebra, physical law, initial condition, theorem, numerical approximation, or uncertainty estimate was independently validated.

## Deliberately exposed semantic gaps

- **D02-11, completion:** A present result accompanied by a completion assertion can satisfy the schema even without execution artifacts.
- **D02-19, relevance:** Unresolved or unrelated assessment references can accompany positive applicability and comparison assertions.
- **D02-20, coverage:** Omitting an anchor condition from an application requires cross-record detection, not just shape checking.
- **D02-21, missing sources:** An unsourced reference formulation remains recordable; its name is not evidence.
- **D02-22, inventories:** A declared-complete balance inventory is not physically established by a schema check.
- **D02-31, citations:** Condition citation IDs need a semantic integrity check against the anchor's source entries.

Those acceptance results are documented limitations, not failing empirical tests that were repaired by adjusting the interpretation. Any future reporter must preserve the distinction between a recorded assertion and a supported assessment.

## Reproduction

The fixture generator is standard-library-only and prints JSON:

```sh
python3 experimental/scope_audit_lab/reviews/draft-0.2/build_examples.py
```

The optional structural reviewer requires an isolated authoring environment with `jsonschema`, `referencing`, and `rfc3339-validator`. The exact installed reviewer versions are recorded in the result artifact, and working date-time validation is explicitly checked before review.

```sh
python3 experimental/scope_audit_lab/reviews/draft-0.2/review_schema.py
```

In the authoring environment, the dependencies were loaded from a temporary directory outside the repository. No requirements/dependency file, runtime engine, automated migration, or generic semantic validator was added.

## Remaining decisions

The unit/dimension encoding and six new supporting types are proposals, not silently approved interface commitments. Numerical representation, general uncertainty treatment, assumption propagation, and detailed semantic validation policies still need explicit review.

Prototype 0.1 compatibility remains UNKNOWN and voice remains DEFERRED. Passing these authoring checks establishes only the reported structural properties, not correctness of the examined physics or full requirements-specification 0.2 conformance.
