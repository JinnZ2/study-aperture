#!/usr/bin/env python3
"""Authoring-only synthetic fixture generator; stdout, standard library only."""

import copy
import json
from pathlib import Path


LAB = Path(__file__).resolve().parent.parent.parent
OLD = "urn:scope-audit-lab:schema:math-evidence:0.1"
NEW = "urn:scope-audit-lab:schema:math-physics-extensions:0.2"
VERSION = "fixture-0.2-1"
BASIS = ["mass", "length", "time", "electric_current",
         "thermodynamic_temperature", "amount_of_substance", "luminous_intensity"]


def present(value):
    return {"status": "PRESENT", "value": value}


def missing(reason):
    return {"status": "MISSING", "reason": reason}


def na(reason):
    return {"status": "NOT_APPLICABLE", "reason": reason}


def number(value):
    return {"status": "PRESENT", "value": value, "encoding": "json_number"}


def ref(name, kind, resolution="NOT_CHECKED"):
    return {"record_id": "physics-draft:" + name,
            "expected_type": kind, "resolution": resolution}


def scope(domain="Synthetic fixed-boundary illustration; not an examined device."):
    return {
        "domain": present(domain),
        "included": present("Only the explicitly stated reference relation or synthetic case."),
        "excluded": present("Empirical validation and applicability outside the declared formalism."),
        "regime": present("Classical/nonrelativistic where a physical interpretation is proposed."),
        "boundary_conditions": missing("No independently established physical boundary conditions."),
        "initial_conditions": missing("No independently established initial conditions."),
    }


def representation(statement):
    return {
        "text": statement, "notation": "PLAIN_TEXT",
        "source_location": present(
            "Editorial formulation in build_examples.py; not a verbatim source quotation."
        ),
        "transcription_status": "ORIGINAL_LOCAL", "artifact_refs": [],
    }


def envelope(name, kind, payload, old=False):
    return {
        "schema_id": OLD if old else NEW,
        "schema_version": "0.1" if old else "0.2",
        "record_id": "physics-draft:" + name,
        "record_type": kind, "record_version": present(VERSION),
        "source_refs": [],
        "recorded_at": missing("No instrument acquisition timestamp asserted."),
        "producer": {
            "identity": present("study-aperture synthetic schema authoring"),
            "kind": "PROCESS", "version": present("build_examples.py / proposed-1"),
        },
        "relations": [], "payload": payload,
    }


def citation(key, url, title, locator, version=None):
    return {
        "citation_id": key, "url": url, "title": title, "locator": locator,
        "publication_version": present(version) if version else missing(
            "Publication version not established from the inspected extract."
        ),
        "inspection_status": "TEXT_EXTRACT_INSPECTED",
        "source_record": ref("source-" + key, "source", "UNRESOLVED"),
        "inspection_limits": (
            "Fetched text/extracted equations inspected; original page rendering "
            "not inspected, not reproduced empirically. URL content is not bundled."
        ),
    }


MIT_ENERGY = citation(
    "mit-energy-2020",
    "https://ocw.mit.edu/courses/2-60j-fundamentals-of-advanced-energy-conversion-spring-2020/54a791b898a31befeea178f796efcd9c_MIT2_60s20_lec2.pdf",
    "MIT 2.60, Fundamentals of Advanced Energy Conversion, Lecture 2",
    "Energy and entropy control-volume balances",
    "Spring 2020 lecture resource",
)
MIT_MOMENTUM = citation(
    "mit-sonin",
    "https://web.mit.edu/2.25/www/pdf/fundamental_laws.pdf",
    "Ain A. Sonin, Fundamental Laws of Motion for Particles, Material Volumes, and Control Volumes",
    "Material-volume linear momentum; Eq. (19)",
    "Revised September 2001, as identified in fetched extract",
)
NASA_MOMENTUM = citation(
    "nasa-newton",
    "https://www.grc.nasa.gov/WWW/K-12/BGP/newton2.html",
    "NASA Glenn, Newton's Second Law",
    "Momentum formulation and constant-mass specialization",
)
MIT_ENTROPY = citation(
    "mit-entropy-2010",
    "https://ocw.mit.edu/courses/22-081j-introduction-to-sustainable-energy-fall-2010/411beca04e9b15f5ca2caed33b4a801d_MIT22_081JF10_lec09a.pdf",
    "MIT Introduction to Sustainable Energy, Thermodynamics",
    "Entropy generation restriction and heat-engine second-law example",
    "Fall 2010 course resource; lecture date September 22, 2010 in extract",
)


