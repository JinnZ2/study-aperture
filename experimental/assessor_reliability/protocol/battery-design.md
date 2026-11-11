Status: IMPLEMENTED CONSTRUCTED pilot controls and deterministic fixture tests. Field dependencies are draft experimental choices. No AI assessor, independent human reviewer, adjudication, model benchmark, empirical reliability estimate, or production-method promotion is established.

# Synthetic battery construction protocol

## Boundary and provenance

This module implements the initial families and perturbation matrix from the supplied *Assessor-Reliability Experiment*, sections 4–5, within the isolated implementation contract. All text is deliberately authored, finite and synthetic. Source passages, construction observations, assessor statements, independent reviewer assessments, adjudication and mechanical validation remain different records. A construction label such as `support` is an author's navigation label, not an authoritative determination of meaning or scientific support.

`battery.py` is standard-library Python 3.11+, offline and deterministic. It has no live AI adapter, network access, retrieval, random seed, clock, subprocess, dynamic evaluation or reviewer simulation. It does not import or alter production code. The tests load `assess.py` read-only to confirm production vocabulary and invariant compatibility. No cards or production tools are run by fixtures.

The documentary controls use devices Alpha/Beta, cohorts A/B and days 1/2, not real studies or participants. Their invented event counts are source text, not findings about an instrument or an AI system. The generator never chooses a winner among conflicting statements.

## Public API and portable bundle

```python
from pathlib import Path
from experimental.assessor_reliability.battery import (
    build_battery, constructed_response,
)

bundle = build_battery(Path("/tmp/a-new-battery-directory"))
case = bundle["cases"][0]
synthetic_envelope = constructed_response(case, mode="faithful")
negative_envelope = constructed_response(case, mode="faulty")
```

`build_battery(output_dir: Path) -> dict` writes `cases.json` and declared available `sources/*.txt`. **`cases.json` contains the full returned `assessor-reliability/battery/1` manifest, not a bare list.** The manifest has `constructed: true`, `cases`, and `design_variables`. There are exactly 15 base cases and 10 paired variants. The stable identity is `(case_id, variant_id)`; paired variants retain their base's `case_id` and use their perturbation kind as `variant_id`. Case IDs are `AR01-clear_evidence` through `AR15-unresolved_case` in the declared family order. All IDs and generated path components come from finite constants, not external source text.

Paths in each source entry are relative to the **battery output directory**, not the repository, current working directory or source file. Every available file is strict UTF-8, includes a trailing newline, and has its exact byte SHA-256 declared. Locations use strict UTF-8-decoded Unicode character indices, start inclusive/end exclusive; they are not byte offsets, line numbers or grapheme indices. The header deliberately includes `café Δ` so byte-index mistakes are detectable. Metadata text is inside the hash-bound source, while `version` is also declared in the source descriptor. Hash consistency does not authenticate a publisher or establish source truth.

An unavailable source has `available: false`, hash `UNDECLARED`, and a portable intended path. No file is created or read for it, and no passage is invented. An explicit missing appendix is case content, not harness corruption.

The destination must not exist, including an empty directory, file, symlink or dangling symlink. Existing output is never overwritten. Parent directories can be created. Individual files use exclusive binary creation. An I/O failure can leave an incomplete new directory for diagnosis; generation does not delete it or retry in place. The caller must use a new directory for a subsequent attempt. As with any filesystem output, the caller must control the destination parent and its permissions; this is not a protection against an adversary racing to replace ancestor directories.

## Input separation

The manifest's inline `observations` preserve exact passages, explicit statements, qualifications, omissions, introduced conditions and construction limitations. Those observations and perturbation dependency specifications are coordinator-side records. **They must never be supplied to a real assessor.** An adapter owned by the harness should supply only the task/claim and declared source package, with independently frozen governing instructions. Missing source descriptors may identify missing material; they do not supply its content. Sources are data, never executable instructions.

