Status: implemented isolated pilot architecture with constructed controls. Live-model performance, independent reviewer participation, semantic fidelity and promotion into the core method are not established.

# Assessor-reliability experiment: three complementary builds

The experiment studies the assessor as an instrument. The source observations, reviewer assessments, adjudication, raw model outputs and mechanical checks are different records. Neither matching a reference nor passing a validator makes an interpretation true. The supplied proposal is retained verbatim in `protocol/PROPOSAL.txt`; the implementation decisions below are separate from that proposal.

## Repository fit and immutable boundary

The implementation was designed against Study Aperture commit `b9dbdeff48c23c44b20dff3c01b4304d3face54a`. The repository instructions in `CLAUDE.md` require offline, standard-library Python, explicit exchange between experimental projects and the core, and preservation of missing values. The seven existing cards route, extract and record; `assess.py` validates a record and prints incompleteness. In particular, `assess.py:load` inserts defaults, while `assess.py:check` assumes an already shaped record. Therefore this harness inspects the original parsed shape **before** calling the frozen validator. Missing fields remain observable rather than being hidden by normalization.

Only the new `experimental/assessor_reliability/` subtree and a test-suite registration in `run_checks.sh` are changed. Cards 00–06, `assess.py`, `TEMPLATE.json`, production vocabulary, vendored files, historical specimens and existing experimental projects are unchanged. No Cards 07–12 are introduced. There is no `labref`, automatic import, support promotion or production ingestion gate for these outputs.

The freeze copies the exact committed method files, the separately versioned experimental implementation, the declared case inventory, its observation/comparison records, and the explicit available source bytes. A case or scoring-dependency change after capture requires a new freeze. A changed harness cannot silently analyze earlier captures through the CLI. A lower-level library call remains a caller responsibility and must not be used to bypass the frozen CLI protocol.

## Build A: offline capture-and-fidelity audit

`harness.py` exports the frozen instructions and an untrusted JSON source package. It deliberately omits source observations, reference assessments, perturbation expectations and scoring rules. The experimental JSON envelope transports an unchanged `study-aperture/1` record alongside evidence bindings, assessor-declared findings and provenance. These additional fields belong only to the experiment.

The capture command saves `raw.bin` and a receipt before parsing, validation or input verification. Invalid JSON, duplicate keys and nonfinite numbers are captured as such; no fenced-block extraction, quote repair or default substitution occurs. Exact prompt hashes, source identities and hashes, model/version declarations, execution date, environment, tool access, supplied/retrieved material, execution errors, retries, truncation and incomplete responses remain available. Missing sources are explicitly unavailable, not read from presumed content. Prior knowledge has unknown origin unless separately established; the harness cannot establish training exposure.

Mechanical measurements remain narrow. Transport/schema validity, deterministic invariant violations and incompleteness are separate. Evidence source IDs, selected spans, exact quotations and declared origin/transformation/justification are checked against explicit captures. Span coordinates count decoded Unicode characters, not bytes or JSON escape characters. An exact quotation can still be irrelevant, scoped incorrectly, attributed to prior work, or misunderstood. A provenance chain binds origin without validating the transformation. Semantic fidelity, omitted relevant evidence, unsupported resolution and source authentication remain for review.

A final JSON record cannot establish that the assessor used the core CLI's legal mutation sequence. The frozen validator checks resolution prerequisites; mutation history is `NOT_ASSESSED` unless separately captured. A structurally valid but incomplete record is not silently failed or called complete.

## Build B: repeatability-and-perturbation analyzer

`comparison.py` compares exact fields under declared equivalent conditions. Run pairs with changed model/prompt/environment/exposure, invalid capture prerequisites or execution problems remain separately unscorable. Field absence is not null. Agreement is reported field by field with raw numerator, denominator, missing/unscorable observations and class prevalence; a disagreement in evidence cannot be offset by agreement in another field.

Relevant source changes necessarily change the full prompt hash. Perturbation comparisons therefore distinguish the instruction hash from the full prompt/source-package hash: governing instructions should remain equivalent while explicitly changed evidence may differ. A predeclared matrix names allowed changes, required changes, invariants, unresolved conditions, evidence justifications and limits. An allowed change is not automatically required; an unchanged output is not automatically a success. Prose unresolved-condition rules and semantic equivalence require review rather than being simulated by field equality.

