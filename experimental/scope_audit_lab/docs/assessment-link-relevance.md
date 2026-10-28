# Assessment-to-subject relevance checks

Status: Implemented in offline integrity checker 0.2.0, with synthetic adversarial tests. “Relevance” here means literal subject/version/selector linkage, not a determination that an assessment's free-form property, evidence, or procedure supports a scientific conclusion.

The checker remains read-only and standard-library-only. It does not promote a recorded conclusion, modify a criterion outcome, fetch references, execute submitted code, or treat a confident assessment as an observation.

## What changed

A reference can resolve to a real assessment and still be unrelated to the record using it. The checker now reports that distinction in `assessment_link_relevance`, separately from ordinary reference resolution, version bindings, and anchor-condition coverage.

For each assessment link, it identifies the owning record, resolves the referenced assessment, and examines its explicit `subjects`. A candidate must name the owning record's exact ID and declared type, and its examined version must match the owner's present version exactly.

An assessment about a model used by an anchor application is not automatically an assessment of that application or its verdict. Such a link is reported as `RELATED_SUBJECT_ONLY`, not silently inherited as support and not declared scientifically irrelevant.

## Literal selector policy

The following are conservative read-time checker conventions, not revisions to the frozen schemas' free-form selector field. No aliases, natural-language equivalence, JSON Pointer translation, whole-record implication, or semantic similarity are inferred.

| Link context | Assessment must explicitly name | Required selector |
|---|---|---|
| Record-level `payload.assessment_refs` | Owning record and version | None for the record-identity check; any supplied selector is retained |
| Top-level `payload.evidence_refs` containing assessment links | Owning record and version | None for the record-identity check |
| Application `applicability_assessment_refs` | Application record and version, not merely its model | `payload.applicability_status` |
| Application `comparison_assessment_refs` | Application record and version | `payload.comparison_status` |
| Structured uncertainty `assessment_refs` | Owning record and version | `payload.uncertainty` |
| A uniquely identified derivation step's `assessment_refs` | Derivation record and version | `step_id=<exact step ID>` |
| An application condition's assessment-typed `evidence_refs` | Application record and version | `condition_id=<exact requirement ID>` |
| An assessment criterion's assessment-typed `evidence_refs` | Owning assessment record and version | `criterion_id=<exact criterion ID>` |
| A calculation prerequisite's assessment-typed `evidence_refs` | Calculation record and version | `requirement_id=<exact requirement ID>` |

For example, this subject binding targets an application's comparison status. It is a binding fragment, not a complete assessment:

```json
{
  "subject": {
    "record_id": "lab:application",
    "expected_type": "anchor_application",
    "resolution": "NOT_CHECKED"
  },
  "examined_version": {"status": "PRESENT", "value": "v1"},
  "examined_state_artifact_refs": [],
  "selector": {"status": "PRESENT", "value": "payload.comparison_status"}
}
```

`payload.applicability_status` cannot substitute for that selector. A whole-record selector or `/payload/comparison_status` is not automatically considered equivalent under this literal convention; a mismatch is a checker-policy mismatch, not proof that the source's scientific reasoning is false.

## Links covered and distinctions preserved

Dedicated assessment-reference fields are inspected, including malformed entries. Generic `evidence_refs` are also inspected when the reference declares an assessment type or resolves to an assessment; ordinary observation/source links are not silently recast as assessment endorsements.

- **METADATA_MATCH_ONLY:** Explicit subject identity, declared version, and any required selector match. This is not a support verdict or complete schema validation.
- **UNRELATED_SUBJECT:** The assessment does not explicitly examine the owning record. Its existence and confident wording cannot fill that link.
- **RELATED_SUBJECT_ONLY:** A model/subject belonging to the application is named, but the application/status is not explicitly examined; relevance remains unresolved.
- **VERSION_MISMATCH / VERSION_UNKNOWN:** A different or missing examined state prevents an established same-version link.
- **SELECTOR_MISMATCH / SELECTOR_UNKNOWN:** The required field/condition/step is different or not explicitly specified.
- **CONFLICTING_SUBJECT_BINDINGS:** Matching bindings disagree on examined version; the checker does not select the convenient one.
- **CONTEXT_UNESTABLISHED:** No explicit literal policy exists, or a referenced step/condition/criterion identifier is ambiguous. It does not guess the intended scope.
- **Blocked or malformed link:** Missing, ambiguous, opaque, mistyped, or malformed assessment/subject records remain visible.
- **SELF_REFERENCE:** An assessment cannot independently substantiate itself. Other graph cycles are not recursively treated as proofs.

Unrelated and relevant links can coexist; a good link does not conceal a bad one. Repeated subject bindings or multiple references do not accumulate confidence, and an assessment of another assessment does not transitively become an assessment of the original subject.

## Outcomes and scientific limits

The report retains the assessment's recorded property and criterion outcomes. Missing criteria, malformed outcomes, and `NOT_EVALUATED`/`INDETERMINATE` outcomes produce explicit diagnostics rather than manufactured completion.

`MET` does not automatically mean the linked conclusion is correct, and `NOT_MET` does not automatically mean that conclusion is false: the criterion might concern a different property or test a discrepancy. No free-form criterion-to-verdict mapping is inferred.

When a definitive application status or criterion outcome cites matching assessment metadata, the checker still records `ASSESSMENT_VERDICT_MAPPING_UNESTABLISHED`. A future typed property/criterion mapping or explicitly authorized examination is needed to establish more than the metadata relationship.

Every link report preserves `property_alignment_established`, `verdict_mapping_established`, and `scientific_support_established` as false. An assessment can name the correct subject and selector while examining an unsuitable property; this checker does not resolve that semantic question or verify its procedure.

## Run and inspect

The CLI is unchanged; follow the [offline checker guide](offline-integrity-checker.md). The new synthetic demonstration uses a different namespace and preserves the original examples:

```sh
python3 experimental/scope_audit_lab/integrity_checker.py \
  experimental/scope_audit_lab/examples/integrity-relevance-0.2/records.json \
  --format markdown --output assessment-link-report.md
```

Expected exit code: 1, because the fixture intentionally contains an unrelated assessment, a wrong-field assessment link, and unresolved evidence. Its third assessment relationship matches metadata but has no established scientific support.

The [verification record](../reviews/integrity-checker-0.2/artifacts/verification.json), [JSON report](../reviews/integrity-checker-0.2/artifacts/relevance-report.json), and [Markdown report](../reviews/integrity-checker-0.2/artifacts/relevance-report.md) retain inspected inputs, exact code hashes, test outcomes, and limitations. Earlier 0.1.0 review artifacts are historical records and are not overwritten.

Checker version 0.2.0, evidence schema draft 0.2, baseline requirements specification 0.2, and Prototype 0.1 are separate versioned objects. Prototype compatibility remains UNKNOWN, voice remains DEFERRED, and full baseline acceptance-matrix conformance is not established.