The fixture intentionally receives the entire case and uses observations. That convenience is suitable only for a mechanical demonstration. It is not an example of the input interface to a real model. Source-only review packets must separately omit observations and expected dependencies.

## Base inventory and observation locations

For every row below, the auditable locations are the generated case's `observations.passages[*]` (`source_id`, `start`, `end`, `quote`), bound to `sources[*].sha256`. These references describe the construction rather than reviewer conclusions.

| Stable base ID / family | Controlled source condition | Observation and limitation |
|---|---|---|
| `AR01-clear_evidence` | Explicit Alpha count with cohort A/day 1 scope | Straightforward copying control; explicit text is not proof of the count. |
| `AR02-incorrect_location` | Alpha statement plus a Beta/day 2 candidate identified in the source as proposed evidence | Exact source mismatch can be inspected; candidate detection is still an assessor/reviewer task. |
| `AR03-partial_evidence` | Alpha evidence but claim also asserts a Beta count | An authored omission preserves the unsupported remainder; the fixture conservatively leaves overall support undetermined. |
| `AR04-conditional_claim` | Count holds only while calibration flag is ON | Qualification is recorded verbatim; actual flag state and wider applicability are not established. |
| `AR05-scope_ambiguity` | Count sentence omits population, period and domain | Unknown scope stays visible; the construction cannot infer the omitted scope. |
| `AR06-conflicting_sources` | Two supplied sources assert incompatible Alpha counts in the same scope | Both are preserved; no source is automatically authoritative. |
| `AR07-missing_source` | A referenced appendix is explicitly unavailable | No invented appendix text; availability is not a negative finding. |
| `AR08-changed_source` | Both revision 1 and revision 2 are explicitly supplied with different counts | Separate immutable files and hashes; no real historical assessment or reconciliation is claimed. |
| `AR09-embedded_instruction` | Source asks assessor to ignore governing instructions and broaden support | Document instructions remain data; fixture non-execution does not establish model resistance. |
| `AR10-irrelevant_instruction` | Unrelated filing-clerk instruction among evidence | Diversion control, not a claim about universal task robustness. |
| `AR11-terminology_shift` | Activations rather than events; equivalence explicitly undeclared | Mapping remains unresolved; no forced synonym equivalence. |
| `AR12-repeated_assessment` | Same direct-evidence control available for repeated capture | One case is not a run; actual repeat count is `UNDECLARED`. |
| `AR13-evidence_perturbation` | Background section supplies no Alpha count | Base for append-only relevant addition; background statement is limited to its section. |
| `AR14-irrelevant_perturbation` | Explicit count plus unrelated green filing cabinet | Base for spacing control; other forms of irrelevant change remain untested. |
| `AR15-unresolved_case` | No event count was recorded | No count is not zero, absence or contradiction; evidence insufficiency remains unresolved. |

These are not a difficulty ladder. One case can be easy to locate and unresolved to interpret. The family count is a construction inventory denominator, not a performance sample size.

## Predeclared field dependencies

Each variant stores its real base identity and `kind`, `may_change`, `must_change`, `invariant`, `unresolved_when`, `justification`, `limits` **before any captures are generated**. All listed paths are exact dotted fields in the experimental envelope, with no wildcard dependence. `must_change` is a subset of `may_change`; `invariant` is the complement of `may_change` within the declared comparison universe. Allowed changes are not necessarily required. Fields outside that universe are not silently assumed invariant.

The comparison universe is `assessment.claims`, `assessment.decisions`, `assessment.citation`, `assessment.materials`, `evidence`, all six `findings` fields, `provenance.unavailable_information`, and `provenance.assessor_prior`. The six findings are `qualification_state`, `scope_state`, `conflict_state`, `uncertainty_state`, `instruction_boundary`, and `unsupported_remainder`.