Repeated runs measure consistency under these declarations, not correctness or independence. Exact array/text differences do not establish materially different meaning. Material-field flags identify prespecified consequential field changes that reviewers must interpret. No aggregate reliability score, chance-corrected statistic or performance threshold is selected by default. Cohen/Fleiss/Gwet statistics and uncertainty intervals remain decisions contingent on the real sampling unit, field structure, dependence and class prevalence.

## Build C: staged blinded review and disagreement-preserving adjudication

`review.py` exports reference packets containing source material but no AI outputs or construction observations. Output-review packets contain anonymized captured outputs and source material but no expected findings or other reviewer judgments. Coordinator mappings remain in a separate private file. Packets and pending templates are not completed reviewer assessments; operational blinding must be managed by the coordinator and cannot be proved by the JSON itself.

Completed reviews record identity, expertise, actual access, procedure, limits, source evidence, reasoning, uncertainty and dimension-specific observations. Failures retain their original observation, a primary category, optional secondary categories and a proposed extension where no existing class fits. `UNCLASSIFIED` is legal. Adjudication preserves the observation object and every independent reviewer record, with agreement, disagreement and unresolved states separately visible. Voting does not turn disagreement into truth. A reviewer can be wrong; neither identity nor agreement is automatic authority.

The initial supplied demonstration deliberately creates pending review packets rather than pretending to recruit independent humans. Synthetic reviewer examples, if used in unit tests, are constructed software test inputs only.

## Pilot decisions and execution gates

The **software demonstration** uses a constructed battery spanning the 15 proposed families and all 10 perturbation types, with a small number of explicit repeated/fault-injection captures. This is an implementation choice for harness testing, not approval of a full study sample size or a hidden model benchmark. The full test battery is public; hidden-test resistance is not established.

Before live execution, the owner/coordinator must preregister a study identifier and resolve the number of cases/repeats, reviewer recruitment and expertise criteria, independence/blinding procedure, model/version identifiers, source exposure or controlled retrieval policy, held-out battery policy, failure-review method, sampling/interval/statistic choices, and intended use of any later threshold. None is filled by an unstated assumption. The offline transport is implemented; live provider execution and controlled retrieval are not enabled automatically.

The proposed sequence is freeze and document, construct cases and observations, obtain independent reference reviews, capture baseline assessments, repeat selected cases, capture perturbations, obtain blinded output reviews, analyze distinct dimensions, then consider a separate promotion review. The CLI allows construction and software demonstrations while those study decisions are pending; it does not authorize presenting those demonstrations as an executed independent assessment study.

## Failure and stopping policy

Predeclared assay failures include invented evidence, unsupported direct-evidence claims, lost material conditions, unsupported resolution, erased disagreement, deterministic invariant violations, instruction diversion and inappropriate perturbation responses. Only the mechanically testable subset is machine-classified. An inadequately supported comparison is `UNSCORABLE`, never a pass or fail. Interpretive/uncertainty judgments remain pending review.

Pause when cases have unintended differences, reference records conflict internally, hashes/versions cannot be reconciled, execution conditions change without adequate recording, or scoring rules are revised after outputs are seen. The harness enforces frozen byte/case/prompt mismatches and preserves failed capture attempts. The reviewer/coordinator handles unintended semantic construction differences and reference inconsistency; software cannot establish those from hashes. Never edit an old attempt or silently rescore it. A correction gets a new version, a new output directory, explicit deviation and linkage to the earlier raw record.

## Evidence for the experiment, not an assessor ranking

Success of the pilot means inspectable, reproducible evidence about the harness and eventually the assessor's behavior, including failure and uncertainty. Unit tests and synthetic controls establish only the implemented behavior within their tested scope. The initial build establishes neither general model reliability nor publication validity, confidence calibration, reviewer correctness, independence or truth. Any promotion into core tooling needs a separately authorized evidential review, not an automatic code path.

## Source anchors

The governing user proposal is `protocol/PROPOSAL.txt`, sections 1–14 and its final design constraint. Repository anchors are the frozen `CLAUDE.md` boundary/invariants, `assess.py` functions `load`, `check` and `incompleteness`, `AI_ENTRY_PROMPT.md` steps 1–8 and output handoff, Card 01 sections 1–3, Card 02 input-average declarations, Card 03 declared-lineage limits, and Card 06 decision ledger/labels. The sibling `experimental/publication_provenance/README.md` supplies the relevant local precedent: hash binding is not semantic fidelity or publisher authentication. No external statistical authority is invented by this design.
