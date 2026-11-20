Status: Implemented offline, standard-library mechanical comparison analyzers with constructed unit tests. This is an isolated pilot implementation, not a model benchmark, independently reviewed assessment, correctness test, or established measure of general assessor reliability. Semantic review and selection of chance-corrected statistics remain unimplemented.

# Comparison protocol

## Boundary and source of requirements

This module implements only repeatability, declared-field perturbation probes, exact agreement, and report rendering. It does not invoke an assessor, open source documents, inspect production artifacts, infer source meaning, synthesize reviewers, or modify a study-aperture record. Captures, mechanical validation, source observations, reviewer assessments, and adjudication remain distinct inputs or records; comparisons do not replace any of them.

The supplied **Assessor-Reliability Experiment** proposal is preserved separately by the coordinator as `protocol/PROPOSAL.txt` (original input: `Pasted_content_73.txt`). The implemented scope derives from §2 (experimental boundary), §5 (predeclared perturbation dependencies), §6 (capture/provenance), §7 (separate measurement dimensions), §8 (agreement counts and limitations), §10 (unscorable cases and protocol drift), §12 (denominators), and its final design constraint. These are design requirements, not observed findings. The shared implementation contract defines the capture interface and API. For the parent's full-prompt hashing convention, see `harness.py::prompt_for`: the full prompt contains the case/source payload; `instructions_sha256` separately identifies governing instructions.

## Public API and output contract

```python
compare_repeats(captures, fields=None, material_fields=None) -> dict
compare_perturbation(base, variant, spec) -> dict
agreement(records, fields) -> dict
render_markdown(report) -> str
```

All reports use `schema: assessor-reliability/comparison/1`, a `kind`, and `status: MECHANICAL_COMPARISON_ONLY`. There is no overall pass/fail judgment, reliability score, threshold, truth label, confidence interval, or selected kappa/AC statistic. `PASS` and `FAIL` name a specific exact-equality or declared-field-rule result, never an assessor's correctness. Inputs are not mutated, and these functions write no files. Persist reports through the parent's fresh-output mechanism.

Runtime is Python 3.11+ using only the standard library. The module contains private helpers and has no dependency on the parent common/harness implementation, production validator, other agents, external packages, credentials, network, random state, or clocks.

Inputs must be plain JSON objects/arrays/scalars. Nonfinite numbers, non-string object keys, tuples, and other Python-only values are rejected as malformed observations. The capture reader, not this analyzer, is responsible for duplicate-key rejection and raw/parsed byte binding. An already-created Python dictionary cannot reveal discarded duplicate JSON keys. Invalid capture objects are recorded as exclusions rather than silently repaired. Invalid API field selections raise `ValueError`; invalid perturbation specifications yield an unscorable report with reasons.

## Exact field selection and missing values

`fields` contains dotted **object-key** paths relative to the parsed experimental envelope for captures, or relative to each directly supplied plain record for `agreement`. Defaults for repeats are:

```text
assessment.claims
assessment.decisions
evidence
findings
```

Explicit `fields=[]` requests no field measurements. Duplicate paths are deduplicated in input order. Material paths not already selected are added to selection. No material paths are assumed by default. Lists can be selected as whole fields but are not indexed or identity-matched. Wildcards are deliberately unsupported and rejected. Object keys containing literal dots are outside this path convention; use a parent object field instead.

Exact equality canonicalizes only object-key order. Array order, case, whitespace, Unicode strings, booleans, numbers, explicit null, and sentinel strings remain literal values; for example `true`, `1`, and `1.0` are three distinct JSON observations. Reordering evidence or claims is an exact disagreement; no semantic equivalence or material meaning is invented.

An absent field is internally a unique missing marker and is rendered as `{"$missing": true}`. Presence flags accompany comparisons, so a real field whose literal value is that same object is not confused with absence. Explicit null is a present value. Absent fields yield `UNSCORABLE`, even when both absent; the reported `exact_equal` can still record both absences as equal, but that is **not counted as agreement**. A missing-versus-null comparison records the difference while remaining unscorable. Two explicit nulls can count as exact agreement without establishing known content. `UNDECLARED`, `UNRESOLVED`, `UNKNOWN_ORIGIN`, and other sentinel strings remain visible literal classes, not zero, false, failure, or completion.

## Capture eligibility and provenance gates

A directly supplied capture is eligible only if it declares the supported capture schema; nonempty run/case/variant identifiers; a SHA-256-shaped raw hash; parsed object output; an empty parse-error list; schema validation true; empty invariant-violation and required-missing-field lists; explicit validation incompleteness; complete provenance; and error-free, nontruncated, nonincomplete execution. A boolean retry count is not an integer count. Missing/null declarations or malformed JSON values are excluded. Duplicate run IDs are excluded because separate executions are not established. The raw hash is checked for format only: actual byte binding is the responsibility of `harness.py::read_capture`, which must be used for persisted captures.

