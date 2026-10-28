# October 27, 2026 theoretical-study run

Status: Completed bounded authoring review with inspectable offline outputs. This is not an independent reproduction, a general-purpose mathematical proof engine, or a whole-paper scientific verdict.

The study is Daniele Gregoris, “Neutrino oscillations inside ultrarelativistic matter: on the role of the Tolman VI spacetime,” published October 27, 2026 in The European Physical Journal C ([publisher article](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). It was selected using the publisher's journal-publication date, not merely a news-story timestamp.

## Start here

- **Worked assessment:** [Findings, equations, numerical results, unknowns, and limitations](study-assessment.pplx.md).
- **Mapping draft:** [Criterion-to-conclusion contract](../../docs/criterion-conclusion-mappings.md) and [five explicit case mappings](mappings.json); draft declarations, not a running generic inference engine.
- **Source capture:** [Selected original publisher HTML TeX and metadata](source-extract.json), [extract lock](source-lock.json), [offline extractor](extract_source.py), and [subsequent visual PDF inspection](pdf-inspection.json).
- **Results:** [Computed values](artifacts/computed.json), [16-record evidence bundle](artifacts/evidence-bundle.json), [integrity JSON](artifacts/integrity-report.json), and [integrity Markdown](artifacts/integrity-report.md).
- **Original toolkit:** [Study Aperture record](study-record.json) and [machine-rendered report](toolkit-report.md); decisions remain unresolved.
- **Verification:** [Case execution/input/output hashes](artifacts/verification.json), [final test procedures/results](test-verification-final.json), and [authoring-only shape review](structural-review.json).
- **Correction history:** [Recorded correction](correction-record.json) and [retained first-attempt report](attempt-01-invalid-trial-references/integrity-report.json).

## Reproduce offline

From the repository root, choose a new output directory. The fixed case program uses only the standard library and executes locally authored functions, not submitted study code.

```sh
python3 experimental/scope_audit_lab/reviews/tolman-vi-2026-10-27/run_case.py \
  --output-dir /tmp/tolman-vi-study-review
python3 -m unittest discover \
  -s experimental/scope_audit_lab/reviews/tolman-vi-2026-10-27 -p test_case.py -v
python3 -m unittest discover -s experimental/scope_audit_lab/tests -v
python3 assess.py check \
  --file experimental/scope_audit_lab/reviews/tolman-vi-2026-10-27/study-record.json
python3 assess.py report \
  --file experimental/scope_audit_lab/reviews/tolman-vi-2026-10-27/study-record.json
```

The fixed verifier refuses to overwrite its output; supply a new filename to run it again. It invokes the 19 case tests, 100 checker tests, five existing toolkit self-tests, and original-toolkit record validation.

```sh
python3 experimental/scope_audit_lab/reviews/tolman-vi-2026-10-27/verify_review.py \
  --output test-verification-rerun.json
```

The original HTML is not required for rerunning the calculations against the captured extract. To make a new extraction, first acquire the publisher HTML separately, then pass that local file and its recorded acquisition timestamp to `extract_source.py`; a changed extract requires explicit reinspection/rebinding, not an automatic lock update.

The optional shape review used separately installed `jsonschema`/`referencing` authoring packages, registered both local frozen schemas, and did not retrieve remote schemas. Those dependencies are not part of the offline runtime and structural acceptance is not scientific validation.

## What was and was not established

An exact coefficient identity passes, equation 12 and equation 13 agree at three samples, and equation 8's literal flavor difference and equation 12 have opposite signs at those samples. This is a candidate internal sign discrepancy, not automatic refutation of the paper's proposed physical interpretation.

The corrected bundle has zero integrity ERROR findings and 19 UNKNOWN findings, preserving unresolved source/trial references. There are no registered anchor applications or generic inference-engine results in this case; neither missing coverage nor missing empirical observations is silently represented as a negative result.

The first attempt's malformed trial references were repaired without changing calculations; its original artifacts remain inspectable. A second HTML-only stage is also retained before the final PDF-cross-checked case-review-2 run; scientific validity, full baseline conformance, and Prototype 0.1 compatibility remain unestablished, with compatibility explicitly UNKNOWN and voice DEFERRED.
