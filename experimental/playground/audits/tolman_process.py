"""Inspect the Tolman VI audit process without changing its original records.

From experimental/: python3 -m playground.audits.tolman_process --output-dir NEW_DIR
The offline replay executes only hash-pinned, locally authored review code.
It does not extend the closed equation engine or execute publication code.
"""

from __future__ import annotations

import argparse
import enum
import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

from ..applicability.mapping import (
    Assessment, Condition, ConditionBasis, Constraint, Context, Decision, Domain,
    EvidenceKind, Judgment, assess, build_map,
)
from ..detection.non_detection import NonDetectionObservation, record_non_detection
from ..detection.scoped_absence import claim_absence
from ..equations.adapter import Equation, EquationRegistry, InputPort, OutputPort
from ..equations.substitution import BoundaryProtocol, Experiment, ValidationPlan, execute
from ..failures import EvidenceRef
from ..gates.l0_closure import (
    BoundaryAccounting, Direction, Exchange, QuantityAccount, ValueProvenance,
)
from ..lifecycle.reevaluation import stale_reliance
from ..lifecycle.unknown_expiry import (
    ExpiryTrigger, ExpiryTriggerKind, UnknownDetermination, UnknownState, check_expiry,
)
from ..reference.anchor import AnchorState
from ..validation.known_answer import KnownAnswerCase
from ..validation.null_harness import NullCase


ROOT = Path(__file__).resolve().parents[3]
CASE = "experimental/scope_audit_lab/reviews/tolman-vi-phase-trace-0.1"
PARENT = "experimental/scope_audit_lab/reviews/tolman-vi-2026-10-27"
ARTICLE = "https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w"
AUDIT_URL = "https://github.com/JinnZ2/study-aperture/blob/main/experimental/scope_audit_lab/reviews/tolman-vi-phase-trace-0.1/README.md"
VERSION = "audit-process-pilot/0.1"
# Newly inspected snapshot, not an automatically refreshed lock. Hashes establish
# byte identity, not scientific truth, source authenticity or independence.
PINNED = {
    f"{CASE}/run_trace.py": "762fed79e6ca31d1f451647f75e9a80ba15a88dc4dd3c3fee5db712b326f4a35",
    f"{CASE}/sources.json": "62c59fbd31722d3c2980cbe378b688670b68682851118c4d79e2e4759357e585",
    f"{CASE}/source-lock.json": "5b6156dfaf2dfdc26fc39e4d44364c41906e35077caad81dfae7a10dea72c43f",
    f"{CASE}/mappings.json": "b52cbeef0df92b4a9e457cac7b4bd864806b7f557d11fd0974b9cd301931f150",
    f"{CASE}/phase-trace.md": "9781cf23f77df8c12ba978d4c5e08703b4ca105075c4da6e662ca17b783cd01d",
    f"{CASE}/source-review.json": "29e5966292f03b6242a386c597030d07d24ea3f37fcdf6b9dd2338db489a6046",
    f"{CASE}/capture_sources.py": "17c1552e466cfcd3d691f826f0599b95c157c0e877ebc5f751720433d2d6d6d4",
    f"{CASE}/artifacts/verification.json": "70d347883c7c849e71b9f4b02ad95a031504ab8fc86535f782fd587a43b0b11b",
    f"{CASE}/artifacts/computed.json": "19101eb3fa221afd3bcb2e5eff4e77d66f85eb3bf958656fa98bd234ada3f612",
    f"{CASE}/artifacts/evidence-bundle.json": "7c90f8019d0fdf561e8312f8b7472119036331c3be8b3c20592cbefd204d533c",
    f"{CASE}/artifacts/integrity-report.json": "0ccd499a0f2887877b5fa664f26982034307d452c8649fc87d1bd35e1e526609",
    f"{CASE}/artifacts/integrity-report.md": "8f7240d68c57215493fbd97dd6281377c189527c2c41d7e47daf58273faf869b",
    f"{PARENT}/run_case.py": "6cef926cb871a384d07ba165402c641379327d4a84a56153456a80b5f9b4ed16",
    f"{PARENT}/study-record.json": "534ef964801c0711afad779282f30ebbab369fc2a8b2a7d3921e3de42dfca6a6",
    f"{PARENT}/source-extract.json": "da5129bf4f980d4ca84b65d967ead6f97d40eda09ca16b7c4aa0d9991ab4c206",
    f"{PARENT}/source-lock.json": "68200f0e6a8799d0581270ca81350d03a12bad2582f21cf45c20aa0fd2b6affb",
    "experimental/scope_audit_lab/integrity_checker.py": "22e14e247849531f91732c30404babb4c7f316e46a4f5e94f477ff66b3247f9b",
}
DECISION = Decision(
    "attributed-audit-process-pilot",
    "Inspect which inferences a preserved audit can support, not issue a whole-paper verdict.",
    "Hash-pinned offline replay; explicit mathematical scope, competing formal propositions and missing physical obligations.",
)
EVIDENCE = (EvidenceRef("preserved-audit", f"{CASE}/phase-trace.md",
                        PINNED[f"{CASE}/phase-trace.md"]),)