def anchor(name, title, kind, statement, formalism, requirements,
           sources, exclusions, hazards):
    conditions = []
    for condition_id, rule, editorial, source_keys in requirements:
        conditions.append({
            "condition_id": condition_id, "exact_requirement": rule,
            "basis": "EDITORIAL_SCOPE_RESTRICTION" if editorial else "SOURCE_EXPLICIT",
            "citation_ids": source_keys,
            "rationale": (
                "Conservative scope chosen for this starter anchor; not a universal necessity."
                if editorial else "Condition belongs to the cited reference formulation."
            ),
        })
    result = envelope(name, "physics_anchor", {
        "name": title, "anchor_kind": kind,
        "reference_statement": representation(statement),
        "formalism": present(formalism),
        "scope": scope(formalism),
        "conditions": conditions, "source_citations": sources,
        "scope_exclusions": exclusions, "application_hazards": hazards,
        "limitations": [
            "Source-backed reference formulation; no applicability to a particular device established.",
            "Inline citations do not create resolved standalone source or artifact records.",
            "Editorial scope restrictions are identified separately from source-explicit conditions.",
        ],
    })
    result["source_refs"] = [s["source_record"] for s in sources]
    return result


def quantity(name, symbol, meaning, exponents, unit):
    return envelope(name, "quantity_definition", {
        "symbol": symbol, "meaning": meaning,
        "quantity_kind": present(meaning),
        "structure": {
            "status": "PRESENT", "kind": "SCALAR", "component_shape": [],
            "frame": missing("No measured frame established."),
            "spatial_support": missing("No measured spatial support established."),
            "temporal_support": missing("No measurement interval established."),
        },
        "dimensions": {
            "status": "PRESENT", "basis_id": "ISQ-seven-base-declared-v1",
            "basis_order": BASIS,
            "exponents": [{"numerator": n, "denominator": 1} for n in exponents],
        },
        "unit": {
            "status": "PRESENT", "symbol": unit, "system": present("SI declared"),
            "role": "LINEAR_INTERVAL", "reference_unit": present(unit),
            "scale_to_reference": number(1), "offset_to_reference": number(0),
            "conversion_rule": present("Identity declaration only; no conversion executed."),
        },
        "scope": scope(), "declaration_refs": [],
        "limitations": ["Author-declared fixture quantity, not an independently checked observation."],
    })


def binding(key, source, quantity_name="power"):
    return {
        "binding_id": key,
        "input": ref(source, "observation") if source else missing("No input record supplied."),
        "selector": present("payload.value"),
        "examined_version": present(VERSION) if source else missing("No input version."),
        "state_artifact_refs": [],
        "quantity_definition": ref(quantity_name, "quantity_definition"),
    }


def requirement(key, rule):
    return {
        "requirement_id": key, "exact_requirement": rule,
        "outcome": "NOT_EVALUATED", "evidence_refs": [],
        "missing_evidence": ["Completed, recorded check of this requirement."],
        "rationale": "Draft fixture, not an assertion of an executed check.",
    }