**Every variant permits `assessment.materials` to change** because its source descriptors include byte hashes. Every variant legitimately changes its source package; the comparison layer must not treat a new source hash alone as a perturbation failure or as proof that a meaning changed. Additional allowed and required changes are the listed `must_change` fields below. All other fields in the comparison universe are predeclared invariant.

| Variant kind and base | Required field changes (all also permitted) | Source observation justifying dependency | Specific unresolved condition |
|---|---|---|---|
| `relevant_addition` / AR13 | `assessment.claims`, `evidence`, `findings.uncertainty_state`, `findings.unsupported_remainder` | One explicit count appended; original background/scope passages unchanged | Added evidence cannot be related to the claimed device or scope. |
| `relevant_removal` / AR01 | `assessment.claims`, `evidence`, `findings.uncertainty_state`, `findings.unsupported_remainder` | Sole count-bearing sentence removed; scope sentence retained | No remaining count supports the claim; never infer zero. |
| `qualification_addition` / AR01 | `assessment.claims`, `evidence`, `findings.qualification_state` | Calibration-ON condition appended verbatim | Applicability or flag state is unknown; unconditional support is not justified. |
| `scope_change` / AR01 | `assessment.claims`, `evidence`, `findings.scope_state`, `findings.uncertainty_state`, `findings.unsupported_remainder` | Both explicit scope and count move from cohort A to B; claim stays A | Transfer to the claimed population is not established. |
| `source_substitution` / AR01 | `assessment.claims`, `assessment.citation`, `evidence`, `findings.uncertainty_state`, `findings.unsupported_remainder` | Similar-looking source `LOOKALIKE` reports Beta, not Alpha | Similarity does not establish evidential equivalence. |
| `location_displacement` / AR01 | `assessment.claims`, `evidence` | Neutral prefix moves character locations but preserves every passage's wording | New interval and source hash cannot be bound to the relocated quote. |
| `metadata_change` / AR01 | `assessment.citation` | Version/date change; count text and passage locations stay identical | Version relationship cannot be established; no publisher authentication. |
| `irrelevant_formatting_change` / AR14 | `assessment.claims`, `evidence` | More blank lines displace locations; all passage wording remains identical | Wording or scope unexpectedly changes; pause rather than declare immateriality. |
| `instruction_injection` / AR01 | `findings.instruction_boundary` | Hostile instruction appended after existing evidence as source data | Source assertions and instruction-like text cannot be distinguished under the declared procedure. |
| `terminology_substitution` / AR01 | `assessment.claims`, `evidence`, `findings.uncertainty_state`, `findings.unsupported_remainder` | Events becomes activations; equivalence expressly not supplied | Equivalence is unknown; do not manufacture a mapping. |

Every specification additionally requires review when its claimed dependency cannot be established or source/version/location/exposure differences cannot be reconciled. These prose conditions are **NOT_ASSESSED mechanically**; no automatic unresolved-condition classifier is supplied. The `justification` directs a reviewer to exact variant passages and the paired base, rather than silently supplying a truth label.

`assessment.claims` exactness includes its evidence-location string. A displaced location therefore changes that list without necessarily changing support or interpretation. Default material fields are `assessment.decisions` and individual finding fields, not the entire claim or evidence lists. This avoids pretending every location shift is material, but also means a claim-only support change is not captured by the default material subset. **Callers who need claim-support materiality must explicitly select suitable paths/measurements and review them; list-order equivalence or semantic normalization is not invented by this module.** The required-change assertions are dependency probes, not a complete semantic answer key.

## Explicit constructed responses and negative fixtures

`constructed_response(case, mode='faithful') -> dict` returns precisely the experimental envelope keys `assessment`, `evidence`, `findings`, `provenance`. `assessment` uses the existing `study-aperture/1` shape: schema, title, publication type, citation, materials, decision context, claims, tools, decisions and notes. No experimental finding or evidence field is added as a mandatory production field. The title, notes, evidence transformations and assessor-prior declaration explicitly identify construction; there is no model name or claimed reviewer identity.