MISSING_PHYSICAL = (
    "physical-normalization", "valid-propagation-and-spin-derivation",
    "physical-boundary-and-closure", "calibrated-detector-response",
    "measured-dataset-and-propagated-uncertainty",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_snapshot(root=ROOT):
    examined = {}
    for name, expected in PINNED.items():
        actual = sha(root / name)
        if actual != expected:
            raise ValueError(f"Snapshot changed; explicit reinspection required: {name}")
        examined[name] = actual
    return examined


def plain(value):
    return json.loads(json.dumps(
        asdict(value), allow_nan=False,
        default=lambda x: x.value if isinstance(x, enum.Enum) else x,
    ))


def mathematical_experiment(mixing=0.75):
    """Formal probability normalization, never a physical mass/energy ledger."""
    anchor = AnchorState.from_maps(
        "formal-total-probability-reference", {"total_probability": 1.0},
        ("Mathematical normalization only; no physical reference state measured.",),
    )
    categories = (
        ("boundary", Domain.BOUNDARY, "selected-formal-two-state-probability-space"),
        ("observer", Domain.OBSERVER, "ideal-uniform-full-phase-period-average"),
        ("environment", Domain.ENVIRONMENT, "formal-coherent-real-two-flavor-model"),
        ("relationships", Domain.RELATIONSHIPS, "retain-mixing-prefactor-in-Eq35"),
        ("uncertainty", Domain.UNCERTAINTY, "formal-selected-input-no-physical-error-model"),
        ("anchor", Domain.ANCHOR, anchor.label),
    )
    context = Context(
        "tolman-formal-phase-average", "1",
        "Conditional Eq35 phase average, not an observed neutrino experiment.",
        anchor.digest(), tuple(
            Condition(k, domain, value, ConditionBasis.SELECTED, DECISION)
            for k, domain, value in categories
        ) + (Condition("mixing_amplitude", Domain.CONTROL, mixing,
                       ConditionBasis.SELECTED, DECISION, "1", 0.0),),
        "Selected M=sin^2(2theta); exact reduced inputs do not establish physical parameter certainty.",
    )
    rules = tuple(Constraint(k, d, DECISION, equals=v) for k, d, v in categories) + (
        Constraint("mixing_amplitude", Domain.CONTROL, DECISION, lower=0, upper=1, unit="1"),
    )
    ledger = BoundaryAccounting(
        categories[0][2], (QuantityAccount(
            "total_probability", 1.0, 1.0, ValueProvenance.SPECIFIED, ValueProvenance.SPECIFIED,
            (Exchange("total_probability", Direction.INFLOW, 0.0, "formal-control",
                      ValueProvenance.SPECIFIED, "control:mixing"),
             Exchange("total_probability", Direction.OUTFLOW, 0.0, "formal-readout",
                      ValueProvenance.SPECIFIED, "observer:average")), 0.0,
        ),), True, ("control:mixing", "observer:average"),
    )
    experiment = Experiment(context, anchor, BoundaryProtocol(
        context.digest(), anchor.digest(), ledger, (("total_probability", "1"),),
        (("control:mixing", "mixing_amplitude"), ("observer:average", "observer")), DECISION,
    ))
    return experiment, rules


def formal_models(rules):
    shared = dict(
        revision="1", inputs=(InputPort("M", "mixing_amplitude", "1"),),
        constraints=rules, decision=DECISION, evidence=EVIDENCE,
    )
    return (
        Equation("retained-mixing-average", property="Conditional full-phase average of Eq35",
                 outputs=(OutputPort("survival", "1-0.5*M", "1"),), **shared),
        Equation("universal-half-proposition", property="Scoped test proposition: average is half for every fixed mixing",
                 outputs=(OutputPort("survival", "0.5", "1"),), **shared),
    )


def plan(model, experiment):
    retained = model.equation_id == "retained-mixing-average"
    # These check implementation fidelity, not the truth of the proposition.
    answers = (1.0, 0.75, 0.5) if retained else (0.5, 0.5, 0.5)
    return ValidationPlan(
        f"{model.equation_id}-implementation-plan", model.digest(), experiment.context.digest(),
        tuple(KnownAnswerCase.from_maps(
            f"implementation-M-{m}", {"M": m}, {"survival": p}, {"survival": 0},
            "Hand-stated implementation answer only; competing proposition need not be true.",
        ) for m, p in zip((0.0, 0.5, 1.0), answers)),
        (NullCase.from_maps(
            "zero-mixing-input", {"M": 0}, {"survival": 1.0 if retained else 0.5},
            {"survival": 0}, "Input-null baseline of THIS implementation, not a physical absence claim.",
        ),), (("M", "1"),), (("survival", "1"),), DECISION, EVIDENCE,
    )


def execute_formal(model, experiment):
    registry = EquationRegistry()
    registry.register(model)
    return execute(registry, model.equation_id, model.revision, experiment,
                   plan(model, experiment), DECISION)


def replay_legacy(output_dir, root=ROOT):
    """Verify before execution and compare deterministic outputs, not timestamps."""
    examined = verify_snapshot(root)
    subprocess.run(
        [sys.executable, "-I", str(root / CASE / "run_trace.py"),
         "--output-dir", str(output_dir)],
        check=True, capture_output=True, text=True, timeout=120,
    )
    comparisons = {}
    for name in ("computed.json", "evidence-bundle.json", "integrity-report.json", "integrity-report.md"):
        fresh = sha(output_dir / name)
        frozen = PINNED[f"{CASE}/artifacts/{name}"]
        if fresh != frozen:
            raise ValueError(f"Replay differs from preserved artifact: {name}")
        comparisons[name] = {"fresh_sha256": fresh, "preserved_sha256": frozen, "byte_identical": True}
    return examined, comparisons


def inspect_process(computed, integrity):
    experiment, rules = mathematical_experiment()
    models = formal_models(rules)
    runs = tuple(execute_formal(model, experiment) for model in models)
    reference = runs[0]
    mathematical_support = Assessment(
        "restricted-mathematical-input", models[0].description().digest(),
        experiment.context.digest(), EvidenceKind.MATHEMATICAL, Judgment.SUPPORTS,
        DECISION, EVIDENCE, "Restricted derivation; no physical normalization or detector evidence.",
    )
    non_promotion = assess(
        models[0].description(), experiment.context, (mathematical_support,), reference.record,
    )
    changed_context = replace(experiment.context, revision="2", conditions=tuple(
        replace(c, value="ideal-uniform-radial-window") if c.key == "observer" else c
        for c in experiment.context.conditions
    ))
    changed_experiment = replace(experiment, context=changed_context, boundary=replace(
        experiment.boundary, context_digest=changed_context.digest(),
    ))
    changed_run = execute_formal(models[0], changed_experiment)
    # Planted probe, NOT an actual observation or claimed non-detection.
    hypothetical = NonDetectionObservation.from_map(
        "PLANTED-NOT-OBSERVED-no-effect", {"audit": VERSION, "response": "NOT_ESTABLISHED"}, 0.125,
    )
    absence = claim_absence("PLANTED-illicit-absence", record_non_detection(hypothetical, None))
    unknown = UnknownDetermination.from_map(
        "tolman-physical-detectability", "Physical detectability remains UNKNOWN.",
        {"publication": ARTICLE, "response": "NOT_ESTABLISHED"},
        (ExpiryTrigger("new-detector-response", ExpiryTriggerKind.NEW_EVIDENCE,
                       "Revisit when an actual calibrated response becomes available."),), EVIDENCE,
    )
    # A simulated trigger does not claim new detector evidence was acquired.
    expired = check_expiry(unknown, ("new-detector-response",))
    stale = stale_reliance({unknown.determination_id: expired.determination.state})
    physical_description = replace(
        models[0].description(), model_id="physical-detectability-obligations",
        property="Does this audit establish a physically detectable effect?",
        unknown_dependencies=MISSING_PHYSICAL,
    )
    obligations = assess(
        physical_description, experiment.context,
        dependency_states={dep: UnknownState.UNKNOWN for dep in MISSING_PHYSICAL},
    )
    # Explicit mathematical criterion, kept outside the physical failure axis.
    retained, half = (r.outputs[0].value for r in runs)
    return {
        "original_integrity_summary": integrity["summary"],
        "formal_runs": [r.to_dict() for r in runs],
        "formal_comparison": {
            "lane": "MATHEMATICAL_VALIDITY",
            "criterion": "Full-phase averaging alone gives half for every fixed mixing amplitude.",
            "attribution": "Scoped formalization, not a whole-paper or observed-physics proposition.",
            "selected_mixing_amplitude": 0.75,
            "retained_prefactor_average": retained, "universal_half_value": half,
            "absolute_difference": abs(retained - half),
            "criterion_outcome": "NOT_MET" if abs(retained - half) > 1e-12 else "MET",
            "implementation_fidelity": "Both implementations passed their own known-answer and input-null cases.",
            "interpretation": "A counterexample to the fixed-angle mathematical proposition, not a broken instrument or physical refutation.",
        },
        "replayed_phase_findings": computed["findings"],
        "first_replayed_trial_branches": computed["probability_trials"][0]["branches"],
        "kernel_change_probe": {
            "input_kind": "PLANTED_SCOPE_CHANGE_NOT_OBSERVATION",
            "run": changed_run.to_dict(),
        },
        "mathematical_to_physical_promotion_probe": plain(non_promotion),
        "absence_probe": {"input_kind": "PLANTED_NON_DETECTION_NOT_OBSERVATION",
                          "result_type": type(absence).__name__, "result": plain(absence)},
        "unknown_expiry_probe": {
            "input_kind": "SIMULATED_TRIGGER_NOT_NEW_EVIDENCE",
            "original": plain(unknown), "expiry": plain(expired), "stale_reliance": plain(stale),
        },
        "physical_obligations": plain(obligations),
        "physical_experiment": {
            "constructed": False,
            "reason": "No measured boundary/anchor, physical closure ledger, calibrated response or observational dataset supplied.",
            "missing": MISSING_PHYSICAL, "physical_status": "UNTESTED",
            "claim_support_promoted": False, "whole_paper_verdict": "NOT_ISSUED",
        },
        "applicability": build_map(
            tuple(m.description() for m in models), (experiment.context, changed_context),
        ).to_dict(),
    }


def markdown_report(report):
    inspection = report["inspection"]
    comparison = inspection["formal_comparison"]
    counts = inspection["original_integrity_summary"]["finding_counts"]
    claim = inspection["original_claim_and_decisions"]["claims"][0]
    return f"""# Tolman VI audit-process pilot

This is a fresh offline replay of a preserved audit, followed by an inspection
of its inference boundaries. It is not an independent scientific replication,
new detector experiment, corrected physical prediction or whole-paper verdict.

## What was reproduced

The preserved trace's four deterministic artifacts reproduced byte-for-byte.
Its integrity report still records {counts["ERROR"]} ERROR and
{counts["UNKNOWN"]} UNKNOWN findings; those unknowns were neither repaired
with invented registry records nor treated as physical refutation.
See the [preserved audit]({AUDIT_URL}).

The publication's original claim {claim["id"]} remains {claim["support"]},
with grade {claim["grade"]}. The two decisions about the discrepancy's origin
and the reliability of the proposed signature remain UNRESOLVED.
The replay does not silently settle either question.

## The process under inspection

The [article's Eq35]({ARTICLE}) retains a mixing-angle prefactor.
For the explicitly selected full-phase average and mixing amplitude
M=3/4, retaining that prefactor gives {comparison["retained_prefactor_average"]},
whereas the universal-half proposition gives {comparison["universal_half_value"]}.
The absolute difference is {comparison["absolute_difference"]}.
This is a mathematical counterexample within that fixed-angle scope, not a
measured neutrino effect or a claim that every physical equilibration mechanism
is excluded. An additional physical mechanism requires separate examination.

Both declarative implementations passed their own implementation-fidelity
harnesses. That success did not make both propositions true: the universal-half
criterion is NOT_MET under the selected formal conditions.
No physical-failure finding was manufactured from that mathematical mismatch.

## Inference boundaries exercised

- Mathematical evidence plus clean software diagnostics did not supply physical support.
- Changing the observer kernel from a uniform phase average to a radial window put the reduced formula outside its declared scope; calculation was blocked.
- A planted, explicitly hypothetical non-detection without sensitivity did not become an absence claim.
- A simulated UNKNOWN-expiry trigger required revision; stale reliance failed determination, not the physical description.
- A physical experiment was not manufactured: normalization, propagation/spin validity, physical boundary/closure, calibrated response and observed data remain unresolved.

The formal L0 ledger accounts only for total probability normalization.
It is not physical energy, mass or source-detector closure, and its selected
anchor is not a measured physical reference.

## What this establishes and what it does not

This pilot demonstrates inspectable behavior on one existing audit plus
explicitly labeled adversarial probes. It does not establish that these guardrails
improve audit accuracy generally, and does not supply independent validation
of the earlier mathematical derivations. Original audit bytes, claim support
and decision records remain unchanged.

The accompanying JSON retains source/code/artifact hashes, full gated runs,
selection decisions, source references, applicability, unresolved obligations
and the distinction between replayed records and planted probes.
"""


def run_pilot(output_dir, root=ROOT):
    output_dir = Path(output_dir).resolve()
    # Never overwrite legacy evidence, even if a caller supplies a bad target.
    if output_dir == root.resolve() or root.resolve() in output_dir.parents:
        raise ValueError("Pilot outputs must be outside the repository; use a new temporary directory")
    if output_dir.exists():
        raise FileExistsError("Output directory already exists; preserve previous evidence")
    verify_snapshot(root)  # fail before creating outputs or executing review code
    code_snapshot = {
        str(p.relative_to(root)): sha(p)
        for p in sorted((root / "experimental/playground").rglob("*.py"))
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    examined, comparisons = replay_legacy(output_dir / "legacy-replay", root)
    computed = json.loads((output_dir / "legacy-replay/computed.json").read_text())
    integrity = json.loads((output_dir / "legacy-replay/integrity-report.json").read_text())
    inspection = inspect_process(computed, integrity)
    study = json.loads((root / PARENT / "study-record.json").read_text())
    inspection["original_claim_and_decisions"] = {
        "claims": study["claims"], "decisions": study["decisions"],
        "source_sha256": PINNED[f"{PARENT}/study-record.json"],
        "bridge_to_physical_claim": "NOT_ESTABLISHED",
        "decision_promotion": False,
    }
    unchanged = verify_snapshot(root)
    if any(sha(root / name) != digest for name, digest in code_snapshot.items()):
        raise ValueError("Playground code changed during the pilot; do not issue a stable report")
    report = {
        "schema": VERSION, "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "article": ARTICLE, "selection": plain(DECISION),
        "pinned_sha256": examined, "legacy_artifact_comparisons": comparisons,
        "python_version": platform.python_version(), "diagnostic_code_sha256": code_snapshot,
        "original_snapshot_unchanged": unchanged == examined,
        "pilot_code_sha256": sha(Path(__file__)),
        "inspection": inspection,
        "limits": [
            "Same-repository reproducibility and planted inference probes, not independent scientific confirmation.",
            "Frozen source capture is content-bound, not independently authenticated or refreshed to the latest publication.",
            "No physical experiment, measured detector response, detection forecast or claim-support promotion.",
        ],
    }
    (output_dir / "tolman-vi-audit-process-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
    )
    (output_dir / "tolman-vi-audit-process-report.md").write_text(markdown_report(report))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_pilot(args.output_dir)
    print(json.dumps({
        "report": str(args.output_dir / "tolman-vi-audit-process-report.json"),
        "legacy_outputs_byte_identical": all(
            c["byte_identical"] for c in result["legacy_artifact_comparisons"].values()),
        "formal_comparison": result["inspection"]["formal_comparison"],
        "physical_experiment": result["inspection"]["physical_experiment"],
    }, indent=2))