A record can be valid and incomplete. `validation.incompleteness` is retained; incompleteness alone does not exclude a parseable valid capture. An absent optional selected field remains separately unscorable. Mechanical fidelity results are not used to infer semantic success, nor automatically excluded: two schema-valid outputs can agree exactly while both have an incorrectly located quote. Structural invalidity prevents scoring here; separate structural/mechanical reports remain necessary.

For repeats, every potential unordered pair is checked against recorded case and variant identifiers, model name/version, environment object, full prompt hash, governing-instruction hash, source-package hash, freeze hash, tools, retrieved material, supplied material, retry count, and declared assessor-prior origin. Equality is exact and exposure lists retain order. Differences make the **pair** unscorable, not a failed assessor output. Assessment timestamps, capture timestamps, run IDs, raw-output hashes, and auditor timestamps are not required to match: they identify executions or outputs, not equivalent assessor inputs. IDs must nonetheless be distinct.

Matching model metadata containing `UNDECLARED`, or a matching empty environment object, is allowed only as **matching declarations**. Reports explicitly expose `unknown_metadata`, a declaration-only basis, and a limitation explaining that actual equivalent model versions/environments have not been established. This avoids upgrading absent provider attestations into claims of controlled execution. Missing or null provenance does not match, even when missing/null on both sides. `UNKNOWN_ORIGIN` for assessor-prior origin is preserved without inferring training exposure. Even fully named matching declarations are not independent identity/runtime attestation.

## Repeats: pair counts, material designation, prevalence

For `n` input records, the pair denominator is `n * (n - 1) / 2`; every unordered pair appears exactly once. Excluded or provenance-mismatched pairs stay in this denominator. Each selected field reports:

- Raw `PASS`, `FAIL`, `UNSCORABLE`, and `NOT_ASSESSED` counts; `denominator` is all potential pairs, and `scorable_denominator` is `PASS + FAIL`.
- `exact_agreement_count` and `exact_disagreement_count`, corresponding only to scorable exact equality/mismatch.
- `declared_material` and `material_disagreement_count`; the latter is an exact mismatch count only when the caller selected that field as material, and otherwise is null, **not zero evidence of no material disagreement**.
- An observation denominator (all input records), eligible-observation denominator (individually usable records), present-observation denominator, and missing/null/excluded observation counts.
- Literal-value `class_prevalence` with raw count, input-record denominator, and present-record denominator. Individually usable captures remain in prevalence even if some pairs are provenance-incomparable; pair gates remain visible separately. Missing fields and excluded records are not manufactured into prevalence classes.

`inputs` retain indices, safe run identifiers, eligibility reasons, and incompleteness. Missing or invalid-JSON incompleteness is displayed as missing rather than silently converted to an empty completed state. `pairs` retain indices, IDs, provenance checks, exclusion reasons, field presence, literal observations, and equality results. Empty samples or singletons have zero pair/scorable denominators, never a successful experiment.

Pairwise observations share records and are not independent Bernoulli trials. No interval or chance correction is selected automatically. A suitable statistic would require a separately versioned protocol defining units, rater/case alignment, field structure, class prevalence, assumptions, and limitations before analysis.

## Perturbations: source/payload changes and declared dependencies

`compare_perturbation` accepts the case's predeclared perturbation specification: base identifiers, kind, `may_change`, `must_change`, `invariant`, prose `unresolved_when`, justification, and limits. Base linkage and nonempty source-change justification must be declared. Invariant rules overlapping change rules, including parent/child overlap, are ambiguous and make the report unscorable. `must_change` implies a permitted change; its inclusion in `may_change` is optional and does not produce conflicting rules.

The recorded source-package hashes must differ. Changed supplied material and a changed **full prompt hash** are allowed and recorded as permitted declaration differences; the full prompt includes the source/case payload. Governing `instructions_sha256`, model declarations, environment, freeze, tools, retrieved exposure, retry conditioning, and assessor-prior declarations must still match. Source/prompt differences alone are not assessor failures. Same-package comparisons, incompatible linkage, undeclared justification, invalid captures, duplicate runs, or other conditioning drift are unscorable.

`source_change.status: DECLARED_CHANGE` means different valid hash declarations with a valid specification, not that this module read source bytes, independently reconciled versions, established authenticity, or proved an isolated legitimate manipulation. A package hash also includes case/variant declarations in the parent harness; a different hash is not by itself proof that substantive source bytes changed. Source integrity and intended manipulations require the parent's frozen bundle checks and source/reviewer records. Allowed full-prompt differences cannot here be decomposed into trusted source-only versus unauthorized governing changes; the separate instruction hash is still only a declaration until binding is checked externally.

