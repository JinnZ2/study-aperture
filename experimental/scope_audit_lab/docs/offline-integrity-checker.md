# Offline evidence-integrity checker

Status: Implemented narrow checker, version 0.1.0, with synthetic adversarial tests. This is not a full schema validator, a physics assessor, a ledger implementation, or conformance to the complete requirements specification.

The [implementation](../integrity_checker.py) uses Python's standard library and operates only on explicitly supplied local JSON bundles. It does not open cited URLs or artifact paths, execute submitted code, install dependencies, or modify input records.

## Run it

From the repository root:

```sh
python3 experimental/scope_audit_lab/integrity_checker.py \
  experimental/scope_audit_lab/examples/schema-draft-0.2/records.json
```

For a readable report in a new file:

```sh
python3 experimental/scope_audit_lab/integrity_checker.py \
  experimental/scope_audit_lab/examples/schema-draft-0.2/records.json \
  --format markdown --output integrity-report.md
```

Multiple positional bundles form one explicitly supplied snapshot. No directory scanning, locator following, implicit import, remote lookup, or “latest version” selection occurs.

An input is either an array of records or an object containing a `records` array. Each file is limited to 16 MiB; duplicate JSON object members, malformed JSON, non-finite numbers, and numeric overflow are rejected instead of being silently normalized.

### Exit codes

- **0:** No gaps detected within the implemented integrity checks. This does not establish structural validity, scientific correctness, complete evidence, or satisfied physical conditions.
- **1:** Inspection completed and recorded integrity gaps or unknowns. The deliberately incomplete example bundle is expected to return 1, not 0.
- **2:** Input/output could not be processed, including an existing output path. No existing report or input file is overwritten.

The output identifies the checker version and the SHA-256 of each input file. JSON is the detailed machine-readable form; Markdown presents references, exact version bindings, condition coverage, recorded outcomes, findings, and verification limits.

## Reference resolution

Index records by exact ID and compare each reference's expected type with its target's declared type. Recorded `RESOLVED` assertions do not create targets or override the supplied snapshot.

- **RESOLVED:** One unambiguous target exists, its declared type matches, and its type/schema/version contract is among the supported draft contracts. This is not JSON Schema validation or evidence authentication.
- **UNRESOLVED:** No target is present in the supplied snapshot. The target may exist elsewhere; missing it here does not establish falsehood or nonexistence.
- **TYPE_MISMATCH:** A target exists but declares a different type.
- **AMBIGUOUS:** Different records share the same ID. Neither the newest-looking version nor the last occurrence is selected.
- **OPAQUE_TARGET:** The target exists and declares the expected type, but uses an unsupported contract/type. Preserve it as opaque rather than infer validity.
- **MALFORMED / ABSENT:** A malformed reference is distinguished from an explicitly missing/invalid/not-applicable input binding. Neither becomes a numerical zero.

Identical reimports are reported informationally and their input occurrences are retained. Identity here uses the exact parsed record serialized with sorted keys, not wording similarity, case folding, number conversion, authenticated origin, or raw-file byte identity; the raw input files have their own hashes.

The checker recognizes reference-shaped objects containing `expected_type` or both `record_id` and `resolution`, including malformed ones. In supported contracts it also inspects declared reference slots and lists, so an incomplete object or non-object cannot escape inspection merely by omitting the usual keys; explicitly typed slots additionally check the recorded expected type.

It examines a finite JSON tree without recursively following graph edges, so reference cycles do not imply evidentiary support or cause infinite graph traversal. Unsupported contracts remain opaque except for signature-based reference inspection.

Supported contracts are the five original record types in evidence schema draft 0.1 and the six extension types in draft 0.2. Source/artifact/verification registries not yet given supported schemas remain opaque if supplied; citation IDs are additionally checked locally against each anchor's own citation entries, without fetching their locators.

## Exact declared-version bindings