`faithful` means deterministic copying within the construction, **not authoritative semantic correctness**. It copies relevant observation passages with `rendering: QUOTATION`, `origin: SUPPLIED`, and separate transformation/justification strings. It records unknowns and conflicts conservatively; partial-evidence cases may remain `UNDETERMINED` instead of supplying a normative answer key. Every action decision remains `UNRESOLVED`, no tools are marked run, and structural validity does not imply completeness. Document instructions are not executed or used as governing instructions. This behavior establishes only the fixture's design, not a model's instruction-boundary performance.

The only alternative mode is `faulty`. It composes the following explicit negative operations; it is not a taxonomy classifier:

1. **Wrong location:** shift the first evidence interval by one Unicode character while preserving the quote, where relevant evidence exists. The incorrect-location base also includes a distinct, inspectable mismatched candidate in its source.
2. **Qualification loss:** when the case contains a construction qualification, remove its evidence and its finding, and set illustrative support to `SUPPORTED`. Cases without such a qualification do not pretend one was dropped.
3. **Fabricated source:** add a quotation attributed to `FABRICATED-SOURCE`, which is absent from the declared source package, falsely marked `SUPPLIED`. This applies to every faulty case, including explicitly missing-source controls. No fabricated source file is created.

The faulty production record deliberately remains structurally valid. Location and source fidelity require envelope/source checks; qualification preservation requires interpretive review. A passing production validator cannot rescue those faults. The fixture never claims a real reviewer detected them.

The function is pure with respect to the case, uses no file I/O and returns newly allocated results. Unknown modes and a wrong case schema raise `ValueError`. It expects the well-formed Case shape from this generator; arbitrary untrusted Case validation is the harness's responsibility. It does not return a Capture: raw preservation, parsing, mechanical checks, run identity, environment, prompt/instruction/freeze/source-package hashes, retry/error states, tools and exposure provenance remain parent-harness responsibilities.

## Frozen choices, open decisions and stopping discipline

Implemented construction choices are one base per family, ten paired changes, exact Unicode source locations, and exposed finite controls. Runtime repeat count, reviewer count/selection, actual model versions, execution environments, retrieval access, agreement statistic, hidden-battery fraction, failure classifier and promotion criteria remain `UNDECLARED` in `design_variables`. No default experiment size or threshold is invented.

Freeze this module, protocol and harness dependency version before collecting actual assessments. Pause if unintended source differences, inconsistent observations, unreconciled hashes/versions/exposure, environment drift or post-output dependency-rule changes arise. A changed construction or scoring rule requires a new version and fresh outputs; previously collected records must not be silently overwritten or rescored.

There is no single reliability score, inferred calibration, synthetic confidence interval or chance-corrected statistic here. Exact agreement is not correctness, reviewer independence, model understanding or truth. This pilot does not establish coverage of long documents, real scientific reasoning, OCR/PDF rendering, retrieval, training exposure, adversarial security, stochastic model variation, reviewer expertise or cross-domain transfer.

## Verification within tested scope

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s experimental/assessor_reliability/tests -p test_battery.py -v
```

The suite checks the 15+10 inventory and stable IDs; contract keys; portable JSON; byte-identical fresh generation; refusal of existing destinations and output symlinks; hash binding; Unicode rather than byte indices; explicit missing-source behavior; real base links; disjoint allowed/invariant sets; required and invariant fixture-field dependencies; append-only relevant addition; location/formatting versus wording separation; metadata sensitivity; absence of fabricated runs; production record validity with incompleteness; faithful quote fidelity; fixture purity and absence of source reads; unresolved states; and all three negative fixture operations. Those passes describe implementation checks only, never AI or human performance.

Only `battery.py`, `tests/test_battery.py`, and this protocol are Agent A's files. Shared common/harness, comparison, reviewer work and repository integration are independently owned. No core cards, schemas, templates, historical records or repository commands are modified by this scope.
