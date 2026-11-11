"""Second source-based audit; synthetic inputs never become measured evidence."""

import json
import math
import shutil
import tempfile
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from ..applicability.mapping import Domain
from ..audits.pendulum_process import (
    NUMERIC_TOLERANCE, PINNED, ROOT, SOURCE, criterion, formal_experiment,
    metric_bounds, models, plan, reference_check, run_pair, run_pilot,
    sine_bounds, verify_snapshot,
)
from ..equations.adapter import EquationRegistry, OutputPort
from ..equations.substitution import RunState, execute
from ..failures import Status


class PendulumAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name) / "fresh-pilot"
        cls.report = run_pilot(cls.output)
        cls.inspection = cls.report["inspection"]
        cls.cases = {c["selected_degrees"]: c for c in cls.inspection["cases"]}

    def test_preserved_authoring_review_is_replayed_without_changing_its_status(self):
        self.assertTrue(self.report["original_snapshot_unchanged"])
        self.assertEqual(verify_snapshot(), PINNED)
        legacy = json.loads((self.output / "legacy-replay.json").read_text())
        self.assertEqual(legacy["fixture_status"], "SYNTHETIC_NOT_EMPIRICAL")
        self.assertIn("runtime_versions", self.report["legacy_comparison"])
        self.assertIn("Only python_version", self.report["legacy_comparison"]["policy"])
        comparison = self.report["legacy_comparison"]
        self.assertEqual(comparison["byte_identical"],
                         comparison["fresh_sha256"] == comparison["preserved_sha256"])
        original = {c["angle_degrees"]: c for c in legacy["small_angle"]["cases"]}
        for degrees in (10, 14.5, 30):
            self.assertAlmostEqual(
                self.cases[degrees]["metrics"]["sine"]["run"]["outputs"][0]["value"],
                original[degrees]["relative_difference"], places=14)

    def test_ten_degree_positive_control_meets_both_selected_criteria(self):
        for metric in self.cases[10]["metrics"].values():
            self.assertEqual(metric["inclusive_selected_criterion"], "MET")
            self.assertEqual(metric["strict_comparison_under_this_denominator"], "MET")

    def test_fourteen_degree_criteria_disagree_without_instrument_failure(self):
        metrics = self.cases[14]["metrics"]
        self.assertEqual(metrics["sine"]["inclusive_selected_criterion"], "NOT_MET")
        self.assertEqual(metrics["angle"]["inclusive_selected_criterion"], "MET")
        for metric in metrics.values():
            run = metric["run"]
            self.assertEqual(run["state"], RunState.COMPUTED.value)
            self.assertFalse(run["known_answer"]["cases_failed"])
            self.assertFalse(run["null"]["cases_flagged"])
            self.assertFalse(any(f["severity"] == "failed" for f in run["record"]["findings"]))

    def test_fourteen_and_half_is_counterexample_only_under_explicit_metrics(self):
        for metric in self.cases[14.5]["metrics"].values():
            self.assertEqual(metric["strict_comparison_under_this_denominator"], "NOT_MET")
        self.assertEqual(self.inspection["source_claim_status"],
                         "UNDETERMINED_AS_WRITTEN_METRIC_NOT_SPECIFIED")
        self.assertEqual(self.inspection["whole_source_verdict"], "NOT_ISSUED")

    def test_zero_relative_error_is_undefined_not_silently_extended(self):
        for metric in self.cases[0]["metrics"].values():
            self.assertEqual(metric["inclusive_selected_criterion"], "UNDEFINED")
            self.assertIsNone(metric["exact_binary_radian_error_bounds"])
            run = metric["run"]
            self.assertEqual(run["state"], RunState.BLOCKED.value)
            self.assertEqual(run["outputs"], [])
            self.assertIsNone(run["known_answer"])
            self.assertEqual(run["applicability"]["scope"], "outside-declared-domain")
            self.assertFalse(any(f["axis"] == "physical" for f in run["record"]["findings"]))

    def test_nonzero_nominal_cases_traverse_the_full_gated_path(self):
        for degrees in (10, 14, 14.5, 30):
            for metric in self.cases[degrees]["metrics"].values():
                self.assertEqual(metric["run"]["stages"], [
                    "protocol-binding:pass", "l0:pass", "applicability:candidate-domain",
                    "validation-plan:pass", "known-answer:pass", "null:pass", "calculation:computed",
                ])

    def test_substitution_retains_experiment_and_requires_new_metric_plan(self):
        experiment, rules, _ = formal_experiment(14)
        a, b = run_pair(experiment, rules)
        self.assertEqual(a.experiment, b.experiment)
        self.assertEqual(b.parent_run_digest, a.digest())
        self.assertNotEqual(a.plan.digest(), b.plan.digest())
        self.assertEqual(a.record.instrument, Status.OK)
        self.assertEqual(b.record.instrument, Status.OK)

    def test_reference_oracle_does_not_call_sine(self):
        with patch("playground.audits.pendulum_process.math.sin", side_effect=AssertionError("circular")):
            lo, hi = sine_bounds(0.5)
        self.assertLess(Fraction(479425538604202, 10**15), lo)
        self.assertLess(lo, hi)
        self.assertLess(hi, Fraction(479425538604204, 10**15))
        self.assertEqual(hi - lo, Fraction(1, 2)**25 / math.factorial(25))

    def test_reference_oracle_retains_exact_binary_input_scope(self):
        self.assertEqual(sine_bounds(0.0), (Fraction(0), Fraction(0)))
        text = self.report["oracle_policy"]["method"]
        self.assertIn("binary radians", text)
        for degree in (10, 14, 14.5, 30):
            theta = math.radians(degree)
            record, _ = reference_check(theta, math.sin(theta))
            self.assertEqual(record.findings, ())

    def test_invalid_reference_inputs_fail_closed(self):
        for theta in (True, 1, -0.1, 0.7, float("nan"), float("inf")):
            with self.subTest(theta=theta), self.assertRaises(ValueError):
                sine_bounds(theta)
        for sine in (float("nan"), float("inf"), 0.5):
            record, _ = reference_check(math.radians(10), sine)
            self.assertIs(record.instrument, Status.FAILED)
            self.assertIs(record.physical, Status.UNTESTED)

    def test_corrupt_reference_blocks_both_metrics_without_physical_blame(self):
        experiment, rules, _ = formal_experiment(10, sine_override=0.5)
        with patch("playground.equations.substitution._calculate") as calculate:
            runs = run_pair(experiment, rules)
            calculate.assert_not_called()
        for run in runs:
            self.assertIs(run.state, RunState.BLOCKED)
            self.assertIs(run.record.instrument, Status.FAILED)
            self.assertIs(run.record.physical, Status.UNTESTED)
            self.assertIsNone(run.known_answer)
        self.assertEqual(runs[0].experiment.diagnostics, runs[1].experiment.diagnostics)

    def test_planted_probes_are_labeled_and_do_not_become_observations(self):
        self.assertEqual(set(self.inspection["probes"]),
                         {"period-transfer", "angle-convention-change", "corrupt-reference"})
        for probe in self.inspection["probes"].values():
            self.assertEqual(probe["input_kind"], "PLANTED_NOT_OBSERVED")
            self.assertTrue(all(r["state"] == RunState.BLOCKED.value for r in probe["runs"]))

    def test_period_and_angle_convention_transfer_stop_before_calculation(self):
        for kwargs in ({"output_quantity": "period-relative-error"}, {"convention": "degrees"}):
            experiment, rules, _ = formal_experiment(10, **kwargs)
            with patch("playground.equations.substitution._calculate") as calculate:
                runs = run_pair(experiment, rules)
                calculate.assert_not_called()
            for run in runs:
                self.assertEqual(run.applicability.scope.value, "outside-declared-domain")
                self.assertIs(run.record.physical, Status.UNTESTED)

    def test_exact_threshold_is_not_confused_with_source_strict_inequality(self):
        controls = self.inspection["exact_threshold_controls"]
        self.assertEqual([c["inclusive"] for c in controls], ["MET", "MET", "NOT_MET"])
        self.assertEqual([c["strict"] for c in controls], ["MET", "NOT_MET", "NOT_MET"])
        self.assertEqual(criterion((Fraction(0), Fraction(1))), "UNRESOLVED_NUMERIC_BOUND")
        self.assertEqual(criterion(None), "UNDEFINED")

    def test_rational_error_bounds_retain_metric_definition(self):
        theta = math.radians(14)
        bounds = sine_bounds(theta)
        self.assertEqual(criterion(metric_bounds(theta, bounds, "sine")), "NOT_MET")
        self.assertEqual(criterion(metric_bounds(theta, bounds, "angle")), "MET")
        with self.assertRaises(ValueError):
            metric_bounds(theta, bounds, "unspecified")

    def test_no_physical_experiment_support_or_output_uncertainty_is_invented(self):
        self.assertFalse(self.inspection["physical_experiment_constructed"])
        self.assertFalse(self.inspection["claim_support_promoted"])
        self.assertEqual(self.inspection["physical_status"], "UNTESTED")
        self.assertTrue(self.inspection["missing_physical"])
        for case in self.cases.values():
            for metric in case["metrics"].values():
                self.assertFalse(any(f["axis"] == "physical" for f in metric["run"]["record"]["findings"]))
                for value in metric["run"]["outputs"]:
                    self.assertIsNone(value["uncertainty"])

    def test_formal_l0_does_not_claim_pendulum_energy_closure(self):
        experiment, _, _ = formal_experiment(14)
        self.assertEqual([a.quantity for a in experiment.boundary.accounting.accounts], ["case_weight"])
        self.assertIn("not pendulum energy", experiment.anchor.conditions[0])
        self.assertEqual({c.domain for c in experiment.context.conditions}, set(Domain))

    def test_corrupt_arithmetic_is_instrument_failure_not_physical_failure(self):
        experiment, rules, _ = formal_experiment(14)
        model = replace(models(rules)[0], outputs=(OutputPort("error", "0", "1"),))
        registry = EquationRegistry()
        registry.register(model)
        run = execute(registry, model.equation_id, model.revision, experiment,
                      plan(model, experiment), model.decision)
        self.assertIs(run.state, RunState.BLOCKED)
        self.assertIs(run.record.instrument, Status.FAILED)
        self.assertIs(run.record.physical, Status.UNTESTED)
        self.assertEqual(run.stages[-1], "known-answer:blocked")

    def test_other_metrics_passing_plan_cannot_be_reused(self):
        experiment, rules, _ = formal_experiment(14)
        a, b = models(rules)
        registry = EquationRegistry()
        registry.register(b)
        with patch("playground.equations.substitution._calculate") as calculate:
            run = execute(registry, b.equation_id, b.revision, experiment,
                          plan(a, experiment), b.decision)
            calculate.assert_not_called()
        self.assertIs(run.record.determination, Status.FAILED)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_computation_tolerance_is_recorded_separately_from_physical_uncertainty(self):
        self.assertEqual(self.report["oracle_policy"]["metric_computation_tolerance"], NUMERIC_TOLERANCE)
        self.assertIn("never physical uncertainty", self.report["oracle_policy"]["meaning"])

    def test_source_review_is_attributed_not_misrepresented_as_full_archive(self):
        source = self.report["source_inspection"]
        self.assertEqual(source["record_kind"], "ATTRIBUTED_SOURCE_INSPECTION_NOT_FULL_SOURCE_ARCHIVE")
        self.assertIn("cached response", source["retrieval"])
        self.assertTrue(source["source_url"].startswith("https://openstax.org/"))
        self.assertIn("denominator", source["unresolved"][0])
        self.assertIn(SOURCE, self.report["pinned_sha256"])

    def test_changed_snapshot_blocks_before_legacy_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            for name in PINNED:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            (root / SOURCE).write_text('{"PLANTED": "altered inspection"}\n')
            with patch("playground.audits.pendulum_process.subprocess.run") as legacy:
                with self.assertRaisesRegex(ValueError, "explicit reinspection"):
                    run_pilot(Path(temp) / "output", root)
                legacy.assert_not_called()
            self.assertFalse((Path(temp) / "output").exists())

    def test_existing_and_repository_output_targets_are_refused(self):
        with self.assertRaises(FileExistsError):
            run_pilot(self.output)
        with self.assertRaises(ValueError):
            run_pilot(ROOT / "PLANTED-do-not-create")
        self.assertFalse((ROOT / "PLANTED-do-not-create").exists())

    def test_invalid_selected_angles_are_not_silently_coerced(self):
        for degree in (True, -1, 31, float("inf"), float("nan"), "14"):
            with self.subTest(degree=degree), self.assertRaises(ValueError):
                formal_experiment(degree)

    def test_inspectable_json_and_readable_report_are_both_available(self):
        payload = json.loads((self.output / "pendulum-audit-process-report.json").read_text())
        self.assertEqual(payload["schema"], "pendulum-process-pilot/0.1")
        json.dumps(payload, allow_nan=False)
        self.assertTrue(payload["diagnostic_code_sha256"])
        self.assertTrue(payload["platform"])
        text = (self.output / "pendulum-audit-process-report.md").read_text()
        self.assertIn("https://openstax.org/", text)
        self.assertIn("not period error", text)


if __name__ == "__main__":
    unittest.main()
