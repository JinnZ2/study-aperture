# Offline integrity checker verification

Status: Executed synthetic verification of the narrow checker, version 0.1.0. This implementation version is not Prototype 0.1 and establishes no compatibility with that uninspected prototype.

## Recorded results

- **Integrity tests:** All 57 stdlib tests passed; [tests.log](artifacts/tests.log) retains their names and output, and [verification.json](artifacts/verification.json) records individual outcomes and exact examined source hashes.
- **Existing-toolkit regressions:** All five fixed `selftest` commands returned exit code 0 and `SELFTEST OK`; their commands and captured outputs are preserved in the verification record.
- **Example CLI:** Inspected 14 records, 35 reference occurrences, seven version bindings, and one anchor application. It returned exit code 1 with `INTEGRITY_GAPS_RECORDED`, as expected for incomplete evidence.
- **Frozen baseline:** Requirement specification 0.2, evidence schema draft 0.1, and its original examples retained their recorded hashes.

The [example JSON report](artifacts/example-report.json) contains 16 unknown findings and no integrity errors: ten unresolved source-reference occurrences, one blocked binding for the deliberately absent angle input, and five unevaluated anchor conditions. The [Markdown rendering](artifacts/example-report.md) shows complete condition-ID coverage without presenting those five conditions as satisfied.

Source references are counted by occurrence, not by unique source, and none was fetched. A source missing from the supplied snapshot is not thereby false or nonexistent elsewhere.

## Reproduce and inspect

Follow the [checker guide](../../docs/offline-integrity-checker.md) for read-only CLI use and test commands. The fixed [verification runner](run_verification.py) creates artifacts only in a new directory and executes repository-owned test commands, not code named in evidence records.

The verification artifact includes hashes of the implementation, tests, runner, example bundle, schema, and output reports. Those hashes bind this run to inspected bytes; they do not authenticate the author, establish source validity, or prove complete test coverage.

## Deliberate limits

This is not execution of the complete baseline acceptance matrix, physical-law verification, empirical reproduction, a ledger implementation, or a proof of correctness. General structural validation, assessment relevance, artifact contents, dependency completeness, and relevance of changes remain outside this checker.

Prototype 0.1 compatibility remains UNKNOWN and voice remains DEFERRED. No evidence record was rewritten, no scientific conclusion was selected, and no open design gate was silently closed.
