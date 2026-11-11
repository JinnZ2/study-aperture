"""CC0. Offline experiment CLI; all generated output directories must be fresh."""
import argparse
import json
import sys
from pathlib import Path

from .common import dump_json, fresh_dir, sha256_bytes, strict_load, utc_now
from . import harness


def _write_report(output_dir, report, markdown=None):
    out = fresh_dir(output_dir)
    report = dict(report)
    report["reported_at"] = utc_now()
    report["procedure"] = {"version": harness.VERSION,
                           "source_sha256": sha256_bytes(Path(__file__).read_bytes())}
    dump_json(out / "report.json", report)
    if markdown:
        (out / "report.md").write_text(markdown, encoding="utf-8")
    return out


def _captures(paths, freeze_dir):
    harness.verify_freeze(freeze_dir)
    digest = sha256_bytes((Path(freeze_dir) / "manifest.json").read_bytes())
    result = [harness.read_capture(p) for p in paths]
    if any(r["provenance"]["freeze_sha256"] != digest for r in result):
        raise ValueError("PAUSE: captures were collected under a different freeze; no silent rescoring")
    if len({r["run_id"] for r in result}) != len(result):
        raise ValueError("duplicate run IDs; do not double-count a capture")
    return result


def parser():
    p = argparse.ArgumentParser(description="Isolated offline assessor-reliability experiment (not a reliability score)")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("battery", "freeze", "demo"):
        q = sub.add_parser(name)
        q.add_argument("--output-dir", required=True)
    sub.choices["freeze"].add_argument("--repo", default=str(harness.REPO_ROOT))
    sub.choices["freeze"].add_argument("--battery", required=True)
    for name in ("prompt", "capture"):
        q = sub.add_parser(name)
        q.add_argument("--battery", required=True)
        q.add_argument("--case", required=True)
        q.add_argument("--variant", default="base")
        q.add_argument("--freeze", required=True)
        q.add_argument("--output-dir", required=True)
    q = sub.choices["capture"]
    q.add_argument("--raw", required=True)
    q.add_argument("--metadata", required=True)
    q.add_argument("--run-id", required=True)
    q = sub.add_parser("repeats")
    q.add_argument("--captures", nargs="+", required=True)
    q.add_argument("--freeze", required=True)
    q.add_argument("--fields", nargs="+")
    q.add_argument("--material-fields", nargs="+")
    q.add_argument("--output-dir", required=True)
    q = sub.add_parser("perturbation")
    q.add_argument("--base", required=True)
    q.add_argument("--variant-capture", required=True)
    q.add_argument("--battery", required=True)
    q.add_argument("--freeze", required=True)
    q.add_argument("--output-dir", required=True)
    q = sub.add_parser("review-packets")
    q.add_argument("--battery", required=True)
    q.add_argument("--captures", nargs="*", default=[])
    q.add_argument("--phase", choices=("reference", "output"), default="reference")
    q.add_argument("--output-dir", required=True)
    q = sub.add_parser("review-validate")
    q.add_argument("--review", required=True)
    q = sub.add_parser("adjudicate")
    q.add_argument("--observations", required=True)
    q.add_argument("--reviews", nargs="+", required=True)
    q.add_argument("--adjudicator", required=True)
    q.add_argument("--output-dir", required=True)
    q = sub.add_parser("review-summary")
    q.add_argument("--reviews", nargs="+", required=True)
    q.add_argument("--output-dir", required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "battery":
            from .battery import build_battery
            result = build_battery(Path(args.output_dir))
            print("Constructed battery written:", len(result["cases"]), "case variants; no model run.")
        elif args.command == "freeze":
            manifest = harness.freeze_battery(args.output_dir, args.battery, args.repo)
            print("Frozen repository commit:", manifest["repository_commit"])
        elif args.command in ("prompt", "capture"):
            case, root = harness.load_case(args.battery, args.case, args.variant)
            if args.command == "prompt":
                prompt = harness.prompt_for(case, root, args.freeze)
                out = fresh_dir(args.output_dir)
                (out / "prompt.txt").write_text(prompt["text"], encoding="utf-8")
                dump_json(out / "prompt-manifest.json", {k: v for k, v in prompt.items() if k not in ("text", "materials")})
                dump_json(out / "metadata-template.json", {
                    "model": {"name": "UNDECLARED", "version": "UNDECLARED"},
                    "assessment_date": "UNDECLARED", "environment": {"identifier": "UNDECLARED"},
                    "tools": [], "retrieved_material": [], "assessor_prior": "UNKNOWN_ORIGIN",
                    "actual_prompt_sha256": prompt["sha256"],
                    "execution": {"errors": [], "retries": 0, "truncated": False, "incomplete": False}})
                print("Prompt exported without observations, reference judgments or scoring dependencies.")
            else:
                result = harness.capture(args.raw, case, root, args.freeze, strict_load(args.metadata), args.output_dir, args.run_id)
                print("Raw bytes preserved; transport/frozen invariants valid:", result["validation"]["schema_valid"])
        elif args.command == "repeats":
            from .comparison import compare_repeats, render_markdown
            captures = _captures(args.captures, args.freeze)
            case_key = (captures[0]["case_id"], captures[0]["variant_id"])
            if any((r["case_id"], r["variant_id"]) != case_key for r in captures):
                raise ValueError("repeats must select one identical case/variant")
            inventory = strict_load(Path(args.freeze) / "battery/cases.json")["cases"]
            matched = [c for c in inventory if (c["case_id"], c["variant_id"]) == case_key]
            if len(matched) != 1:
                raise ValueError("case/variant not in frozen inventory")
            declared = matched[0]["comparison_spec"]
            fields = declared["fields"]
            material = declared["material_fields"]
            if args.fields is not None and args.fields != fields:
                raise ValueError("PAUSE: repeat field selection differs from predeclared frozen case")
            if args.material_fields is not None and args.material_fields != material:
                raise ValueError("PAUSE: material fields differ from predeclared frozen case")
            report = compare_repeats(captures, fields, material)
            report["capture_bindings"] = [{"run_id": r["run_id"], "raw_sha256": r["raw_sha256"],
                                          "freeze_sha256": r["provenance"]["freeze_sha256"]} for r in captures]
            _write_report(args.output_dir, report, render_markdown(report))
        elif args.command == "perturbation":
            from .comparison import compare_perturbation, render_markdown
            base, variant = _captures([args.base, args.variant_capture], args.freeze)
            case, root = harness.load_case(args.battery, variant["case_id"], variant["variant_id"])
            spec = case.get("perturbation")
            if not spec:
                raise ValueError("selected case has no predeclared perturbation")
            if (base["case_id"], base["variant_id"]) != (spec["base_case_id"], spec["base_variant_id"]):
                raise ValueError("capture does not match declared perturbation base")
            harness.source_material(case, root)
            report = compare_perturbation(base, variant, spec)
            report["capture_bindings"] = [{"run_id": r["run_id"], "raw_sha256": r["raw_sha256"],
                                          "freeze_sha256": r["provenance"]["freeze_sha256"]} for r in (base, variant)]
            _write_report(args.output_dir, report, render_markdown(report))
        elif args.command == "review-packets":
            from .review import make_review_packets
            battery = strict_load(args.battery)
            captures = [harness.read_capture(p) for p in args.captures]
            for path, record in zip(args.captures, captures):
                try:
                    record["raw_text"] = (Path(path).parent / "raw.bin").read_bytes().decode("utf-8")
                except UnicodeError:
                    record["raw_review_limit"] = "Raw bytes are non-UTF8; coordinator must arrange a separately recorded binary review."
            make_review_packets(battery["cases"], captures, Path(args.output_dir), phase=args.phase,
                                source_root=Path(args.battery).parent)
            print("Pending review packets created; coordinator mapping must remain private.")
        elif args.command == "review-validate":
            from .review import validate_review
            errors = validate_review(strict_load(args.review))
            print(json.dumps({"errors": errors, "valid": not errors}, indent=2))
            return 1 if errors else 0
        elif args.command == "adjudicate":
            from .review import adjudicate
            result = adjudicate(strict_load(args.observations), [strict_load(p) for p in args.reviews], strict_load(args.adjudicator))
            _write_report(args.output_dir, result)
        elif args.command == "review-summary":
            from .review import summarize_reviews
            _write_report(args.output_dir, summarize_reviews([strict_load(p) for p in args.reviews]))
        elif args.command == "demo":
            from .demo import run_demo
            result = run_demo(Path(args.output_dir))
            print("CONSTRUCTED demonstration only:", result["capture_count"], "synthetic captures; zero live model assessments.")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("INPUT/EXECUTION ERROR:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
