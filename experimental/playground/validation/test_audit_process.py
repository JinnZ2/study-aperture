"""One preserved audit plus planted inference probes; no empirical promotion."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ..applicability.mapping import Domain
from ..audits.tolman_process import (
    CASE, PINNED, ROOT, execute_formal, formal_models, mathematical_experiment,
    replay_legacy, run_pilot, sha, verify_snapshot,
)
from ..equations.substitution import RunState
from ..failures import Status


class AuditProcessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name) / "fresh-pilot"
        cls.report = run_pilot(cls.output)
        cls.inspection = cls.report["inspection"]

    def test_existing_audit_reruns_byte_identically_not_just_successfully(self):
        comparisons = self.report["legacy_artifact_comparisons"]
        self.assertEqual(len(comparisons), 4)
        for comparison in comparisons.values():
            self.assertTrue(comparison["byte_identical"])
            self.assertEqual(comparison["fresh_sha256"], comparison["preserved_sha256"])

    def test_original_snapshot_and_publication_claim_records_unchanged(self):
        self.assertTrue(self.report["original_snapshot_unchanged"])
        self.assertEqual(verify_snapshot(), PINNED)
        self.assertTrue(any(name.endswith("study-record.json") for name in PINNED))
        self.assertTrue(any(name.endswith("mappings.json") for name in PINNED))

    def test_integrity_unknowns_are_preserved_not_converted_to_absence(self):
        counts = self.inspection["original_integrity_summary"]["finding_counts"]
        self.assertEqual(counts["ERROR"], 0)
        self.assertEqual(counts["UNKNOWN"], 24)
        self.assertEqual(self.inspection["original_integrity_summary"]["anchor_application_count"], 0)

    def test_formal_competitors_both_have_functioning_implementations(self):
        for run in self.inspection["formal_runs"]:
            self.assertEqual(run["state"], RunState.COMPUTED.value)
            self.assertFalse(run["known_answer"]["cases_failed"])
            self.assertTrue(run["known_answer"]["cases_run"])
            self.assertFalse(run["null"]["cases_flagged"])
            self.assertTrue(run["null"]["cases_run"])
            self.assertEqual(run["stages"][-3:], ["known-answer:pass", "null:pass", "calculation:computed"])

    def test_correctly_implemented_proposition_can_fail_a_mathematical_criterion(self):
        comparison = self.inspection["formal_comparison"]
        self.assertEqual(comparison["retained_prefactor_average"], 0.625)
        self.assertEqual(comparison["universal_half_value"], 0.5)
        self.assertEqual(comparison["absolute_difference"], 0.125)
        self.assertEqual(comparison["criterion_outcome"], "NOT_MET")
        self.assertEqual(comparison["lane"], "MATHEMATICAL_VALIDITY")
        for run in self.inspection["formal_runs"]:
            self.assertFalse(any(f["axis"] == "instrument" and f["severity"] == "failed"
                                 for f in run["record"]["findings"]))

    def test_mathematical_mismatch_is_not_automatically_physical_failure(self):
        for run in self.inspection["formal_runs"]:
            self.assertFalse(any(f["axis"] == "physical" for f in run["record"]["findings"]))
            self.assertEqual(run["applicability"]["state"], "unknown")
            self.assertTrue(all(o["uncertainty"] is None for o in run["outputs"]))

    def test_maximal_mixing_is_retained_as_a_special_agreement_case(self):
        experiment, rules = mathematical_experiment(1.0)
        runs = [execute_formal(m, experiment) for m in formal_models(rules)]
        self.assertEqual([r.outputs[0].value for r in runs], [0.5, 0.5])
        self.assertTrue(all(r.record.physical is Status.UNTESTED for r in runs))

    def test_zero_mixing_counterexample_is_not_misdiagnosed_as_software_defect(self):
        experiment, rules = mathematical_experiment(0.0)
        runs = [execute_formal(m, experiment) for m in formal_models(rules)]
        self.assertEqual([r.outputs[0].value for r in runs], [1.0, 0.5])
        self.assertTrue(all(r.record.instrument is Status.OK for r in runs))

    def test_formal_l0_is_not_a_fabricated_physical_closure_ledger(self):
        experiment, _ = mathematical_experiment()
        self.assertEqual([a.quantity for a in experiment.boundary.accounting.accounts],
                         ["total_probability"])
        self.assertEqual(experiment.boundary.quantity_units, (("total_probability", "1"),))
        self.assertIn("Mathematical normalization only", experiment.anchor.conditions[0])
        self.assertFalse(self.inspection["physical_experiment"]["constructed"])

    def test_all_selected_context_domains_and_decisions_are_retained(self):
        experiment, _ = mathematical_experiment()
        self.assertEqual({c.domain for c in experiment.context.conditions}, set(Domain))
        for run in self.inspection["formal_runs"]:
            self.assertTrue(run["selection"]["criteria"])
            self.assertTrue(run["plan"]["evidence"])
            self.assertTrue(run["experiment"]["context"]["uncertainty_notes"])
            self.assertTrue(run["plan_digest"])
            self.assertTrue(run["context_digest"])

    def test_kernel_change_is_scope_change_not_a_new_physical_finding(self):
        probe = self.inspection["kernel_change_probe"]
        self.assertEqual(probe["input_kind"], "PLANTED_SCOPE_CHANGE_NOT_OBSERVATION")
        self.assertEqual(probe["run"]["state"], RunState.BLOCKED.value)
        self.assertEqual(probe["run"]["outputs"], [])
        self.assertEqual(probe["run"]["applicability"]["scope"], "outside-declared-domain")
        self.assertFalse(any(f["axis"] == "physical" for f in probe["run"]["record"]["findings"]))

    def test_math_assessment_and_clean_diagnostics_do_not_promote_physics(self):
        probe = self.inspection["mathematical_to_physical_promotion_probe"]
        self.assertEqual(probe["state"], "unknown")
        self.assertEqual(probe["assessments"][0]["kind"], "mathematical-consistency")
        self.assertFalse(any(f["axis"] == "physical" for f in probe["record"]["findings"]))

    def test_hypothetical_non_detection_without_sensitivity_is_rejected(self):
        probe = self.inspection["absence_probe"]
        self.assertEqual(probe["input_kind"], "PLANTED_NON_DETECTION_NOT_OBSERVATION")
        self.assertEqual(probe["result_type"], "AbsenceRejection")
        self.assertTrue(any(f["code"] == "ND_UNQUALIFIED"
                            for f in probe["result"]["record"]["findings"]))

    def test_expiry_is_simulated_revision_not_new_data_or_refutation(self):
        probe = self.inspection["unknown_expiry_probe"]
        self.assertEqual(probe["input_kind"], "SIMULATED_TRIGGER_NOT_NEW_EVIDENCE")
        self.assertEqual(probe["original"]["state"], "unknown")
        self.assertEqual(probe["expiry"]["determination"]["state"], "expired")
        self.assertEqual(probe["expiry"]["transition"]["track"], "determination")
        self.assertEqual(probe["expiry"]["record"]["findings"], [])
        self.assertTrue(all(f["axis"] == "determination"
                            for f in probe["stale_reliance"]["findings"]))
        self.assertTrue(any(f["severity"] == "failed"
                            for f in probe["stale_reliance"]["findings"]))

    def test_physical_obligations_remain_unresolved(self):
        obligations = self.inspection["physical_obligations"]
        self.assertEqual(obligations["state"], "unknown")
        self.assertEqual(len(obligations["dependency_states"]), 5)
        self.assertTrue(all(state == "unknown" for _, state in obligations["dependency_states"]))
        self.assertFalse(self.inspection["physical_experiment"]["claim_support_promoted"])
        self.assertEqual(self.inspection["physical_experiment"]["physical_status"], "UNTESTED")
        self.assertEqual(self.inspection["physical_experiment"]["whole_paper_verdict"], "NOT_ISSUED")

    def test_publication_claim_and_actual_audit_decisions_are_not_promoted(self):
        original = self.inspection["original_claim_and_decisions"]
        self.assertEqual(original["claims"][0]["id"], "C1")
        self.assertEqual(original["claims"][0]["support"], "UNDETERMINED")
        self.assertEqual(original["claims"][0]["grade"], "UNMEASURED")
        self.assertEqual([d["state"] for d in original["decisions"]], ["UNRESOLVED", "UNRESOLVED"])
        self.assertFalse(original["decision_promotion"])
        self.assertEqual(original["bridge_to_physical_claim"], "NOT_ESTABLISHED")

    def test_replayed_phase_results_do_not_become_detection_forecasts(self):
        findings = self.inspection["replayed_phase_findings"]
        self.assertEqual(findings["empirical_detectability"], "NOT_EVALUATED")
        self.assertEqual(findings["corrected_physical_prediction"], "NOT_ESTABLISHED")
        branches = self.inspection["first_replayed_trial_branches"]
        self.assertEqual({b["spin_orientation"] for b in branches}, {-1, 1})
        self.assertTrue(all(b["conditional_minus_published"] != 0 for b in branches))

    def test_out_of_range_mixing_blocks_before_numerical_evaluation(self):
        experiment, rules = mathematical_experiment(1.1)
        with patch("playground.equations.substitution._calculate") as calculate:
            result = execute_formal(formal_models(rules)[0], experiment)
        calculate.assert_not_called()
        self.assertIs(result.state, RunState.BLOCKED)
        self.assertIs(result.record.physical, Status.UNTESTED)

    def test_map_retains_two_native_unknown_and_two_changed_kernel_outside_cells(self):
        cells = self.inspection["applicability"]["cells"]
        self.assertEqual(len(cells), 4)
        self.assertEqual([c["state"] for c in cells],
                         ["unknown", "unknown", "outside-declared-domain", "outside-declared-domain"])

    def test_strict_json_and_human_report_are_delivered_together(self):
        payload = json.loads((self.output / "tolman-vi-audit-process-report.json").read_text())
        self.assertEqual(payload["schema"], "audit-process-pilot/0.1")
        json.dumps(payload, allow_nan=False)
        text = (self.output / "tolman-vi-audit-process-report.md").read_text()
        self.assertIn("https://link.springer.com/", text)
        self.assertIn("not an independent scientific replication", text)
        self.assertTrue(payload["diagnostic_code_sha256"])
        self.assertTrue(payload["python_version"])

    def test_existing_output_directory_is_never_overwritten(self):
        before = sha(self.output / "tolman-vi-audit-process-report.json")
        with self.assertRaises(FileExistsError):
            run_pilot(self.output)
        self.assertEqual(sha(self.output / "tolman-vi-audit-process-report.json"), before)

    def test_outputs_cannot_be_placed_inside_legacy_or_repository_paths(self):
        with self.assertRaises(ValueError):
            run_pilot(ROOT / CASE / "PLANTED-do-not-create")
        self.assertFalse((ROOT / CASE / "PLANTED-do-not-create").exists())

    def test_changed_pinned_source_blocks_before_review_code_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            for name in PINNED:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            (root / CASE / "sources.json").write_text('{"PLANTED": "changed source"}\n')
            output = Path(temp) / "output"
            with patch("playground.audits.tolman_process.subprocess.run") as execute:
                with self.assertRaisesRegex(ValueError, "explicit reinspection"):
                    run_pilot(output, root=root)
            execute.assert_not_called()
            self.assertFalse(output.exists())

    def test_missing_snapshot_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileNotFoundError):
                verify_snapshot(Path(temp))

    def test_changed_replay_output_does_not_pass_as_reproduction(self):
        def corrupted(command, **kwargs):
            target = Path(command[-1])
            target.mkdir()
            for name in ("computed.json", "evidence-bundle.json", "integrity-report.json", "integrity-report.md"):
                shutil.copyfile(ROOT / CASE / "artifacts" / name, target / name)
            (target / "computed.json").write_text('{"PLANTED": "corrupted output"}\n')
        with tempfile.TemporaryDirectory() as temp:
            with patch("playground.audits.tolman_process.subprocess.run", side_effect=corrupted):
                with self.assertRaisesRegex(ValueError, "Replay differs"):
                    replay_legacy(Path(temp) / "replay")


if __name__ == "__main__":
    unittest.main()
