Status: Implemented isolated offline review APIs with CONSTRUCTED unit-test fixtures. No real human reviews, authenticated reviewer independence, ground truth, model benchmark, calibrated confidence, or aggregate reliability score are established.

# Staged reference and output review

`review.py` uses only Python 3.11+ standard-library facilities. It does not invoke models, execute document content, access the network, modify core records, or turn machine checks into interpretive authority. Source-grounded observations, reviewer assessments, original captures, mechanical checks, and adjudicator decisions remain distinct records.

## Packet API and distribution

```python
make_review_packets(cases, captures, output_dir, phase="reference", *, source_root=None)
```

`source_root` is the **battery directory**, not its `sources/` subdirectory. Each available source's relative POSIX `path` is resolved only under this explicit root. Absolute paths, traversal, escaping symlinks, non-UTF-8 bytes, and source-hash mismatches are rejected. Source version must be explicit text. An unavailable source must have hash `UNDECLARED`; its path is never opened, and the packet records `available: false, text: null`. Missing material is not a negative finding or corruption. All validation and reads precede directory creation. Any existing output directory, including an empty directory or a dangling symlink, is refused. Writes use exclusive file creation.

Reference packets contain exact source-text snapshots with local source aliases, source hashes/versions/availability, and `assessment_target`: the supplied `case['claim']` in unaltered wording. This target is input material, not an answer key. They never include assessor output, source observations, family, test purpose, expected observations/labels, comparison specifications, perturbation dependencies, or other reviewers. Reference packet generation does not consult assessor findings.

Output packets contain the same source material and assessment target, plus an anonymous parsed-output view and anonymous raw-output copy. A capture can provide original raw text through its optional `raw_text` field (`raw` is an alias). If `raw_sha256` is supplied, it is checked against strict UTF-8 encoding of that text. The capture contract's hash alone cannot reconstruct raw text: absent text is explicitly `NOT_PROVIDED`, never regenerated from parsed output and mislabeled raw. Parent CLI should read already hash-verified `raw.bin` and attach its strict UTF-8 decoded text. Non-UTF-8 raw bytes cannot be represented by this optional text API; they remain preserved separately by the harness.

The pilot deliberately supports **supplied case sources only** for output review. Any nonempty `capture.provenance.retrieved_material` causes an explicit `Unsupported staged retrieval-review` error before packet creation. Retrieval review needs a later interface for explicit hash-verified retrieved-source snapshots and consistent aliases; it must not silently omit evidence used by the assessor. Source-only reference packets remain available because they expose no assessor retrieval record.

Packet IDs and pending review IDs are opaque random identifiers; order is randomized independently for each generation. Source IDs become local `source-01`, `source-02`, etc. Packet identifiers are stable within the generated records but intentionally not reproducible across generations. The coordinator mapping retains original case/variant/run identifiers, source-alias mapping, original case, and original capture. It is written separately to `coordinator/mapping.json`; the directory is created with mode `0700`. This is a **distribution boundary, not proof of secrecy**. Share only `reviewer/`, never the complete bundle or coordinator mapping. Reviewers of the same packet may receive separate copies of its template but must assign distinct `review_id` values when returning their independently completed records.

### Blindness limitations and transformations

Known structured coordinator keys are removed recursively from displayed parsed/JSON raw output, including run/case/variant identifiers, model metadata, observations, expected-result keys, comparison specifications, mechanical checks, and reviewer/adjudication records. `expected_*` keys are suppressed. Distinctive model names/IDs and run/case/source identities are token-redacted in output text, not matched as arbitrary substrings inside larger words or IDs. Generic versions such as `"1"`, sentinels such as `UNDECLARED`, and generic variant names such as `base` are not global identity tokens. Structured `source_id` references are always aliased exactly, including generic source IDs. Redaction that would create duplicate object keys is rejected rather than silently overwriting output data.

