# Offline integrity checker 0.2.0 verification

Status: The declared synthetic checker tests and existing toolkit self-tests passed in the recorded environment. This establishes the recorded procedure's results for the examined code and inputs, not scientific validity, independent reproduction, or complete requirements conformance.

The user authorized assessment-to-subject relevance checks after the earlier offline checker. This revision implements literal linkage policies without treating that authorization as adoption of all proposed schema contracts or closure of other design questions.

## Recorded results

- **Checker tests:** All 100 passed, including 43 new assessment-link tests and the preserved 57-test suite.
- **Toolkit regressions:** Five existing fixed self-test commands completed with exit code zero; their outputs are retained.
- **Original synthetic bundle:** Still has 14 records, zero assessment links, zero ERROR findings, and 16 UNKNOWN findings. Missing evidence was not repaired by inventing sources or measurements.
- **New synthetic bundle:** Has 15 records, 40 reference occurrences, eight declared-version bindings, and three assessment links. It intentionally produces two ERROR findings and 17 UNKNOWN findings, with CLI exit code 1.
- **Explicit linkage cases:** The residual calculation has `METADATA_MATCH_ONLY`, the balance equation has `UNRELATED_SUBJECT`, and the application's comparison link has `SELECTOR_MISMATCH`.
- **No support promotion:** Property alignment, criterion-to-verdict mapping, and scientific support remain unestablished for all three links.
- **Preserved originals:** Recorded hashes match the baseline requirements, draft-0.1 schema, and both earlier example bundles. Old 0.1.0 verification artifacts are retained.

See the [recorded procedure and test outcomes](artifacts/verification.json), [individual test log](artifacts/tests.log), [new JSON report](artifacts/relevance-report.json), [new Markdown report](artifacts/relevance-report.md), and [original-bundle report under the current checker](artifacts/base-report.json). The verification record contains the examined implementation/test/input hashes and the hashes of generated reports.

## Reproduce offline

Run from the repository root, choosing a new output directory. Existing output directories are refused to avoid silently overwriting verification evidence.

```sh
python3 experimental/scope_audit_lab/reviews/integrity-checker-0.2/run_verification.py \
  --artifact-dir /tmp/study-aperture-integrity-0.2-review
```

This authoring verification runner invokes fixed repository tests and checker commands. It is separate from the runtime checker, which never executes submitted evidence or fetches network resources.

The [fixture builder](build_relevance_example.py) transforms the original example into a new `relevance-demo:` namespace and emits JSON to stdout. It does not modify the original bundle or obtain empirical measurements.

```sh
python3 experimental/scope_audit_lab/reviews/integrity-checker-0.2/build_relevance_example.py
```

## Interpretation limits

The [literal selector policy](../../docs/assessment-link-relevance.md) identifies wrong subjects, wrong/missing declared versions, and wrong/missing field/step/condition selectors. It does not establish that an assessment actually examined its claimed property, used an adequate procedure, or justified a verdict.

The implementation and tests were authored in the same development process, not independently audited. Passing these tests cannot establish general robustness, physical-law applicability, dimensional correctness, mathematical proof, empirical agreement, or the truth of recorded `MET` outcomes.

Voice is DEFERRED, Prototype 0.1 compatibility is UNKNOWN, and full baseline acceptance-matrix conformance remains unestablished. The original [0.1.0 review](../integrity-checker-0.1/README.md) is a historical record for the implementation published at commit `02178e463dafa818a21e0ac1abc075fd3c026d06`, not a verification of the current checker.
