"""Constructed controls and explicitly adapted preserved-specimen challenges."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from .audit import INPUT_SCHEMA, InputError, audit, write_report


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "audits/gemini-assessment-records-2026-11-11/data"
EXCERPTS = Path(__file__).parent / "examples/review-excerpts"
SPECIMEN_PINS = {
    "attempt-01.txt":
        "6dcc25cb8b77bf5fbd65a1a3d1a3883cb7382aca9798c7f6e6b8f5fe1a4cbd85",
    "attempt-02.txt":
        "a57f43198198d2e2bf3dec17d925e01bdc918d3e8725558834937104cf43b9ca",
}
EXCERPT_PINS = {
    "agency.txt": "60df611fb1f3abcec2b2e3a10704fd423cb1622e69c16944bcf63e063e16c436",
    "bias.txt": "cc2f86a4343dc4f3a411115e100f9dc01deb85d79aa57d22787b3d6606775a57",
    "rl.txt": "c85e0b2ea232275c21df201b517530e2f58d12dca28bd829fdc5d77aa58e51a3",
    "stopping.txt": "669126405cdc071af2765f83dabac8fb0ecb5c7d3ec711bacd453b70dfd21728",
}
A = "Within chamber A, selected readings averaged 2.44 units.\n"
B = "The constructed controller uses a socket.\n"
PUB_A = {"identifier": "constructed:paper-a", "title": "Chamber protocol",
         "authors": ["Constructed author A"], "version": "fixture-v1"}
PUB_B = {"identifier": "constructed:paper-b", "title": "Controller protocol",
         "authors": ["Constructed author B"], "version": "fixture-v1"}


def capture(cid, publication, path, raw, kind="CONSTRUCTED_EXCERPT"):
    return {
        "id": cid, "publication": copy.deepcopy(publication), "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(), "material_kind": kind,
        "source_url": "UNDECLARED", "acquired_by": "DEMO_CONSTRUCTOR",
        "capture_decision": "Explicit bounded fixture, not a publisher capture",
    }


def base_bundle():
    return {
        "schema": INPUT_SCHEMA,
        "provenance": {
            "kind": "CONSTRUCTED",
            "selection_decision": "Exercise binding outcomes independently",
            "conditions": "Two toy publications; selected local UTF-8 files",
            "remaining_uncertainty": "No physical or publisher authenticity tested",
        },
        "publication": copy.deepcopy(PUB_A),
        "captures": [
            capture("a", PUB_A, "a.txt", A.encode()),
            capture("b", PUB_B, "b.txt", B.encode()),
            capture("a-full", PUB_A, "b.txt", B.encode(),
                    kind="CONSTRUCTED_FULL_TEXT_FRAGMENT"),
        ],
        "materials_held": ["a"],
        "claims": [{
            "id": "C1", "text": A.rstrip("\n"), "rendering": "QUOTATION",
            "capture_id": "a",
            "location": {"start": 0, "end": len(A) - 1, "label": "fixture sentence"},
            "assessment_as_supplied": {"support": "UNDETERMINED",
                                      "decision": "UNRESOLVED"},
        }],
    }


def constructed_cases():
    """Expected outcomes are defined independently in tests, not by this runner."""
    result = {}

    def case(name):
        result[name] = base_bundle()
        return result[name]

    case("exact-positive")
    case("identifier-difference")["publication"]["identifier"] = "constructed:other"
    case("same-id-title-difference")["publication"]["title"] = "Another title"
    case("author-difference")["publication"]["authors"] = ["Another author"]
    case("version-difference")["publication"]["version"] = "fixture-v2"
    case("missing-version")["publication"]["version"] = "UNDECLARED"
    mixed = case("difference-with-unknown")
    mixed["publication"].update(identifier="constructed:other",
                                version="UNDECLARED")
    case("empty-held-list")["materials_held"] = []
    case("unknown-held-list")["materials_held"] = "UNDECLARED"
    full = case("full-text-outside-held")["claims"][0]
    full.update(capture_id="a-full", text=B.rstrip("\n"))
    full["location"]["end"] = len(B) - 1
    case("missing-location")["claims"][0]["location"] = "NO_EVIDENCE_LOCATION"
    case("invalid-span")["claims"][0]["location"]["end"] = 99999
    case("declared-paraphrase")["claims"][0].update(
        rendering="PARAPHRASE", text="Selected readings in chamber A average 2.44.")
    case("undeclared-rendering")["claims"][0]["rendering"] = "UNDECLARED"
    case("empty-quote")["claims"][0]["text"] = ""
    case("quotation-difference")["claims"][0]["text"] = A.upper().rstrip("\n")
    case("different-donor-not-repaired")["claims"][0]["text"] = B.rstrip("\n")
    case("changed-hash")["captures"][0]["sha256"] = "0" * 64
    case("missing-file")["captures"][0]["path"] = "not-present.txt"
    case("missing-hash")["captures"][0]["sha256"] = "UNDECLARED"
    case("undeclared-capture")["claims"][0]["capture_id"] = "not-declared"
    promotion = case("no-promotion")
    promotion["claims"][0]["assessment_as_supplied"] = {
        "support": "SUPPORTED", "grade": "MEASURED_PRESENT",
        "design_checks": "CHECKED", "independence": "INDEPENDENT_CONVERGENCE",
        "physical_adequacy": "PASS", "deployment": "RESOLVED",
    }
    return result


def specimen_cases():
    """Adapt C1 only; do not reconstruct the assessor's unrecorded access."""
    records = []
    for name, digest in SPECIMEN_PINS.items():
        raw = (ARCHIVE / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise InputError("original specimen changed; adaptation refused")
        for index, fragment in enumerate(
                re.split(r"(?m)^PUBLICATION: ", raw.decode("utf-8"))[1:], 1):
            records.append((name, index, "PUBLICATION: " + fragment))
    declarations = [
        ("2611.00496",
         "Swap, Replicate, Read the Mass: A Protocol for Auditing Demographic Bias "
         "in System One Decision Models", "bias.txt", "ABSTRACT_EXCERPT",
         "https://arxiv.org/abs/2611.00496"),
        ("2611.12122", "System Optimizations for Cost-Efficient Agent Harnesses",
         "agency.txt", "SECTION_4.1_EXCERPT",
         "https://arxiv.org/html/2611.12122v1"),
        ("2611.12865",
         "Shortcuts and Boundaries: Verifiable RL Misalignment and Contextual "
         "Safety Learning", "rl.txt", "ABSTRACT_EXCERPT",
         "https://arxiv.org/abs/2611.12865"),
        ("2611.00166",
         "Early Stopping in Large Reasoning Models: A Survey and Empirical Audit "
         "of Efficiency and Reliability", "stopping.txt", "SECTION_6_EXCERPT",
         "https://arxiv.org/html/2611.00166v1"),
    ]
    if len(records) != len(declarations):
        raise InputError("specimen map must cover every selected original record")
    result = {}
    for record, declaration in zip(records, declarations):
        name, index, original = record
        identifier, title, filename, location, url = declaration
        wording = re.search(r'(?m)^Bullet C1 \[OBSERVED\] "([^"]+)"', original)
        header = re.fullmatch(
            r"PUBLICATION: (.+) \((?:(.+), )?arXiv:([0-9.]+)\)",
            original.splitlines()[0].split(" | TYPE:", 1)[0])
        if (wording is None or header is None or header.group(1) != title
                or header.group(3) != identifier):
            raise InputError("specimen adaptation map no longer fits original")
        raw = (EXCERPTS / filename).read_bytes()
        if hashlib.sha256(raw).hexdigest() != EXCERPT_PINS[filename]:
            raise InputError("review excerpt changed; retain prior capture")
        publication = {"identifier": f"arxiv:{identifier}",
                       "title": header.group(1),
                       "authors": header.group(2) or "UNDECLARED",
                       "version": "UNDECLARED"}
        material = capture("named-source-excerpt", publication, filename, raw)
        material["publication"]["authors"] = "UNDECLARED"
        material["publication"]["version"] = (
            "v1" if url.endswith("v1") else "UNDECLARED")
        material.update(
            source_url=url, material_kind="REVIEWER_TRANSCRIBED_" + location,
            acquired_by="REVIEWER_TRANSCRIPTION_FROM_CITED_PASSAGE",
            capture_decision="Selected passage only, not a complete paper search")
        result[f"specimen-{name[:-4]}-record-{index}"] = {
            "schema": INPUT_SCHEMA,
            "publication": publication, "captures": [material],
            # A source excerpt held by this reviewer does not establish what
            # the original assessor held, despite its broad materials label.
            "materials_held": "UNDECLARED",
            "provenance": {
                "kind": "SPECIMEN_DERIVED_CHALLENGE",
                "selection_decision": "Compare supplied C1 with one named-source "
                                      "passage; no whole-paper absence inference",
                "conditions": "Reviewer-transcribed excerpts; not raw HTTP "
                              "captures or an original assessor execution",
                "remaining_uncertainty": "Original material access and version, "
                                         "and captured author list unresolved; "
                                         "abbreviated original author "
                                         "attributions retained without expansion",
                "specimen": name, "record_index": index,
                "specimen_sha256": SPECIMEN_PINS[name],
                "original_record_as_supplied": original,
            },
            "claims": [{
                "id": "C1", "text": wording.group(1), "rendering": "QUOTATION",
                "capture_id": "named-source-excerpt",
                "location": {"start": 0, "end": len(raw.decode().rstrip("\n")),
                             "label": location},
                "assessment_as_supplied": {"raw_claim_line": next(
                    line for line in original.splitlines()
                    if line.startswith("Bullet C1 "))},
            }],
        }
    return result


def run(output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    sources = output / "constructed-sources"
    sources.mkdir()
    (sources / "a.txt").write_bytes(A.encode())
    (sources / "b.txt").write_bytes(B.encode())
    reports = {}

    def store(name, bundle, source_root):
        report = audit(bundle, source_root)
        destination = output / name
        write_report(report, destination)
        # Each generated case is independently replayable with the audit CLI.
        # These are our fixed fixture paths, already checked by audit().
        for path in {c["path"] for c in bundle["captures"]}:
            source = source_root / path
            if source.is_file():
                (destination / path).write_bytes(source.read_bytes())
        (destination / "bundle.json").write_text(
            json.dumps(bundle, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        reports[name] = report

    for name, bundle in constructed_cases().items():
        store(name, bundle, sources)
    for name, bundle in specimen_cases().items():
        store(name, bundle, EXCERPTS)
    (output / "index.json").write_text(json.dumps({
        "status": "REPORTS_ONLY_NOT_TEST_RESULTS",
        "cases": {name: report["binding_counts"]
                  for name, report in reports.items()},
        "limitations": "Constructed controls and adapted C1 comparisons, not "
                       "authenticated publication or original model execution.",
    }, indent=2) + "\n", encoding="utf-8")
    (output / "evidence.json").write_text(
        json.dumps(reports, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    lines = [
        "Status: generated binding evidence, not a test PASS or scientific verdict.",
        "", "# Publication-to-claim provenance audit", "",
        "Twenty-two constructed controls and four adapted specimen challenges.",
        "The independent test matrix, not these report labels, checks the audit.",
        "", "| Case | Binding | Known differences | Unresolved |",
        "|---|---|---|---|",
    ]
    for name, report in reports.items():
        claim = report["claims"][0]
        lines.append(
            f"| {name} | {claim['binding']} | "
            f"{', '.join(claim['differences']) or 'none recorded'} | "
            f"{', '.join(claim['unresolved']) or 'none recorded'} |")
    lines += ["", "## What this does not establish", "",
              "Identity is compared with declared captures, not authenticated.",
              "Paraphrase meaning, author endorsement, study design, independence,",
              "physical adequacy and deployment remain outside this audit.",
              "The adapted cases compare selected passages, not whole papers.",
              "No parent assessment, original specimen or support grade is changed.",
              "Each case retains a portable bundle, source files and full report.",
              "Use a fresh output directory when replaying any case.", ""]
    (output / "index.md").write_text("\n".join(lines), encoding="utf-8")
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        reports = run(args.output_dir)
    except (InputError, OSError, ValueError) as error:
        parser.exit(2, f"INPUT/OUTPUT ERROR: {error}\n")
    print(f"{len(reports)} reports written; not a test PASS or scientific verdict")


if __name__ == "__main__":
    main()
