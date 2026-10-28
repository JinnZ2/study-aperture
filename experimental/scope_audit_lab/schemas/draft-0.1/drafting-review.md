# Drafting-time structural review

Status: Limited authoring check performed on the draft artifacts identified below. This is not execution of the Scope Audit Lab acceptance matrix, implementation of an audit engine, formal verification, independent replication, or empirical validation.

## Examined artifacts and method

| Artifact | SHA-256 of examined bytes |
|---|---|
| `evidence.schema.json` | `db9d9902bd943e80cdccc660b22dbb12192732adc5bfcd5aecb0c4f801975775` |
| `../../examples/schema-draft-0.1/records.json` | `4d152cf48c629ff0e96857fe40716844669ef445f6f6d472fcac57c5192e9f90` |

The authoring environment used `jsonschema` 4.26.0 with `Draft202012Validator`, plus explicit `FormatChecker` and `rfc3339-validator` 0.1.4 support for date-time checks. These packages were installed in a temporary reviewer directory outside the repository; they are not a runtime dependency, selected lab test framework, or permission to install dependencies during an audit.

The schema passed the reviewer's Draft 2020-12 meta-schema check, and the five individual records in the example container were accepted structurally. The container itself is descriptive packaging, not an instance of one of the five schemas.

The authoring checks also parsed the JSON strictly, resolved local schema-definition pointers, checked unique example record IDs, matched their referenced example types, and checked that derivation step dependencies point to earlier unique steps. These checks concern this fixture only; no reusable lab resolver or semantic validator is implemented.

## Focused probes and observed results

Each probe used a copy of the relevant example, changing only the described field(s). No fixture was promoted to a real observation or completed assessment.

| Probe | Observed structural result |
|---|---|
| Delete required `producer` from equation record | Rejected |
| Relabel equation record as observation without changing payload | Rejected |
| Replace synthetic observation value with PRESENT numeric zero and JSON-number encoding | Accepted |
| Supply MISSING value object with an extra `value: 0` | Rejected |
| Supply present numeric string `"0"` | Rejected |
| Supply present numeric null | Rejected |
| Change schema version to an unknown value | Rejected as a draft-0.1 instance |
| Add top-level `verified: true` | Rejected |
| Change equation's assumption reference expected type to equation | Rejected |
| Mark criterion MET with no evidence references | Rejected |
| Mark criterion NOT_MET with no evidence references | Rejected |
| Change illustrative assessment to INDETERMINATE | Accepted |
| Supply a PRESENT timestamp with invalid date-time text | Rejected with date-time format checking enabled |

All thirteen final probes matched the stated structural expectations. This is a small targeted review, not exhaustive schema testing or conformance to all cases in [review-cases.md](review-cases.md).

## A review-environment failure and a demonstrated schema boundary

The initial review accepted the intentionally invalid timestamp because optional date-time checking support was absent despite a `FormatChecker` object being supplied. After adding the temporary reviewer support, checking explicitly that `"not-a-date"` fails the format check, and rerunning the probes, the timestamp was rejected; an implementation must not assume a declared format is enforced merely because its validator reports success.

A separate boundary probe changed an assessment's subject reference to an absent target while labeling it RESOLVED. The record remained structurally acceptable, as expected: JSON Schema does not resolve the evidence graph or authenticate the assertion. A future semantic resolver must report that discrepancy.

The schema and examples were authored and reviewed in the same workstream. Structural agreement between them is not independent evidence of their scientific adequacy; no mathematical claims, physical measurements, or proof procedures were validated by these probes.

## Reproduction outline

Use an explicitly approved authoring-only environment with the reviewer versions above. Load the schema and example JSON locally; call `Draft202012Validator.check_schema(schema)`, construct a validator with an active date-time format checker, and validate each member of `records` individually.

Assert that the date-time checker rejects `"not-a-date"` before relying on its timestamp result. Deep-copy the relevant record for each mutation in the table and compare acceptance against the listed expectation; do not modify the archived example records or their outcome fields.

Retain inspected file hashes, reviewer identity/version, results, and limitations for any rerun. Differences in files or reviewer configuration constitute a different examined state, not automatic reuse of these results.
