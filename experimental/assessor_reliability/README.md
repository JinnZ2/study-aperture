Status: implemented experimental, offline, standard-library pilot with three complementary builds and constructed controls. It has not measured live-model reliability, recruited independent reviewers, established semantic fidelity, or changed core Study Aperture rules.

# Assessor-reliability pilot

This experiment audits whether an assessor locates and preserves evidence and uncertainty while using the existing Study Aperture method. Structural compliance, evidence fidelity, interpretation, uncertainty, repeatability, perturbation response and provenance remain separate. There is no overall reliability score.

The three builds share one frozen method and one declared case inventory. **A** captures exact raw outputs and performs bounded schema/evidence checks. **B** analyzes repeated and perturbed assessments field by field. **C** stages blinded reference/output review and preserves disagreement during adjudication. Each can be used independently through explicit local JSON; none feeds results automatically into `assess.py`.

The original proposal is [preserved unchanged](protocol/PROPOSAL.txt). [DESIGN.md](DESIGN.md) records repository fit, the three architectures, stopping rules, open decisions and limits. [REPORT_TEMPLATE.md](REPORT_TEMPLATE.md) keeps the requested final study report distinct from synthetic demonstration results. Per-build contracts are in `protocol/battery-design.md`, `protocol/comparison-design.md` and `protocol/review-design.md`.

## Quick software demonstration

Run from the repository root with Python 3.11 or later:

```sh
python3 -m experimental.assessor_reliability demo --output-dir /tmp/assessor-demo-new
python3 -m unittest discover -s experimental/assessor_reliability/tests -v
./run_checks.sh
```

The demo constructs source packages and assessor outputs in code, freezes inputs, records representative faithful/faulty synthetic captures, exercises repeats and perturbations, and exports pending review packets. `index.md` explains the artifacts; `index.json` supplies exact counts. No model API is called. No independent reviewer participation is claimed. The fixture generator sees its own construction observations; it is emphatically not a blinded assessor.

Every output directory must be new. Existing runs are refused. A failed capture keeps its raw bytes and execution-error record; preserve it and retry into a fresh directory. Do not edit generated reports or prior attempts.

## Build A: battery, freeze, prompt and capture

```sh
python3 -m experimental.assessor_reliability battery --output-dir /tmp/assessor-battery-new
python3 -m experimental.assessor_reliability freeze \
  --battery /tmp/assessor-battery-new/cases.json --output-dir /tmp/assessor-freeze-new
```

Use the case/variant identifiers from `cases.json`. Export a prompt, which excludes reference observations, scoring rules and expected perturbation results:

```sh
python3 -m experimental.assessor_reliability prompt \
  --battery /tmp/assessor-battery-new/cases.json --case <case-id> --variant <variant-id> \
  --freeze /tmp/assessor-freeze-new --output-dir /tmp/assessor-prompt-new
```

Supply the exported prompt exactly to the chosen assessor outside this offline harness. Save its unmodified response as a file and complete the generated `metadata-template.json` honestly. Model versions, dates and environment details that are not exposed stay explicitly `UNDECLARED`; they do not become proof of equivalent execution conditions. The `actual_prompt_sha256` must bind the exact exported prompt actually supplied. The harness does not authenticate that declaration or execute the provider.

```sh
python3 -m experimental.assessor_reliability capture \
  --battery /tmp/assessor-battery-new/cases.json --case <case-id> --variant <variant-id> \
  --freeze /tmp/assessor-freeze-new --raw /path/to/raw-output.txt \
  --metadata /path/to/completed-metadata.json --run-id <unique-run-id> \
  --output-dir /tmp/assessor-capture-new
```

The generated `capture.json` retains parsed output, original missing fields, mechanical results and execution provenance. `raw.bin` precedes parsing, `source-package.json` snapshots evidence available to the auditor, `case-record.json` retains source observations/dependencies, and `artifacts.json` binds persisted files. These are local consistency hashes, not signed identity or runtime attestations; someone controlling all files can forge a coherent history.