Bindings are checked for assessment/application subjects, calculation/approximation inputs, and an anchor application's anchor. These are the explicit binding locations in the two supported draft contracts.

- **SAME_DECLARED_VERSION:** Both present version strings match exactly. This does not prove equal contents or unchanged physical conditions.
- **DIFFERENT_DECLARED_VERSION:** The examined version and supplied target version differ. This is a binding discrepancy, not proof of a relevant subsequent change or scientific failure.
- **VERSION_UNKNOWN:** Either version is missing, invalid, inapplicable, or malformed. No version is inferred from filenames, artifact names, timestamps, or neighboring records.
- **BLOCKED_REFERENCE:** The target is absent, unresolved, ambiguous, mismatched, malformed, or opaque; comparison cannot establish a bound version.

The checker does not order version strings, strip whitespace, interpret semantic versions, infer a change's relevance, inspect artifact contents, or mark evidence stale merely because it is old. Changes made under an unchanged version identifier are not detected except where the implemented content comparisons, such as exact condition wording, expose them.

## Anchor-condition coverage

Resolve the application's anchor and compare the available anchor's condition IDs against the application's check IDs. Report missing checks, extra IDs, duplicates, malformed fields, changed requirement wording, unsupported outcome values, missing evidence references for definitive outcomes, and explicit unresolved-condition notes.

Identity coverage is `COMPLETE`, `GAPS`, `INVALID`, or `UNAVAILABLE`. Coverage for the bound version remains `UNESTABLISHED` unless the exact anchor-version binding matches; the checker may still show the available target's conditions to explain the discrepancy.

**Complete coverage is not satisfaction.** A check for every condition can still record `NOT_EVALUATED`, `INDETERMINATE`, or `NOT_MET`; these remain visible and no outcome is promoted. Resolved evidence links establish neither relevance nor truth of a recorded `MET` assertion.

Recorded positive applicability/comparison statuses are flagged when conditions are missing, version-unbound, unresolved, unevaluated, or contradictory. Definitive status fields need assessment references, but relevance and sufficiency of a resolved assessment are not established by this checker.

An out-of-scope or unknown application does not authorize a definitive law-comparison verdict. Observations, numerical differences, unsuccessful criteria, and competing explanations remain untouched in their own input records.

## Tests and inspectable artifacts

Run the standard-library test suite:

```sh
python3 -m unittest discover -s experimental/scope_audit_lab/tests -v
```

The [verification record](../reviews/integrity-checker-0.1/artifacts/verification.json) records individual test outcomes, procedure/input hashes, existing-toolkit regression outputs, and preserved baseline hashes. The [example JSON report](../reviews/integrity-checker-0.1/artifacts/example-report.json) and [Markdown report](../reviews/integrity-checker-0.1/artifacts/example-report.md) retain the synthetic bundle's genuine gaps.

To reproduce the fixed tests and example reports into a new directory:

```sh
python3 experimental/scope_audit_lab/reviews/integrity-checker-0.1/run_verification.py \
  --artifact-dir /tmp/study-aperture-integrity-review-new
```

Unlike the read-only checker, this separately invoked authoring runner creates a new artifact directory and executes the repository's explicitly named tests. It does not run commands supplied by an audited record.

## Limits and acceptance scope

These tests demonstrate the specified narrow behavior on synthetic cases. They are not independent evidence of complete correctness and do not close the full baseline acceptance matrix.

No full JSON Schema validation, assumption propagation, assessment relevance proof, source authenticity check, artifact-byte verification, append-only storage, chronology/relevant-change analysis, dimension engine, numerical solver, or physical-law validity test is implemented. A report can find no gaps within these checks while important evidence remains outside the checked scope.

The checker does not mutate a claim's support, rewrite reference assertions, choose between conflicting records, or discard competing interpretations. Prototype 0.1 compatibility remains UNKNOWN, voice remains DEFERRED, and full requirements-specification 0.2 conformance remains unestablished.