Exact source snapshots and the target claim are **never secretly redacted**, because that would alter evidence locations and wording. A distinctive known model/run identity found as a token in those materials causes output packet generation to refuse unsafe blinding. Generic model-version/source-version `1` and numeral `10` do not trigger refusal or quotation rewriting. The raw-output display identifies its transformation as an anonymized copy, not byte-identical original evidence. Original captures remain coordinator-only. If raw output is unparseable, it remains anonymous display text; if it contains recognizable coordinator metadata keys, it is explicitly `WITHHELD_FOR_BLINDNESS` instead of risking answer-key leakage. Duplicate-key/nonfinite raw JSON is never accepted as a parsed reference object; original malformed raw may remain display data, not executable data.

These safeguards do not mechanically prove blindness. Writing style, publicly known sources, source versions, uncontrolled prose, undisclosed identities, or designed source conditions can still reveal origin or permit inference. Coordinators must screen packet content and verify staging and distribution operationally. A schema-valid declaration is not authenticated proof of human participation, expertise, access, blindness, independence, evidence fidelity, or correctness.

## Pending and completed review records

`validate_review(record) -> list[str]` checks structural record requirements without assigning truth. JSON object duplicates must be rejected by the caller's strict loader before passing an in-memory dictionary; Python dictionaries cannot recover duplicate input keys. Non-JSON values and nonfinite numbers are rejected here. Case/variant/capture identifiers, review/packet/failure identifiers, and measurement names use a bounded filename-independent stable-ID vocabulary. Duplicated case/variant, capture, source, review, failure, or same-packet/same-phase reviewer identities are rejected at the applicable API boundary.

Generated records use schema `assessor-reliability/review/1`, status `PENDING`, no identity or invented expertise, `assessment: null`, empty evidence/uncertainty/disagreement/failure lists, and `NOT_ASSESSED` measurements. Blindness/independence declarations remain `UNKNOWN`, with `cannot_mechanically_prove: true`. These are task templates, not provided reviewer records, and summaries explicitly exclude them from completed-review denominators. A pending template that claims a reviewer identity or completed finding is invalid.

A completed record requires:

- `review_id`, `packet_id`, `phase` (`reference` or `output`), and status `COMPLETED`.
- `reviewer.identity`, explicit `kind` (`HUMAN`, `AI`, or `CONSTRUCTED`), nonempty declared `expertise`, `access`, `limitations` lists, and recorded `procedure`.
- An explicitly supplied nonempty `assessment` object, an `evidence` list, and recorded `reasoning`.
- Explicit `uncertainties`, `disagreements`, and `failures` lists (empty lists are allowed declarations, not inferred answers).
- `declarations.blindness`: `DECLARED`, `NOT_BLIND`, or `UNKNOWN`; `declarations.independence`: `DECLARED`, `NOT_INDEPENDENT`, or `UNKNOWN`; and `cannot_mechanically_prove: true`.
- Nonempty `measurements`, keyed by dimension. Each value contains `outcome` (`PASS`, `FAIL`, `UNSCORABLE`, `NOT_ASSESSED`), explicit `finding` (null allowed), `evidence`, and nonempty `reasoning`. PASS/FAIL require evidence, and FAIL requires a primary-classified failure entry for that dimension.

Each evidence item has stable `source_id`, integer nonnegative Unicode `start` inclusive / `end` exclusive, and `quote` text. This module validates location structure, not that a quotation actually matches a source or that reasoning is valid. Output/mechanical evidence can use explicit stable output identifiers rather than claiming to be a source passage. Reviewer procedures must explain those identifiers and material access.

Failure entries preserve `failure_id`, `dimension`, `primary`, `secondary`, `original_observation`, and a separate `proposed_extension`. The taxonomy is STRUCTURAL, EVIDENCE-LOCATION, EVIDENCE-FIDELITY, INTERPRETATION, SCOPE, UNCERTAINTY, PROVENANCE, PERTURBATION, INSTRUCTION-BOUNDARY, REPEATABILITY, REVIEW-DISAGREEMENT, and UNCLASSIFIED. Secondary classifications may be empty, but may not duplicate the primary or one another. New categories are not forced into this vocabulary: choose UNCLASSIFIED where appropriate and record `proposed_extension: {"category": "...", "description": "..."}` separately, or explicit null if no extension is proposed. Original wording is retained unchanged by summaries and adjudication.