A valid record may remain incomplete. Matching a source ID or quote cannot prove correct source selection, passage relevance, meaning, qualification preservation, calibrated confidence or truth. Those remain review questions. Evidence coordinates are Unicode-character `[start,end)` spans in the selected decoded source text. A missing-source declaration is different from a hash mismatch or invented quotation.

## Build B: repeats and controlled changes

```sh
python3 -m experimental.assessor_reliability repeats \
  --captures /path/run-1/capture.json /path/run-2/capture.json \
  --freeze /tmp/assessor-freeze-new --output-dir /tmp/assessor-repeats-new

python3 -m experimental.assessor_reliability perturbation \
  --base /path/base-run/capture.json --variant-capture /path/variant-run/capture.json \
  --battery /tmp/assessor-battery-new/cases.json --freeze /tmp/assessor-freeze-new \
  --output-dir /tmp/assessor-perturbation-new
```

Use `--fields` and `--material-fields` only when those selections were specified before observing outputs; selection must be recorded in the study protocol. Frozen case dependencies govern the perturbation CLI. Missing/null values, execution failures, provenance differences and unscorable observations remain visible. Exact agreement is consistency, not correctness; a prespecified material-field difference is a review flag, not proof that meaning changed. Governing instructions stay fixed during a source perturbation even though the full prompt hash legitimately differs.

The CLI refuses changed implementation/freeze/capture hashes rather than silently rescoring. To investigate with revised scoring, version the revision explicitly and preserve earlier results. The lower-level Python functions are available for declared local analyses, not as an authorization to bypass this policy.

## Build C: blinded packets and adjudication

```sh
python3 -m experimental.assessor_reliability review-packets \
  --battery /tmp/assessor-battery-new/cases.json --phase reference \
  --output-dir /tmp/assessor-reference-packets-new

python3 -m experimental.assessor_reliability review-packets \
  --battery /tmp/assessor-battery-new/cases.json --phase output \
  --captures /path/run-1/capture.json /path/run-2/capture.json \
  --output-dir /tmp/assessor-output-packets-new
```

Send only the individual packet directories to the relevant independent reviewers, not the coordinator mapping, case inventory, expected observations or other reviewers' assessments. Reference reviewers should work before seeing model outputs. Output reviewers should work without expected conclusions. The templates are `PENDING`, not scores or completed human records. Do not distribute the entire coordinator output folder as a blinded packet.

```sh
python3 -m experimental.assessor_reliability review-validate --review /path/review.json
python3 -m experimental.assessor_reliability adjudicate \
  --observations /path/observations.json --reviews /path/review-1.json /path/review-2.json \
  --adjudicator /path/adjudicator.json --output-dir /tmp/assessor-adjudication-new
python3 -m experimental.assessor_reliability review-summary \
  --reviews /path/review-1.json /path/review-2.json --output-dir /tmp/assessor-review-summary-new
```

Reviewer expertise, access, procedure, limitations, evidence and uncertainty are required records, not guarantees of authority. Adjudication retains observations and each reviewer record separately. Unresolved disagreement does not become a forced consensus. Failure taxonomy extensions remain explicit rather than being squeezed into an inappropriate existing category.

The initial output-packet workflow refuses captures with nonempty retrieved-material exposure rather than silently omitting evidence. Capture can retain explicitly declared local retrieval snapshots, but staged blinded retrieval review is not implemented. Use supplied-only source packages for this pilot or design a separately versioned retrieval-review extension before that study.

## Before a live study

The owner/coordinator must resolve live sample sizes/repetitions, reviewer recruitment and blinding, model versions/environments, source exposure/retrieval conditions, hidden-battery policy, statistical choices, failure-review procedure and any later decision threshold. The constructed battery size is a software-test choice, not an unstated study-design decision. No threshold is invented before baseline evidence exists.

Core files and historical assessments remain unchanged. No new production mandatory fields, cards, tools or promotion rules are introduced. The only parent integration is registering this experiment's tests in `run_checks.sh`.

Exit 0 means an operation completed, including a capture containing invalid/unscorable assessment data; it is not an assessor pass. `review-validate` exits 1 for an invalid reviewer record. Exit 2 means invalid input or execution/I/O failure. Inspect the separate recorded outcomes rather than interpreting a shell exit as reliability.
