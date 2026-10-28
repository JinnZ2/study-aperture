#!/usr/bin/env python3
"""Fixed, offline study probes. Never evaluates or executes source-provided code."""

import argparse
import hashlib
import importlib.util
import json
import math
import platform
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
VERSION = "case-review-2"
URL = "https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w"
OLD = "urn:scope-audit-lab:schema:math-evidence:0.1"
PREFIX = "tolman-20261027:"


def present(value):
    return {"status": "PRESENT", "value": value}


def missing(reason):
    return {"status": "MISSING", "reason": reason}


def na(reason):
    return {"status": "NOT_APPLICABLE", "reason": reason}


def ref(name, kind):
    return {"record_id": PREFIX + name, "expected_type": kind, "resolution": "NOT_CHECKED"}


def load_checker():
    spec = importlib.util.spec_from_file_location("case_integrity_checker", LAB / "integrity_checker.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def simpson(function, left, right, steps):
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 2 or steps % 2:
        raise ValueError("An even positive integer >= 2 is required.")
    if not (math.isfinite(left) and math.isfinite(right) and left < right):
        raise ValueError("Finite ordered endpoints required.")
    h = (right - left) / steps
    values = [function(left + i * h) for i in range(steps + 1)]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Nonfinite integrand; no successful result manufactured.")
    return h / 3 * math.fsum(
        v * (1 if i in {0, steps} else 4 if i % 2 else 2)
        for i, v in enumerate(values)
    )


def domain(r, energy, angular, mk, mj):
    if not all(math.isfinite(x) for x in (r, energy, angular, mk, mj)):
        raise ValueError("Finite values required.")
    if r <= 0 or energy <= 0 or min(mk, mj) < 0:
        raise ValueError("Positive radius/energy, nonnegative masses required.")
    q = energy**2 / r - angular**2 / r**2
    if q <= max(mk**2, mj**2):
        raise ValueError("Strictly inside both square-root domains required.")
    return q


def exact_difference(r, energy, angular, mk, mj, a):
    """Eq8(k)-Eq8(j); rationalized to avoid subtraction cancellation."""
    q = domain(r, energy, angular, mk, mj)
    if not math.isfinite(a) or a <= 0:
        raise ValueError("Positive a required.")
    return math.sqrt(a) * (mj**2 - mk**2) / (
        math.sqrt(q - mk**2) + math.sqrt(q - mj**2))


def expansion(r, energy, angular, mk, mj, a, source=True):
    q = domain(r, energy, angular, mk, mj)
    if not math.isfinite(a) or a <= 0:
        raise ValueError("Positive a required.")
    # Source Eq12 has a positive quadratic term and negative quartic term.
    # Expanding Eq8(k)-Eq8(j) literally gives two negative terms.
    first = (mk**2 - mj**2) / (2 * math.sqrt(q))
    fourth = -(mk**4 - mj**4) / (8 * q**1.5)
    return math.sqrt(a) * ((first if source else -first) + fourth)


def primitive13(r, energy, angular, mk, mj, a):
    domain(r, energy, angular, mk, mj)
    s = (angular / energy)**2
    u = math.sqrt(r - s)
    return math.sqrt(a) / energy * (
        (r + 2*s)*u*(mk**2 - mj**2)/3
        - (r**3 + 2*s*r**2 + 8*s*s*r - 16*s**3)
        * (mk**4 - mj**4)/(20*energy**2*u)
    )


def compute():
    a = Fraction(7, 4)
    coefficients = {"rho": a-1, "pr": 2-a, "pt": Fraction(1, 4)}
    rational_pass = coefficients["pr"] == coefficients["pt"] == coefficients["rho"]/3
    trace = -coefficients["rho"] + coefficients["pr"] + 2*coefficients["pt"]
    trials = []
    for energy, angular, mk, mj, left, right in (
        (10., 1., .2, .1, 1., 2.),
        (20., 0., .1, .05, 2., 4.),
        (15., 2., .15, .03, 1., 3.),
    ):
        args = energy, angular, mk, mj, float(a)
        exact = [simpson(lambda r: exact_difference(r, *args), left, right, n)
                 for n in (256, 512, 1024)]
        reported = simpson(lambda r: expansion(r, *args), left, right, 1024)
        conditional = simpson(lambda r: expansion(r, *args, source=False), left, right, 1024)
        endpoint = primitive13(right, *args) - primitive13(left, *args)
        # For these chosen intervals q decreases monotonically, so endpoints bound x=m^2/q.
        q_min = min(domain(r, energy, angular, mk, mj) for r in (left, right))
        x_max = max(mk**2, mj**2)/q_min
        remainder_bound = (
            math.sqrt(float(a)) * (right-left) * (mk**6+mj**6)
            / (16*q_min**2.5*(1-x_max)**2.5)
        )
        trials.append({
            "inputs": dict(a=str(a), E=energy, L=angular, mk=mk, mj=mj,
                           r_A=left, r_B=right, interpretation="model-coordinate numbers, not SI measurements"),
            "method": "Composite Simpson; CPython float; no submitted source code execution.",
            "steps": [256, 512, 1024], "eq8_difference_convergence": exact,
            "max_expansion_parameter_m2_over_q": x_max,
            "eq12_source_expansion": reported,
            "eq8_literal_taylor_comparison": conditional,
            "eq13_endpoint_difference": endpoint,
            "eq12_minus_eq8": reported-exact[-1],
            "literal_taylor_minus_eq8": conditional-exact[-1],
            "eq13_minus_eq12": endpoint-reported,
            "conditional_taylor_remainder_bound": remainder_bound,
            "tolerance": 1e-10,
            "source_sign_agreement": math.copysign(1, reported) == math.copysign(1, exact[-1]),
            "eq12_eq13_sampled_agreement": abs(endpoint-reported) <= 1e-10,
            "convergence_difference_below_tolerance": abs(exact[-1]-exact[-2]) <= 1e-10,
        })
    return {
        "coefficient_check": {
            "a": str(a), "common_factor": "1/(a*r^2), r>0",
            "coefficients": {k: str(v) for k,v in coefficients.items()},
            "pressure_isotropy_and_p_equals_rho_over_3": rational_pass,
            "trace_coefficient": str(trace), "trace_zero": trace == 0,
            "limit": "Exact rational coefficient identity, not an Einstein-tensor derivation or empirical check.",
        },
        "numerical_trials": trials,
        "analytical_comparison": {
            "definition": "q=E^2/r-L^2/r^2; q>max(mk^2,mj^2); Delta m^n=mk^n-mj^n",
            "literal_eq8_difference": "sqrt(a)*[-Delta m^2/(2*sqrt(q))-Delta m^4/(8*q^(3/2))+O(m^6/q^(5/2))]",
            "published_eq12": "sqrt(a)*[+Delta m^2/(2*sqrt(q))-Delta m^4/(8*q^(3/2))]",
            "status": "CANDIDATE_INTERNAL_SIGN_DISCREPANCY",
            "limits": "Conditional on published equations and stated mass/phase ordering. No global correction or physical consequence established.",
        },
    }


def scope():
    return {
        "domain": present("Selected equations of the published Tolman VI theoretical model."),
        "included": present("a=7/4 rational coefficients; three admissible phase-integral comparisons."),
        "excluded": present("Full proof audit, empirical neutrino observations, singular-center extrapolation."),
        "regime": present("Static spherical metric, positive r; selected WKB/eikonal formulas; small m^2/q."),
        "boundary_conditions": missing("No astrophysical matching to an external solution examined."),
        "initial_conditions": missing("No physical source/detector realization examined."),
    }


def envelope(name, kind, payload):
    return {
        "schema_id": OLD, "schema_version": "0.1", "record_id": PREFIX+name,
        "record_type": kind, "record_version": present(VERSION),
        "source_refs": [ref("publisher-source", "source")],
        "recorded_at": missing("This authoring record is not an instrument acquisition."),
        "producer": {"identity": present("study-aperture local authoring review"), "kind": "PROCESS",
                     "version": present("run_case.py / "+VERSION)},
        "relations": [], "payload": payload,
    }


def evidence_bundle(source, computed):
    records = []
    for key, latex in source["equations"].items():
        records.append(envelope(key.lower(), "equation", {
            "exact_statement": latex, "statement_kind": "APPROXIMATION" if key in {"Equ12","Equ13","Equ14"} else "OTHER",
            "original": {"text": latex, "notation": "LATEX", "source_location": present(URL+"#"+key),
                         "transcription_status": "REVIEWED", "artifact_refs": []},
            "transcription": na("Original HTML TeX retained; no repaired expression substituted."),
            "symbols": [], "scope": scope(), "assumption_refs": [], "dependency_refs": [],
            "ambiguities": ["Only selected PDF equations on pages 4-5 visually cross-checked; full typography and coordinate-unit normalization not audited."],
        }))
    for index, trial in enumerate(computed["numerical_trials"], 1):
        payload = {
            "observation_kind": "NUMERICAL_RUN",
            "quantity": present("eq12_source_expansion minus eq8_difference in local phase comparison"),
            "value": {"status":"PRESENT","value":trial["eq12_minus_eq8"],"encoding":"json_number"},
            "units": present("model-coordinate phase convention; not an SI measurement"),
            "scope": scope(), "method": present("run_case.py; fixed composite Simpson comparison at 1024 steps"),
            "instrument": na("Local computational run, not physical apparatus."),
            "calibration": na("No physical instrument."), "resolution": na("No sensor resolution."),
            "uncertainty": missing("Convergence evidence is separate; no full floating-point interval or physical uncertainty model."),
            "observed_at": na("Run time is in verification.json; no physical measurement time."),
            "condition_refs": [], "trial_ref": ref("execution-trial-"+str(index), "experiment"),
            "artifact_refs": [], "execution_refs": [],
            "limitations": ["Computed output from selected source formulas, not measured neutrino behavior."],
        }
        records.append(envelope("trial-"+str(index), "observation", payload))
    criteria = [
        ("exact-coefficients", "Isotropy and trace identities from equation 2 at a=7/4 after removal of nonzero common factor.",
         "MET" if computed["coefficient_check"]["trace_zero"] else "NOT_MET", "equ2", "ANALYTICAL"),
        ("phase-expansion", "Literal Eq8(k)-Eq8(j) and Eq12 agree in sign at the recorded admissible small-parameter inputs.",
         "MET" if all(t["source_sign_agreement"] for t in computed["numerical_trials"]) else "NOT_MET", "equ12", "NUMERICAL"),
        ("primitive-samples", "Eq12 quadrature and Eq13 endpoints differ by at most 1e-10 at three recorded inputs.",
         "MET" if all(t["eq12_eq13_sampled_agreement"] for t in computed["numerical_trials"]) else "NOT_MET", "equ13", "NUMERICAL"),
        ("coordinate-units", "Restore and inspect all coordinate and unit normalizations before an SI dimension verdict.",
         "INDETERMINATE", "equ1", "ANALYTICAL"),
        ("empirical", "Inspect actual new neutrino observations compatible with the proposed signature.",
         "NOT_EVALUATED", "equ7", "EMPIRICAL"),
    ]
    for name, rule, outcome, subject, kind in criteria:
        evidence = [ref("trial-"+str(i), "observation") for i in (1,2,3)] if kind=="NUMERICAL" else (
            [ref(subject,"equation")] if name=="exact-coefficients" else [])
        records.append(envelope("assessment-"+name, "assessment", {
            "assessment_kind": kind,
            "subjects": [{"subject":ref(subject,"equation"),"examined_version":present(VERSION),
                          "examined_state_artifact_refs":[],"selector":present("payload.exact_statement")}],
            "property": name,
            "procedure": {"identity":present("bounded authoring review"), "version":present(VERSION),
                          "description":present("See computed.json, source-extract.json, and study-assessment.pplx.md; no generic prover."),
                          "execution_refs":[],"verification_event_refs":[]},
            "dependency_refs": [ref("equ8","equation"),ref("equ12","equation")] if name=="phase-expansion" else [],
            "criteria": [{"criterion_id":name,"version":present(VERSION),"exact_rule":rule,"scope":scope(),
                          "outcome":outcome,"evidence_refs":evidence,
                          "missing_evidence": ["Independent verification, authenticated source/artifact registry, full uncertainty treatment."] if outcome in {"MET","NOT_MET"} else ["Qualifying evidence/procedure not established."],
                          "rationale":"Attributed limited authoring assessment; no whole-paper verdict."}],
            "interpretation_refs":[],
            "limitations":["Generic source/artifact/verification-event registries are not implemented; computed artifacts are linked by the sidecar manifest."],
        }))
    return {"bundle_kind":"WORKED_THEORETICAL_STUDY_ASSESSMENT","records":records,
            "source_url":URL, "source_registry_status":"UNRESOLVED; URL and captured extract retained separately.",
            "limits":["A source record was not fabricated to remove an integrity gap. Assessment records do not automatically establish their conclusions."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    source_file = HERE/"source-extract.json"
    source = json.loads(source_file.read_text())
    # A changed source must trigger explicit reinspection, not silently reuse the transcription.
    lock = json.loads((HERE/"source-lock.json").read_text())
    if hashlib.sha256(source_file.read_bytes()).hexdigest() != lock["source_extract_sha256"]:
        raise ValueError("Source extract changed; review/rebind before executing.")
    computed = compute()
    bundle = evidence_bundle(source, computed)
    checker = load_checker()
    report = checker.check_records(bundle["records"])
    outputs = {"computed.json":computed, "evidence-bundle.json":bundle, "integrity-report.json":report}
    for name, value in outputs.items():
        (args.output_dir/name).write_text(json.dumps(value,indent=2,allow_nan=False)+"\n")
    (args.output_dir/"integrity-report.md").write_text(checker.markdown(report))
    examined = [Path(__file__), HERE/"extract_source.py", source_file, HERE/"source-lock.json", HERE/"pdf-inspection.json",
                HERE/"mappings.json", LAB/"integrity_checker.py"]
    manifest = {
        "executed_at_utc":datetime.now(timezone.utc).isoformat(), "python":platform.python_version(),
        "procedure_version":VERSION, "checker_version":checker.VERSION,
        "source_url":URL, "study_publication_date":"2026-10-27",
        "today_interpretation":"2026-10-27 America/Chicago; execution may be Oct28 UTC.",
        "mapping_status":"DRAFT_NOT_EXECUTABLE; case-specific conclusions are attributed authoring assessments.",
        "examined_sha256":{str(p.relative_to(LAB)):hashlib.sha256(p.read_bytes()).hexdigest() for p in examined},
        "output_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.output_dir.iterdir())},
        "execution_completed":True, "scientific_validity_established":False,
        "empirical_reproduction":"NOT_PERFORMED", "prototype_0_1_compatibility":"UNKNOWN","voice":"DEFERRED",
        "limits":["Fixed selected formulas only; no full derivation audit, formal proof, GR tensor derivation, or physical experiment.",
                  "Simpson convergence is diagnostic, not a rigorous quadrature/roundoff interval bound.",
                  "Source and artifact registries remain unresolved in the evidence checker; the manifest is not source authentication."],
    }
    (args.output_dir/"verification.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"coefficient_check":computed["coefficient_check"],"trials":computed["numerical_trials"],
                      "integrity_summary":report["summary"]},indent=2))


if __name__ == "__main__":
    main()
