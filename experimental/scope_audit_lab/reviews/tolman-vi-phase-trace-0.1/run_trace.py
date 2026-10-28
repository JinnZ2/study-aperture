#!/usr/bin/env python3
"""Fixed offline probability/averaging trace, not an empirical prediction engine."""

import argparse
import cmath
import hashlib
import importlib.util
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
PARENT = HERE.parent/"tolman-vi-2026-10-27"
VERSION = "phase-trace-0.1.1"
PREFIX = "tolman-phase-trace:"
SOURCE = "https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w"


def old_case():
    spec = importlib.util.spec_from_file_location("previous_case", PARENT/"run_case.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_finite(*numbers):
    if not all(math.isfinite(x) for x in numbers):
        raise ValueError("Nonfinite input; no probability manufactured.")


def probability(theta, eikonal, spin=0.):
    require_finite(theta, eikonal, spin)
    total = eikonal + spin
    require_finite(total)
    return 1 - math.sin(2*theta)**2 * math.sin(total/2)**2


def probability_from_amplitude(theta, phi_k, phi_j):
    """Real two-state mixing, same-flavor amplitude before squaring."""
    require_finite(theta, phi_k, phi_j)
    amplitude = math.cos(theta)**2*cmath.exp(1j*phi_k) + math.sin(theta)**2*cmath.exp(1j*phi_j)
    return abs(amplitude)**2


def averaged_probability(theta):
    require_finite(theta)
    return 1 - .5*math.sin(2*theta)**2


def finite_uniform_phase_average(theta, center, width):
    require_finite(theta, center, width)
    if width < 0:
        raise ValueError("Nonnegative phase width required.")
    amplitude = math.sin(2*theta)**2
    half = width/2
    sinc = 1. if half == 0 else math.sin(half)/half
    return 1-amplitude/2 + amplitude/2*sinc*math.cos(center)


def uniform_radial_log_average(theta, coefficient, log_epsilon_over_rA):
    """Exact average for Phi=C ln(r/rA), r uniform on (0,epsilon).

    A mathematical response-kernel counterexample, not a physical detector model.
    """
    require_finite(theta, coefficient, log_epsilon_over_rA)
    phase = coefficient*log_epsilon_over_rA
    require_finite(phase)
    characteristic = cmath.exp(1j*phase)/(1+1j*coefficient)
    amplitude = math.sin(2*theta)**2
    return 1-amplitude/2+amplitude/2*characteristic.real


def source_boost(a, energy, mk, mj, left, right, orientation=1):
    require_finite(a, energy, mk, mj, left, right)
    if a <= 0 or energy <= 0 or min(left,right) <= 0 or min(mk,mj)<0:
        raise ValueError("Positive a/E/endpoints, nonnegative masses required.")
    if orientation not in {-1,1} or isinstance(orientation,bool):
        raise ValueError("Explicit spin-index orientation +1 or -1 required.")
    try:
        result = orientation*(mk-mj)*(math.log(right)-math.log(left))/(8*a**1.5*energy)
    except (OverflowError,ZeroDivisionError) as exc:
        raise ValueError("Boost expression outside finite arithmetic domain.") from exc
    require_finite(result)
    return result


def compute():
    old = old_case()
    parent = old.compute()
    trials = []
    theta = math.pi/6
    for prior in parent["numerical_trials"]:
        p = prior["inputs"]
        a = float(old.Fraction(p["a"]))
        energy, angular, mk, mj, left, right = [p[k] for k in ("E","L","mk","mj","r_A","r_B")]
        args = energy, angular, mk, mj, a
        exact = prior["eq8_difference_convergence"][-1]
        published = prior["eq13_endpoint_difference"]
        leading = old.simpson(lambda r: math.sqrt(a)*(mk**2-mj**2)/
                              (2*math.sqrt(old.domain(r,energy,angular,mk,mj))),left,right,1024)
        quartic = -old.simpson(lambda r: -math.sqrt(a)*(mk**4-mj**4)/
                               (8*old.domain(r,energy,angular,mk,mj)**1.5),left,right,1024)
        branches = []
        for orientation in (1,-1):
            spin = source_boost(a,energy,mk,mj,left,right,orientation)
            pub_p = probability(theta,published,spin)
            conditional_p = probability(theta,exact,spin)
            partial_flip_p = probability(theta,-published,spin)
            identity_rhs = math.sin(2*theta)**2*math.sin(published)*math.sin(spin)
            branches.append({
                "spin_orientation": orientation,
                "index_alignment": "Delta m_ij=+(mk-mj)" if orientation==1 else "Delta m_ij=-(mk-mj)",
                "source_boost_phase": spin,
                "published_probability": pub_p,
                "conditional_eq8_with_unchanged_boost_probability": conditional_p,
                "conditional_minus_published": conditional_p-pub_p,
                "partial_eikonal_sign_flip_probability": partial_flip_p,
                "partial_flip_minus_published": partial_flip_p-pub_p,
                "partial_flip_identity_rhs": identity_rhs,
                "global_phase_sign_flip_probability": probability(theta,-published,-spin),
                "complex_amplitude_probability": probability_from_amplitude(theta,published+spin,0),
            })
        trials.append({
            "inputs": p, "theta_radians":theta, "mixing_amplitude":math.sin(2*theta)**2,
            "leading_positive_eikonal_A":leading,"positive_quartic_magnitude_B":quartic,
            "source_eikonal_A_minus_B":published,
            "eq8_literal_eikonal":exact,
            "conditional_quartic_eikonal_minus_A_minus_B":-leading-quartic,
            "eikonal_only_source_probability":probability(theta,published),
            "eikonal_only_eq8_probability":probability(theta,exact),
            "eikonal_only_quartic_probability_delta":probability(theta,-leading-quartic)-probability(theta,leading-quartic),
            "quartic_delta_identity_rhs":-math.sin(2*theta)**2*math.sin(leading)*math.sin(quartic),
            "branches":branches,
            "limits":["Formal model-coordinate evaluation, not an SI-calibrated prediction or measured probability.",
                      "Holding Eq32 fixed while replacing Eq13 is a conditional branch, not an established correction.",
                      "Mass-index orientation is explicit; neither branch is automatically selected as the physical one."],
        })
    averaging = []
    for angle in (0,math.pi/12,math.pi/8,math.pi/6,math.pi/4):
        # Integrate the probability using an independent quadrature path.
        numeric = old.simpson(lambda phase:probability(angle,phase),0,2*math.pi,4096)/(2*math.pi)
        averaging.append({"theta_radians":angle,"phase_average":averaged_probability(angle),
                          "uniform_phase_quadrature":numeric,
                          "equals_one_half":abs(averaged_probability(angle)-.5)<=1e-14})
    radial = []
    coefficient=1.
    for n in (0,1,2,3):
        # Both subsequences tend to r=0 while the averaged probabilities differ.
        log_high=-2*math.pi*n
        log_low=-(2*n+1)*math.pi
        radial.append({
            "coefficient":coefficient,"n":n,
            "log_epsilon_over_rA_high":log_high,"log_epsilon_over_rA_low":log_low,
            "uniform_radial_average_high":uniform_radial_log_average(theta,coefficient,log_high),
            "uniform_radial_average_low":uniform_radial_log_average(theta,coefficient,log_low),
        })
    return {
        "procedure_version":VERSION,"formula":"P=1-sin^2(2theta)*sin^2((F+S)/2)",
        "probability_trials":trials,"uniform_phase_averaging":averaging,
        "finite_phase_windows":[{"width_radians":w,"center_radians":.7,
                                "mean_probability":finite_uniform_phase_average(theta,.7,w)}
                               for w in (0.,.2,math.pi,2*math.pi,20*math.pi)],
        "log_phase_response_counterexample":{
            "assumptions":"Ideal mathematical response uniform in r on (0,epsilon); Phi=C ln(r/rA); no eikonal term.",
            "characteristic_function":"<exp(i Phi)>=(epsilon/rA)^(iC)/(1+iC)",
            "residual_amplitude":"1/sqrt(1+C^2), independent of epsilon for fixed C",
            "subsequences":radial,
            "limit":"Counterexample to divergence alone guaranteeing full averaging; not a model of a measured detector.",
        },
        "findings":{
            "global_relative_phase_flip":"INVARIANT_WITHIN_STATED_TWO_FLAVOR_FORMULA",
            "eikonal_only_leading_sign_flip":"INVARIANT_IF_SPIN_AND_QUARTIC_TERMS_ARE_OMITTED",
            "partial_phase_flip_with_fixed_spin":"GENERALLY_NOT_INVARIANT",
            "quartic_eikonal_only":"SOURCE_AND_LITERAL_EQ8_ARE_NOT_EXACT_GLOBAL_NEGATIVES",
            "averaged_survival":"1-0.5*sin^2(2theta), not generically 0.5",
            "averaging_from_divergence_alone":"NOT_ESTABLISHED; response/ensemble kernel needed",
            "empirical_detectability":"NOT_EVALUATED",
            "corrected_physical_prediction":"NOT_ESTABLISHED",
        },
    }


def evidence_bundle(source, computed):
    old = old_case()
    def reference(name,kind):
        return {"record_id":PREFIX+name,"expected_type":kind,"resolution":"NOT_CHECKED"}
    def scope():
        value=old.scope()
        value["included"]=old.present("Eq35 two-flavor algebra, fixed sample branches, and specified averaging kernels.")
        value["excluded"]=old.present("Spin transport rederivation, measured detector response, 3-flavor/matter evolution, singularity extrapolation.")
        value["regime"]=old.present("Formal coherent two-flavor Eq35; nonsingular numerical trials; response-kernel counterexample is not a detector model.")
        return value
    def envelope(name,kind,payload):
        record=old.envelope(name,kind,payload)
        record.update(record_id=PREFIX+name,record_version=old.present(VERSION))
        record["source_refs"]=[reference("publisher-source","source")]
        record["producer"]["version"]=old.present(VERSION)
        return record
    records=[]
    for eq,latex in source["publisher"]["equations"].items():
        records.append(envelope(eq.lower(),"equation",{
            "exact_statement":latex,"statement_kind":"OTHER",
            "original":{"text":latex,"notation":"LATEX","source_location":old.present(SOURCE+"#"+eq),
                        "transcription_status":"REVIEWED","artifact_refs":[]},
            "transcription":old.na("Original selected HTML TeX retained."),
            "symbols":[],"scope":scope(),"assumption_refs":[],"dependency_refs":[],
            "ambiguities":["Spin mass-index alignment and physical phase normalization not independently derived."],
        }))
    derivations={
        "global-invariance":[
            ("P(F,S)=1-M*sin^2((F+S)/2); M=sin^2(2theta).", "Adopt the inspected Eq35 within its real, coherent two-state scope.", "UNSPECIFIED"),
            ("P(-F,-S)=1-M*sin^2(-(F+S)/2)=P(F,S).", "Use oddness of sine and evenness of its square; reverse both contributions.", "EQUIVALENT"),
        ],
        "universal-half":[
            ("<P>=1-M/2+(M/2)*Re<exp(i*Phi)>.", "Rewrite the sine square in Eq35 using the double-angle identity; keep fixed M.", "EQUIVALENT"),
            ("For uniform full-period phase averaging: <P>=1-M/2.", "Integrate exp(i*Phi) over a full uniformly weighted phase period.", "IMPLIES"),
            ("theta=pi/6 gives <P>=5/8, not 1/2; M=1 gives 1/2.", "Exhibit a nonmaximal-mixing counterexample without introducing population equilibration.", "IMPLIES"),
        ],
        "divergence-implies-averaging":[
            ("Phi=C*ln(r/rA); response w(r)=1/epsilon for 0<r<epsilon.", "Specify a purely mathematical normalized response, not a measured detector.", "UNSPECIFIED"),
            ("<exp(i*Phi)>=(epsilon/rA)^(iC)/(1+iC).", "Integrate (r/rA)^(iC) on (0,epsilon); the lower-end primitive has magnitude proportional to r.", "IMPLIES"),
            ("abs(<exp(i*Phi)>)=1/sqrt(1+C^2); for fixed C it does not decay as epsilon->0.", "Take the modulus; compare two shrinking-window subsequences at C=1.", "IMPLIES"),
        ],
    }
    for name,lines in derivations.items():
        steps=[]
        for i,(text,operation,relation) in enumerate(lines,1):
            steps.append({
                "step_id":"s"+str(i),
                "premise_refs":[reference("equ32" if name=="divergence-implies-averaging" else "equ35","equation")] if i==1 else [],
                "prior_step_ids":["s"+str(i-1)] if i>1 else [],
                "conclusion":{"text":text,"notation":"PLAIN_TEXT",
                              "source_location":old.present("Original local derivation in phase-trace.md; not a quoted author result."),
                              "transcription_status":"ORIGINAL_LOCAL","artifact_refs":[]},
                "operation":old.present(operation),"claimed_relation":relation,
                "assumption_refs":[],"introduced_assumption_refs":[],"assessment_refs":[],
            })
        records.append(envelope("derivation-"+name,"derivation",{
            "target_refs":[reference("equ35","equation")],"scope":scope(),"completeness":"PARTIAL",
            "steps":steps,
            "omitted_steps":old.present("Elementary field/integration axioms not expanded; no formal proof certificate."),
            "limitations":["Attributed local algebraic derivation, not a schema-established proof.",
                           "Explicit fixed-mixing and response assumptions are declared in the steps and report, not physically validated."],
        }))
    for i,trial in enumerate(computed["probability_trials"],1):
        value=trial["branches"][0]["conditional_minus_published"]
        records.append(envelope("trial-"+str(i),"observation",{
            "observation_kind":"NUMERICAL_RUN",
            "quantity":old.present("Conditional Eq8 plus unchanged Eq32 survival probability minus published Eq13 plus Eq32 value."),
            "value":{"status":"PRESENT","value":value,"encoding":"json_number"},
            "units":old.present("dimensionless, within formal Eq35; not a measured probability"),
            "scope":scope(),"method":old.present("run_trace.py; fixed phases; theta=pi/6; spin orientation +1."),
            "instrument":old.na("No physical apparatus."),"calibration":old.na("No physical instrument."),
            "resolution":old.na("No measured resolution."),
            "uncertainty":old.missing("No physical uncertainty or full floating-point interval model."),
            "observed_at":old.na("Run timestamp recorded separately; no physical observation time."),
            "condition_refs":[],"trial_ref":reference("execution-trial-"+str(i),"experiment"),
            "artifact_refs":[],"execution_refs":[],
            "limitations":["Both spin orientations retained in computed.json; this observation stores +1 only.","Not an established correction."],
        }))
    assessments=[
        ("global-invariance","The two-flavor survival probability is invariant under simultaneous F->-F and S->-S.","MET","ANALYTICAL"),
        ("partial-invariance","Keeping S fixed, reversing F leaves all recorded survival probabilities unchanged within 1e-12.",
         "MET" if all(abs(b["partial_flip_minus_published"])<=1e-12 for t in computed["probability_trials"] for b in t["branches"]) else "NOT_MET","NUMERICAL"),
        ("universal-half","Uniform phase averaging gives survival probability one-half for every recorded mixing angle.",
         "MET" if all(t["equals_one_half"] for t in computed["uniform_phase_averaging"]) else "NOT_MET","ANALYTICAL"),
        ("divergence-implies-averaging","A logarithmically divergent phase necessarily makes the specified radial-window average converge to the fully phase-averaged value.","NOT_MET","ANALYTICAL"),
        ("empirical-effect","A measured, calibrated, model-compatible probability dataset distinguishes the competing phase branches.","NOT_EVALUATED","EMPIRICAL"),
    ]
    for name,rule,outcome,kind in assessments:
        records.append(envelope("assessment-"+name,"assessment",{
            "assessment_kind":kind,
            "subjects":[{"subject":reference("equ35","equation"),"examined_version":old.present(VERSION),
                         "examined_state_artifact_refs":[],"selector":old.present("payload.exact_statement")}],
            "property":name,
            "procedure":{"identity":old.present("Attributed probability trace"),"version":old.present(VERSION),
                         "description":old.present("See phase-trace.md and computed.json; analytical identities and fixed bounded tests."),
                         "execution_refs":[],"verification_event_refs":[]},
            "dependency_refs":[reference("equ32","equation"),reference("equ13","equation")],
            "criteria":[{"criterion_id":name,"version":old.present(VERSION),"exact_rule":rule,
                         "scope":scope(),"outcome":outcome,
                         "evidence_refs":([reference("trial-"+str(i),"observation") for i in (1,2,3)] if kind=="NUMERICAL"
                                          else [reference("derivation-"+name,"derivation")] if kind=="ANALYTICAL" else []),
                         "missing_evidence":["Independent scientific review; authenticated registries; physical observation/response model."],
                         "rationale":"Restricted implication only; no universal verdict on the publication."}],
            "interpretation_refs":[],"limitations":["Case-specific authoring assessment, not a generic mapping executor or independent empirical reproduction."],
        }))
    return {"bundle_kind":"PHASE_TO_PROBABILITY_TRACE","records":records,
            "limits":["No source/trial registry entries invented.","Draft mappings are declarations only; property alignment not inferred by the general checker."]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",required=True,type=Path)
    args=p.parse_args()
    lock=json.loads((HERE/"source-lock.json").read_text())
    for name,digest in lock["examined_sha256"].items():
        if hashlib.sha256((LAB/name).read_bytes()).hexdigest()!=digest:
            raise ValueError("Source/parent implementation changed; explicit reinspection required: "+name)
    source=json.loads((HERE/"sources.json").read_text())
    computed=compute()
    bundle=evidence_bundle(source,computed)
    checker=old_case().load_checker()
    report=checker.check_records(bundle["records"])
    args.output_dir.mkdir(parents=True,exist_ok=False)
    for name,value in {"computed.json":computed,"evidence-bundle.json":bundle,"integrity-report.json":report}.items():
        (args.output_dir/name).write_text(json.dumps(value,indent=2,allow_nan=False)+"\n")
    (args.output_dir/"integrity-report.md").write_text(checker.markdown(report))
    examined=[Path(__file__),HERE/"capture_sources.py",HERE/"sources.json",HERE/"source-lock.json",
              HERE/"source-review.json",PARENT/"run_case.py",LAB/"integrity_checker.py"]
    manifest={
        "executed_at_utc":datetime.now(timezone.utc).isoformat(),"python":platform.python_version(),
        "procedure_version":VERSION,"checker_version":checker.VERSION,
        "examined_sha256":{str(f.relative_to(LAB)):hashlib.sha256(f.read_bytes()).hexdigest() for f in examined},
        "output_sha256":{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in args.output_dir.iterdir()},
        "execution_completed":True,"scientific_validity_established":False,
        "empirical_detectability":"NOT_EVALUATED","corrected_physical_prediction":"NOT_ESTABLISHED",
        "mapping_executor":"NOT_IMPLEMENTED; case-specific analytical review only",
        "prototype_0_1_compatibility":"UNKNOWN","voice":"DEFERRED",
    }
    (args.output_dir/"verification.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"findings":computed["findings"],"integrity":report["summary"],
                      "first_trial":computed["probability_trials"][0]},indent=2))


if __name__=="__main__":
    main()