Every selected field records exact comparison values and these independently reported rule outcomes:

| Rule | Equal present values | Different present values | Field absent or pair ineligible |
|---|---|---|---|
| `must_change` | `FAIL` | `PASS` | `UNSCORABLE` |
| `invariant` | `PASS` | `FAIL` | `UNSCORABLE` |
| `may_change` only | `NOT_ASSESSED` | `NOT_ASSESSED` | `UNSCORABLE` |
| No declared rule | `NOT_ASSESSED` | `NOT_ASSESSED` | `UNSCORABLE` |

A must-change `PASS` says only that the selected literal field changed. A change to explicit null is recorded as a present literal change, not an appropriate uncertainty response. The same field's exact-equality comparison and dependency-rule outcome can differ: an unchanged required-change field has exact-equality `PASS` and must-change `FAIL`. Neither is an overall correctness judgment.

Perturbation per-field counts use a **rule-evaluation denominator**, not a sample or pair denominator. For a field appearing in both may-change and must-change, there are two rule outcomes: an optional change rule remains `NOT_ASSESSED`; the required-change rule is scored independently. `pair_denominator: 1`, `rule_denominator`, and the two-record observation denominators are explicitly separate. Per-field missing/null/excluded counts and literal prevalence are also retained. A conditioning-invalid perturbation excludes both field observations from that matched pair's measurements.

To detect undeclared output differences, the analyzer recursively compares all parsed-envelope object keys. Ordered arrays are atomic values; no element/claim/evidence identity matching is inferred. A parent change rule covers descendant object-key changes. Differences covered by may/must rules are recorded `NOT_ASSESSED` as permitted literal changes; differences in invariant fields or outside all allowed paths are flagged `FAIL` as `INVARIANT_FIELD_CHANGE` or `UNPLANNED_FIELD_CHANGE`. These are mechanical protocol-review flags, **not automated findings that a change is semantically unsupported**. Added or removed keys have explicit presence markers. A missing required field remains unscorable under its declared rule even if its literal presence change is reported. No unplanned semantic classifier is implemented.

All prose unresolved conditions remain `NOT_ASSESSED`, with raw condition counts and zero scorable denominator. The original prose, justification, and limits are retained for human inspection. There is no automatic assessment of whether a response changed for the right evidential reasons.

## Agreement across records

`agreement(records, fields)` uses the same exact pair/observation/prevalence reporting. Plain record objects are compared directly as explicitly supplied same-unit records: the caller must align case, dimension, procedure, and records before calling. The analyzer neither matches reviewers nor establishes their identity, access, expertise, blindness, independence, or correctness. A literal `UNSCORABLE` or `NOT_ASSESSED` string in a plain record remains a visible class; it is not silently converted into agreement with known content. Review eligibility/status summaries belong to the separate review module.

When the supplied records are capture objects, they are unwrapped to parsed output and subject to the full capture/provenance repeat gates. Mixed capture/plain-record pairs are unscorable. If assessors intentionally have different model/prompt/environment conditions, their captures are not equivalent repeats; align explicitly selected plain assessment records for descriptive cross-assessor agreement, retain their original provenance separately, and do not claim an equivalent-conditions experiment. Pooling different cases or missing observations to inflate agreement is outside the protocol.

## Markdown report and verification

`render_markdown` starts with the limitation status, shows sample/pair denominators and per-field outcome counts, explains denominator units and material designation, lists limitations, and includes a complete JSON audit appendix. The appendix preserves all prevalence, field-presence markers, exclusions, provenance checks, permitted differences, and unresolved conditions rather than hiding them behind a table. Table content is escaped, and code fences expand to preserve arbitrary backticks in input text. Output is deterministic and ends with a newline. It cannot establish data authenticity.

Focused tests, from repository root:

```sh
python3 -m unittest discover -s experimental/assessor_reliability/tests -p test_comparison.py -v
```

Tests use only **CONSTRUCTED** capture-shaped objects and plain observations; schema-valid metadata in these fixtures is a constructed declaration, not an assertion that production validation or an assessor ran. Tests cover exact pair counts and denominators; declared material designation; absent/null/literal-marker distinctions; sentinel prevalence; incompleteness; type and order exactness; every matching-condition category; missing/null provenance; unknown-version declaration limits; invalid capture/execution shapes; duplicate IDs; zero denominators; perturbation source/full-prompt allowances with instruction drift excluded; optional versus required changes; invariant/unplanned flags; invalid/conflicting specifications; missing/null changes; unresolved prose; input immutability; Markdown escaping and full-audit preservation. Passing these tests supports only the stated implemented scope.
