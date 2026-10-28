# Tolman VI phase-to-probability follow-up

Status: Completed bounded analytical/numerical authoring trace with offline reproduction artifacts. It does not establish a corrected physical prediction, experimental detectability, independent scientific reproduction, or a whole-paper verdict.

This follows the [original scoped assessment](../tolman-vi-2026-10-27/README.md) without changing its records or artifacts. The studied journal article was published October 27, 2026, while its preprint v1 was submitted October 8 ([publisher](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w), [preprint history](https://arxiv.org/abs/2610.11319)).

## Findings and artifacts

- **Analytical trace:** [Phase conventions, interference, averaging, numerical examples, and limits](phase-trace.md).
- **Restricted result:** A complete phase reversal is invariant in Eq35, but a partial eikonal reversal with a fixed spin contribution generally is not. At full phase averaging, the retained mixing factor gives \(1-\tfrac12\sin^2(2\theta)\), not universally one-half.
- **Source capture:** [Original selected journal/preprint TeX](sources.json), [source/parent-code lock](source-lock.json), and [attributed lineage/PDF inspection](source-review.json).
- **Computed outputs:** [Conditional probability branches and averaging counterexamples](artifacts/computed.json).
- **Evidence records:** [21-record bundle](artifacts/evidence-bundle.json), [integrity JSON](artifacts/integrity-report.json), and [integrity Markdown](artifacts/integrity-report.md).
- **Draft implications:** [Five explicit scoped mappings](mappings.json), not a generic inference executor or a declaration of physical support.
- **Verification:** [Run/input/output hashes](artifacts/verification.json), [tests and isolated reproduction](test-verification.json), and [optional authoring-only shape review](structural-review.json).

The integrity result has zero ERROR findings and 24 UNKNOWN findings, chiefly unresolved source/trial registry references. There are no registered anchor applications in this trace, and full physical unit/coordinate normalization remains unestablished.

## Reproduce locally without network

From the repository root, choose a new output directory. The runtime uses the Python standard library, requires the bundled source capture and frozen earlier-case helper, and neither fetches web content nor executes code from the publication.

```sh
python3 -I experimental/scope_audit_lab/reviews/tolman-vi-phase-trace-0.1/run_trace.py \
  --output-dir /tmp/tolman-phase-trace-review
python3 -m unittest discover \
  -s experimental/scope_audit_lab/reviews/tolman-vi-phase-trace-0.1 -p test_trace.py -v
```

The fixed verifier runs the 27 new trace tests, unchanged 19 original case tests, 100 checker tests, five toolkit self-test commands, and a fresh isolated rerun. It checks deterministic artifacts byte-for-byte, records code/input/output hashes, and refuses to overwrite its verification file.

```sh
python3 experimental/scope_audit_lab/reviews/tolman-vi-phase-trace-0.1/verify_trace.py \
  --output test-verification-rerun.json
```

For a new source capture, use `capture_sources.py` with already acquired publisher and versioned preprint HTML files. A changed source/helper digest requires explicit reinspection and rebinding; updating the lock merely to make a check pass is not verification.

The optional shape review uses separate authoring-only `jsonschema`/`referencing` packages with both local frozen schemas, not runtime dependencies. Neither that structural check nor successful script execution validates the physical content.

The initial missing-derivation-link package and failed shape review remain preserved under `attempt-01-missing-derivation-links/`, with a [correction record](correction-record.json). The final procedure is versioned phase-trace-0.1.1; supplying explicit derivation records does not silently establish their scientific validity.

## Interpretation boundary

Holding the published spin term fixed while substituting the literal Eq8 phase is an explicitly conditional branch, not an author-approved correction. Both spin-index orientations are retained as sensitivity choices, and an ideal response-kernel counterexample is not a measured detector model.

The work still needs a consistent first-principles phase/spin derivation, valid near-singularity approximation control, a specified finite response/ensemble, and physical observational evidence before an empirical signature is established. Prototype 0.1 compatibility remains UNKNOWN, voice is DEFERRED, and full baseline conformance is not claimed.
