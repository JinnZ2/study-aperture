"""CC0. CONSTRUCTED software demonstration, never model-performance evidence."""
import json
from pathlib import Path

from .battery import build_battery, constructed_response
from .common import dump_json, fresh_dir, utc_now
from .comparison import compare_perturbation, compare_repeats, render_markdown
from .harness import capture, freeze_battery, prompt_for, read_capture
from .review import make_review_packets


def run_demo(output_dir):
    out = fresh_dir(output_dir)
    battery = build_battery(out / "battery")
    freeze_dir = out / "freeze"
    freeze_battery(freeze_dir, out / "battery/cases.json")
    (out / "inputs").mkdir()
    (out / "captures").mkdir()
    cases = {(c["case_id"], c["variant_id"]): c for c in battery["cases"]}
    captures, faithful, paths = [], {}, {}

    def record(case, mode, suffix):
        run_id = "synthetic-" + case["case_id"] + "-" + case["variant_id"] + "-" + suffix
        response = constructed_response(case, mode)
        raw = json.dumps(response, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
        raw_path = out / "inputs" / (run_id + ".txt")
        raw_path.write_bytes(raw)
        prompt = prompt_for(case, out / "battery", freeze_dir)
        metadata = {
            "constructed": True, "model": {"name": "CONSTRUCTED_FIXTURE", "version": "constructed-response/1"},
            "assessment_date": "CONSTRUCTED_NOT_A_MODEL_ASSESSMENT",
            "environment": {"identifier": "CONSTRUCTED_OFFLINE_COPYING_CONTROL", "retrieval": "NONE"},
            "tools": [], "retrieved_material": [],
            "actual_prompt_sha256": prompt["sha256"],
            "assessor_prior": "CONSTRUCTED_FIXTURE_SEES_CONSTRUCTION_OBSERVATIONS",
            "execution": {"errors": [], "retries": 0, "truncated": False, "incomplete": False}}
        run_path = out / "captures" / run_id
        result = capture(raw_path, case, out / "battery", freeze_dir, metadata, run_path, run_id)
        captures.append(result)
        paths[run_id] = run_path / "capture.json"
        return result

    for case in battery["cases"]:
        faithful[(case["case_id"], case["variant_id"])] = record(case, "faithful", "copy-1")
    faults = []
    for family in ("clear_evidence", "conditional_claim", "unresolved_case"):
        case = next(c for c in battery["cases"] if c["family"] == family and c["variant_id"] == "base")
        faults.append(record(case, "faulty", "fault"))
    repeated = next(c for c in battery["cases"] if c["family"] == "repeated_assessment" and c["variant_id"] == "base")
    repeated_captures = [faithful[(repeated["case_id"], "base")],
                         record(repeated, "faithful", "copy-2"), record(repeated, "faithful", "copy-3")]
    repeats = compare_repeats(repeated_captures, repeated["comparison_spec"]["fields"], repeated["comparison_spec"]["material_fields"])
    repeats["constructed"] = True
    repeats["interpretation"] = "Three identical copying fixtures, not three independent model assessments."
    (out / "analysis").mkdir()
    dump_json(out / "analysis/repeats.json", repeats)
    (out / "analysis/repeats.md").write_text(render_markdown(repeats), encoding="utf-8")
    perturbations = []
    for case in battery["cases"]:
        spec = case.get("perturbation")
        if not spec:
            continue
        base = faithful[(spec["base_case_id"], spec["base_variant_id"])]
        variant = faithful[(case["case_id"], case["variant_id"])]
        report = compare_perturbation(base, variant, spec)
        report["constructed"] = True
        report["source_case_id"] = case["case_id"]
        dump_json(out / "analysis" / (spec["kind"] + ".json"), report)
        (out / "analysis" / (spec["kind"] + ".md")).write_text(render_markdown(report), encoding="utf-8")
        perturbations.append({"kind": spec["kind"], "report": "analysis/" + spec["kind"] + ".json"})
    references = make_review_packets(battery["cases"], [], out / "reference-review", phase="reference", source_root=out / "battery")
    conditional_case = next(c for c in battery["cases"] if c["family"] == "conditional_claim" and c["variant_id"] == "base")
    output_captures = [faithful[(conditional_case["case_id"], "base")], faults[1]]
    transport_copies = []
    for item in output_captures:
        # Separate in-memory transport copy; persisted capture is never edited.
        copied = dict(read_capture(paths[item["run_id"]]))
        copied["raw_text"] = paths[item["run_id"]].with_name("raw.bin").read_bytes().decode("utf-8")
        transport_copies.append(copied)
    output_packets = make_review_packets(battery["cases"], transport_copies, out / "output-review", phase="output", source_root=out / "battery")
    summary = {
        "schema": "assessor-reliability/demo/1", "constructed": True, "status": "SOFTWARE_DEMONSTRATION_ONLY",
        "created_at": utc_now(), "base_case_count": battery["design_variables"]["base_case_count"],
        "case_variant_count": len(battery["cases"]), "perturbation_count": len(perturbations),
        "capture_count": len(captures), "live_model_assessments": 0, "completed_independent_reviews": 0,
        "repeat_capture_count": len(repeated_captures), "fault_capture_count": len(faults),
        "reference_packet_count": references["packet_count"], "output_packet_count": output_packets["packet_count"],
        "captures": [{"run_id": c["run_id"], "path": str(paths[c["run_id"]].relative_to(out)),
                      "schema_valid": c["validation"]["schema_valid"], "raw_sha256": c["raw_sha256"]} for c in captures],
        "perturbations": perturbations,
        "limits": ["All assessor outputs were deterministically copied or deliberately corrupted by construction code.",
                   "Fixture generation sees authored observations; no assessor blinding is claimed.",
                   "Pending packets are not reviewer assessments; adjudication is not performed without reviewers.",
                   "No numerical model-reliability result, correctness threshold or core promotion follows."]}
    dump_json(out / "index.json", summary)
    lines = ["Status: CONSTRUCTED software demonstration only; no live models or completed independent reviews.", "",
             "# Assessor-reliability demonstration", "",
             f"The battery contains {summary['base_case_count']} constructed base cases and {summary['perturbation_count']} controlled variants ({summary['case_variant_count']} total case variants).",
             f"It preserves {summary['capture_count']} synthetic raw captures: {summary['case_variant_count']} initial copying fixtures, {summary['fault_capture_count']} fault fixtures and two extra copies of one repeated case.",
             "These counts describe software artifacts, not assessor accuracy or population sample sizes.", "",
             "## Build A", "",
             "`battery/cases.json` preserves observations/dependencies separately from assessor inputs. `freeze/` pins the committed method, implementation and battery. Each `captures/<run>/` directory holds original raw bytes, parsed data, source snapshots, mechanical results and artifact hashes.",
             "Fault fixtures intentionally displace a location, drop a qualification when present and invent an undeclared source. Inspect their separate mechanical results; semantic/uncertainty review remains NOT_ASSESSED.", "",
             "## Build B", "",
             "`analysis/repeats.json` and its generated markdown compare three identical copying fixtures. The ten separate perturbation JSON/markdown reports exercise predeclared field dependencies. Any disagreements/failures concern the declared software probes, not a model or scientific validity.", "",
             "## Build C", "",
             f"`reference-review/` contains {summary['reference_packet_count']} pending source-only packets; `output-review/` contains {summary['output_packet_count']} pending anonymized fixture-review packets.",
             "No reviewer assessment or adjudication is manufactured. Distribute only an individual `reviewer/<packet>/` directory; keep `coordinator/mapping.json` private.", "",
             "## Replay boundary", "",
             "Use the original unchanged implementation and the frozen battery to replay analysis. Revised implementation/scoring requires a new freeze and explicitly versioned analysis; never rewrite this directory. All generated paths must be fresh.", ""]
    (out / "index.md").write_text("\n".join(lines), encoding="utf-8")
    return summary