def build():
    old_bundle = json.loads(
        (LAB / "examples/schema-draft-0.1/records.json").read_text()
    )
    template_obs = next(r for r in old_bundle["records"] if r["record_type"] == "observation")
    template_assessment = next(r for r in old_bundle["records"] if r["record_type"] == "assessment")
    energy = anchor(
        "energy-anchor", "Classical fixed-control-volume energy balance", "BALANCE_LAW",
        "dE_CV/dt = Qdot_in - Wdot_out + sum_in mdot*(h+v^2/2+g*z) - sum_out mdot*(h+v^2/2+g*z).",
        "Classical continuum thermodynamics; fixed control volume; uniform g*z potential specialization.",
        [
            ("E-boundary", "Define a fixed control volume and all crossing mass/energy transfers.", False, ["mit-energy-2020"]),
            ("E-signs", "Qdot is positive into the volume and Wdot positive out; avoid double counting flow work already represented by h.", False, ["mit-energy-2020"]),
            ("E-stored", "Retain the time rate of stored energy unless a zero-storage-rate condition is justified.", False, ["mit-energy-2020"]),
            ("E-formalism", "Use this starter only in its declared classical continuum and uniform-g potential formulation.", True, ["mit-energy-2020"]),
            ("E-inventory", "Document included energy forms and transfer mechanisms; no unrecorded transfer may be assumed zero.", True, []),
        ],
        [MIT_ENERGY],
        ["Relativistic, cosmological, and quantum formulations are not covered by this starter anchor.",
         "Moving-boundary variants require a separately stated formulation."],
        ["Missing stored energy is not zero stored-energy change.",
         "A convenient split into heat, work, and flow terms must be checked for omissions and double counting.",
         "A model residual does not independently establish a violation of energy conservation."],
    )
    momentum = anchor(
        "momentum-anchor", "Classical material-system linear momentum balance", "DYNAMICAL_LAW",
        "P = integral_over_material_system rho*v dV; dP/dt = sum_external F, in a declared inertial frame.",
        "Classical nonrelativistic mechanics; material system with explicitly included matter.",
        [
            ("P-system", "The selected material system follows the same matter.", False, ["mit-sonin"]),
            ("P-frame", "Evaluate momenta and external forces in an inertial frame.", False, ["mit-sonin"]),
            ("P-forces", "Declare external interactions and the system whose internal forces cancel in the selected formulation.", False, ["mit-sonin"]),
            ("P-mass", "Use F=m*a only as a justified constant-mass specialization, not as a shortcut for an open rocket subsystem.", False, ["nasa-newton"]),
            ("P-formalism", "Restrict this starter to classical nonrelativistic matter mechanics.", True, ["mit-sonin"]),
        ],
        [MIT_MOMENTUM, NASA_MOMENTUM],
        ["Open-control-volume momentum fluxes require a separately stated balance.",
         "Relativistic and field-momentum formulations are outside this starter's coverage."],
        ["Missing forces are not zero forces.",
         "A closed material-system equation cannot silently validate a variable-membership subsystem."],
    )
    entropy = anchor(
        "entropy-anchor", "Classical control-volume entropy balance and nonnegative generation", "THERMODYNAMIC_INEQUALITY",
        "dS_CV/dt = sum_j Qdot_j/T_boundary_j + sum_in mdot*s - sum_out mdot*s + Sdot_gen; Sdot_gen >= 0.",
        "Classical continuum/local-equilibrium thermodynamic model with defined entropy states.",
        [
            ("S-boundary", "Define the system boundary and account for entropy transfers by heat and mass.", False, ["mit-energy-2020"]),
            ("S-temperature", "Use the relevant absolute boundary temperature for each heat-transfer term.", False, ["mit-energy-2020"]),
            ("S-generation", "Separate entropy transfer from generation; the reference generation restriction is nonnegative.", False, ["mit-entropy-2010"]),
            ("S-isolation", "Do not infer dS/dt>=0 for an arbitrary subsystem by omitting its entropy-transfer terms.", True, ["mit-energy-2020"]),
            ("S-formalism", "Require a declared continuum/local-equilibrium entropy description for this starter.", True, []),
        ],
        [MIT_ENERGY, MIT_ENTROPY],
        ["Microscopic stochastic-trajectory and other alternative entropy formalisms need separate anchors.",
         "No classification of an uninstrumented subsystem as isolated is supplied."],
        ["A subsystem entropy decrease is not by itself a negative-generation observation.",
         "Do not treat useful heat transfer, entropy transfer, and entropy generation as interchangeable quantities."],
    )
    records = [
        energy, momentum, entropy,
        quantity("power", "P", "energy transfer or storage rate", [1, 2, -3, 0, 0, 0, 0], "W"),
        quantity("dimension-one", "e", "dimension-one scalar error ratio", [0, 0, 0, 0, 0, 0, 0], "1"),
        quantity("angle", "theta", "plane angle", [0, 0, 0, 0, 0, 0, 0], "rad"),
    ]
    for name, label, value in (
        ("power-in", "stipulated total incoming power", 100),
        ("power-out", "stipulated total outgoing power", 120),
        ("storage-rate", "unmeasured stored-energy time rate", None),
    ):
        obs = copy.deepcopy(template_obs)
        obs.update({k: v for k, v in envelope(name, "observation", {}, old=True).items() if k != "payload"})
        obs["payload"].update({
            "quantity": present(label), "scope": scope(),
            "value": number(value) if value is not None else missing("No storage-rate measurement supplied."),
            "units": present("W"),
            "method": present("Authored synthetic fixture; not a measurement or executed numerical model."),
            "uncertainty": missing("No uncertainty model supplied."),
        })
        records.append(obs)
    inputs = [binding("storage", "storage-rate"), binding("incoming", "power-in"), binding("outgoing", "power-out")]
    records.append(envelope("residual", "calculation", {
        "purpose": "Record prerequisites for r = storage - (incoming - outgoing).",
        "method": {
            "identity": present("specified scalar subtraction"),
            "version": present("proposed-1"),
            "expression": present("r = storage - incoming + outgoing"),
            "numerical_representation": missing("No runtime numerical backend selected."),
        },
        "inputs": inputs, "scope": scope(),
        "prerequisites": [requirement("storage-available", "A valid storage rate and compatible input units are supplied.")],
        "execution_status": "NOT_EXECUTED", "execution_refs": [],
        "result": missing("The storage-rate input is missing; no residual was executed."),
        "result_quantity": ref("power", "quantity_definition"),
        "uncertainty": missing("No covariance or uncertainty inputs supplied."),
        "dependency_refs": [ref("balance", "balance_specification")],
        "assessment_refs": [],
        "limitations": ["No inference of conservation failure or root cause."],
    }))
    terms = []
    for key, role, expression, coefficient, observation in (
        ("storage", "STORAGE", "dE/dt", 1, "storage-rate"),
        ("incoming", "TRANSFER", "P_in", -1, "power-in"),
        ("outgoing", "TRANSFER", "P_out", 1, "power-out"),
    ):
        terms.append({
            "term_id": key, "role": role, "expression": present(expression),
            "coefficient": number(coefficient),
            "quantity_definition": ref("power", "quantity_definition"),
            "input_refs": [ref(observation, "observation")], "inclusion": "INCLUDED",
            "rationale": "Authored aggregate balance term, not a verified inventory.",
            "evidence_refs": [],
        })
    records.append(envelope("balance", "balance_specification", {
        "anchor": ref("energy-anchor", "physics_anchor"),
        "system": {
            "identity": present("synthetic-box"), "version": present(VERSION),
            "boundary_kind": "FIXED_CONTROL_VOLUME",
            "boundary_description": present("Synthetic fixed boundary; physical transfer inventory unverified."),
            "frame": missing("No independently established frame."),
            "spatial_support": missing("No measured geometry."),
            "temporal_support": missing("No measurement interval."),
            "steady_state_basis": missing("Steady state not established."),
            "evidence_refs": [],
        },
        "scope": scope(), "balanced_quantity": ref("power", "quantity_definition"),
        "relation": representation("storage - incoming + outgoing = 0"),
        "term_inventory_status": "UNKNOWN", "terms": terms,
        "missing_term_policy": "REQUIRE_EXPLICIT_JUSTIFICATION",
        "assumption_refs": [], "assessment_refs": [],
        "limitations": [
            "Aggregate incoming/outgoing terms have not been mapped exhaustively to the anchor channels.",
            "Included storage term has a missing value; INCLUDED does not mean measured.",
        ],
    }))
    records.append(envelope("sine-approximation", "approximation_specification", {
        "reference_expression": representation("sin(theta)"),
        "approximate_expression": representation("theta"),
        "reference_refs": [], "scope": scope("Real theta in radians; target is the sine replacement only."),
        "inputs": [binding("theta", None, "angle")],
        "expansion_parameter": present("theta, dimension-one angle expressed in radians"),
        "order_notation": na("No asymptotic-order claim is asserted in this fixture."),
        "target_output": "Relative error of the sine replacement, NOT pendulum period.",
        "error": {
            "metric": "RELATIVE",
            "expression": present("abs(theta - sin(theta))/abs(sin(theta))"),
            "denominator": present("abs(sin(theta))"),
            "zero_denominator_policy": "UNAVAILABLE",
            "extension_definition": na("No continuous extension was specified."),
            "quantity_definition": ref("dimension-one", "quantity_definition"),
        },
        "criterion": {
            "criterion_id": "sine-error-le-0.01", "version": present("illustrative-1"),
            "operator": "LE", "threshold": number(0.01),
            "threshold_quantity": ref("dimension-one", "quantity_definition"),
            "basis": "USER_SELECTED", "evidence_refs": [],
        },
        "bound_claims": [], "bound_evidence_refs": [], "assessment_refs": [],
        "limitations": [
            "No theta input or criterion evaluation is asserted.",
            "Illustrative tolerance, not a physical transition or source-derived universal boundary.",
        ],
    }))
    conditions = energy["payload"]["conditions"]
    records.append(envelope("energy-application", "anchor_application", {
        "anchor": ref("energy-anchor", "physics_anchor"),
        "anchor_version": present(VERSION),
        "subjects": [{
            "subject": ref("balance", "balance_specification"),
            "examined_version": present(VERSION), "examined_state_artifact_refs": [],
            "selector": present("payload"),
        }],
        "scope": scope(),
        "condition_checks": [
            requirement(c["condition_id"], c["exact_requirement"]) for c in conditions
        ],
        "unaddressed_conditions": [],
        "symbol_mappings": [{
            "anchor_symbol": "dE_CV/dt",
            "subject": ref("storage-rate", "observation"),
            "selector": present("payload.value"),
            "quantity_definition": ref("power", "quantity_definition"),
        }],
        "applicability_status": "UNKNOWN", "applicability_assessment_refs": [],
        "comparison_status": "NOT_EVALUATED", "comparison_assessment_refs": [],
        "competing_interpretation_refs": [],
        "limitations": [
            "Every listed condition is unevaluated; an empty unaddressed list does not mean they passed.",
            "Transfer mappings and scope evidence are incomplete.",
        ],
    }))
    assessment = copy.deepcopy(template_assessment)
    assessment.update({k: v for k, v in envelope("residual-assessment", "assessment", {}, old=True).items() if k != "payload"})
    ap = assessment["payload"]
    ap["subjects"] = [{
        "subject": ref("residual", "calculation"),
        "examined_version": present(VERSION), "examined_state_artifact_refs": [],
        "selector": present("payload.result"),
    }]
    ap["property"] = "Eligibility for calculating the specified synthetic energy residual."
    ap["dependency_refs"] = [ref("storage-rate", "observation")]
    ap["procedure"]["description"] = present("Proposed input eligibility review, not performed.")
    ap["criteria"][0].update({
        "criterion_id": "storage-available", "scope": scope(),
        "exact_rule": "Do not calculate this residual until its missing storage input is available and compatible.",
    })
    records.append(assessment)
    return {
        "bundle_kind": "SYNTHETIC_DRAFT_EXAMPLES_NOT_EXECUTION_EVIDENCE",
        "schema_ids": [OLD, NEW],
        "limitations": [
            "Mixed-version records, not a migration of draft 0.1.",
            "Inline source citations exist; standalone source records remain unresolved.",
            "All condition outcomes and the model applicability comparison remain unevaluated.",
        ],
        "records": records,
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, allow_nan=False))