## Adjudication without forced consensus

```python
adjudicate(observations, reviews, adjudicator)
```

This requires explicit source observations with their schema and all six source-observation lists; at least one valid **completed** review; the same packet and phase across reviews; no duplicate reviewer participation in that packet; and a fully declared adjudicator with identity/kind/expertise/access/procedure/limitations. Empty objects, unprovided identities, and pending templates cannot impersonate independent reviewers. Constructed participants are accepted only with explicit `kind: CONSTRUCTED` and remain visibly tagged; such fixtures are not human participation.

The adjudicator must supply `decisions` for every dimension present in the reviews. Each decision requires `status: RESOLVED|UNRESOLVED`, recorded `reason`, `evidence` list, and explicit `resolution`. A RESOLVED decision requires nonempty evidence and non-null stated resolution. An UNRESOLVED decision must leave resolution null; missing evidence is allowed if the reason states the limitation. These are adjudicator claims, not mechanically established resolutions.

The result deep-copies observations into `source_observations`, every completed review into `reviewer_assessments`, and the adjudicator into `adjudication`; none overwrite one another. A separate `dimensions` view compares exact outcome, finding, and evidence, including locations. It labels **AGREEMENT**, **DISAGREEMENT**, or **UNRESOLVED**, retaining each review's measurements, uncertainty, and disagreement. Exact disagreement is never removed by an adjudicator decision. Fewer than two provided measurements, missing dimensions, unscorable/unassessed states, or explicitly declared uncertainty/disagreement keep matters unresolved. Differing exact findings/evidence remain DISAGREEMENT, with `unresolved: true`, even if the adjudicator separately proposes a resolution. No majority vote, inferred semantic equivalence, or forced reference label is generated. Review-level uncertainty is conservatively applied to each dimension; richer dimension-specific uncertainty is a future schema decision.

## Descriptive summaries

`summarize_reviews(reviews)` validates records, rejects duplicate IDs/participation, and reports completed records, pending templates, participant kinds, and declared participant identities. It produces no overall reliability score. For each measured dimension it reports all four raw outcome counts, `denominator` (all completed review records), `scorable_denominator` (PASS + FAIL), explicit missing count/IDs, exact finding prevalence, and prevalence denominator (records actually containing that dimension). Missing dimensions contribute NOT_ASSESSED, never pass. Pending-only and empty inputs produce no invented completed measurement results.

Comparisons are grouped strictly by packet and phase, never across unrelated items. Counts may pool review records across cases but are not counts of independent humans or independent cases. Failure summaries separately count primary entries and secondary classification assignments, state their respective denominators, and retain every original failure and extension with review ID. Exact agreement is descriptive consistency, not correctness or independence. No chance-corrected coefficient, calibration inference, confidence interval, benchmark threshold, or aggregate reliability metric is fabricated.

## Verification within tested scope

Run from repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s experimental/assessor_reliability/tests -p 'test_review.py' -v
```

All fixtures explicitly constructed, not reviewer participation or model outputs. Coverage includes staged source-only/reference packets; target claims; omitted answer keys/model identities; exact source snapshots and source aliases; unavailable source no-read; raw availability/hash/anonymization; fresh directories; duplicate/unsafe IDs; hash/UTF-8/path/symlink controls; generic model version `1`, variant `base`, numeral `10`, and generic source IDs; explicit retrieved-material rejection; required participant provenance; no fake pending reviewers; per-measurement outcomes/evidence; primary/secondary taxonomy and extensions; unprovided/empty/duplicate review rejection; single-review/missing/unscorable unresolved states; preserved disagreements despite adjudicator resolution; input immutability; per-dimension denominators and prevalence; and no fictitious outcomes from empty or pending-only inputs.
