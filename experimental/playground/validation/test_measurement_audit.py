"""Third pilot: measured indications, diagnostic validity and claim support differ."""

import copy
import json
import tempfile
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from ..audits.measurement_process import (
    DECISION, PRIOR_PINNED, REQUIRED_TERMS, ROOT, SOURCE, SOURCE_SHA256,
    BoundaryFixture, CalibrationFixture, bounded_rule, compare, covariance_record,
    finding, formal_experiment, model, paired_statistics, plan, read_source,
    run_case, run_pilot, sha,
)
from ..equations.adapter import EquationRegistry, OutputPort
from ..equations.substitution import RunState, execute, substitute
from ..failures import Axis, Status


class MeasurementAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name) / "fresh-pilot"
        cls.report = run_pilot(cls.output)
        cls.inspection = cls.report["inspection"]
        cls.source = read_source()
        cls.stats = paired_statistics(cls.source)
        cls.paired = run_case(cls.stats)
        cls.cal = CalibrationFixture(cls.paired.experiment.context.digest(), 0.01)
        cls.boundary = BoundaryFixture(cls.paired.experiment.context.digest(), REQUIRED_TERMS)

    def bridge(self, run=None, **kwargs):
        args = dict(cross_covariance=0.0, calibration=self.cal, boundary=self.boundary)
        args.update(kwargs)
        return compare(self.paired if run is None else run, **args)

    def test_source_and_prior_records_stay_byte_identical(self):
        self.assertEqual(sha(ROOT / SOURCE), SOURCE_SHA256)
        self.assertTrue(self.report["original_source_record_unchanged"])
        self.assertTrue(self.report["prior_pilot_source_pins_unchanged"])
        self.assertEqual(self.report["preserved_prior_records_sha256"], PRIOR_PINNED)
        self.assertEqual({k: sha(ROOT / k) for k in PRIOR_PINNED}, PRIOR_PINNED)

    def test_source_is_explicitly_illustrative_not_authenticated_measurements(self):
        self.assertIn("WORKED_EXAMPLE", self.source["record_kind"])
        self.assertIn("real measurements", self.source["provenance_warning_excerpt"])
        self.assertFalse(self.inspection["physical_experiment_constructed"])
        self.assertIn("sequential", self.source["zero_covariance_check_scope"])
        self.assertEqual(self.inspection["whole_source_verdict"], "NOT_ISSUED")

    def test_transcribed_means_and_explicit_milliamp_conversion(self):
        self.assertEqual(self.stats["v"], Fraction("4.9990"))
        self.assertEqual(self.stats["i"], Fraction("0.0196610"))
        self.assertEqual(self.stats["vv"], Fraction("0.0000103"))
        self.assertEqual(self.stats["ii"], Fraction("0.0000000000897"))
        self.assertEqual(self.stats["cov"], Fraction("-0.0000000108"))

    def test_exact_centered_pair_oracle_matches_covariance_formula(self):
        s = self.stats
        formula = s["vv"]/s["i"]**2 + s["v"]**2*s["ii"]/s["i"]**4 - 2*s["v"]*s["cov"]/s["i"]**3
        self.assertEqual(formula, s["oracle_variance"])
        self.assertLess(s["cov"], 0)
        self.assertLess(s["cov"]**2, s["vv"]*s["ii"])

    def test_reported_rounding_intervals_check_estimate_and_two_budgets(self):
        s = self.stats
        self.assertLess(abs(s["ratio_of_means"] - Fraction("254.260")), Fraction("0.0005"))
        self.assertLess(Fraction("0.2355")**2, s["oracle_variance"])
        self.assertLess(s["oracle_variance"], Fraction("0.2365")**2)
        diagonal = s["vv"]/s["i"]**2 + s["v"]**2*s["ii"]/s["i"]**4
        self.assertLess(Fraction("0.2035")**2, diagonal)
        self.assertLess(diagonal, Fraction("0.2045")**2)

    def test_mean_of_ratios_is_retained_as_distinct_not_forced_equivalent(self):
        self.assertNotEqual(self.stats["ratio_of_means"], self.stats["mean_of_ratios"])
        self.assertNotEqual(self.stats["oracle_variance"], self.stats["mean_of_ratios_variance"])
        self.assertLess(abs(self.stats["mean_of_ratios"] - Fraction("254.260")), Fraction("0.0005"))

    def test_pairing_cannot_be_reconstructed_by_silently_sorting_marginals(self):
        source = copy.deepcopy(self.source)
        currents = sorted(r["current"] for r in source["rows"])
        for row, current in zip(source["rows"], currents):
            row["current"] = current
        changed = paired_statistics(source)
        self.assertEqual(changed["v"], self.stats["v"])
        self.assertEqual(changed["i"], self.stats["i"])
        self.assertNotEqual(changed["cov"], self.stats["cov"])
        self.assertNotEqual(changed["oracle_variance"], self.stats["oracle_variance"])

    def test_duplicate_pairs_and_wrong_source_units_are_rejected(self):
        for kind in ("duplicate", "unit"):
            source = copy.deepcopy(self.source)
            if kind == "duplicate":
                source["rows"][1]["pair_id"] = source["rows"][0]["pair_id"]
            else:
                source["source_units"]["current"] = "A"
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                paired_statistics(source)

    def test_no_pair_oracle_uses_the_equation_backend(self):
        with patch("playground.equations.substitution._calculate", side_effect=AssertionError("circular")):
            self.assertEqual(paired_statistics(read_source()), self.stats)

    def test_nominal_case_traverses_every_existing_diagnostic_layer(self):
        self.assertEqual(self.paired.state, RunState.COMPUTED)
        self.assertEqual(self.paired.stages, (
            "protocol-binding:pass", "l0:pass", "applicability:candidate-domain",
            "validation-plan:pass", "known-answer:pass", "null:pass", "calculation:computed",
        ))
        self.assertEqual(self.paired.record.instrument, Status.OK)
        self.assertEqual(self.paired.record.physical, Status.UNTESTED)
        self.assertAlmostEqual(self.paired.outputs[1].value, float(self.stats["oracle_variance"]), places=13)

    def test_missing_input_covariance_blocks_before_backend_and_is_not_zero(self):
        with patch("playground.equations.substitution._calculate", side_effect=AssertionError("bypass")):
            run = run_case(self.stats, "missing")
        self.assertEqual(run.outputs, ())
        self.assertEqual(run.state, RunState.BLOCKED)
        self.assertEqual(run.record.determination, Status.INDETERMINATE)
        self.assertEqual(run.record.instrument, Status.UNTESTED)
        self.assertEqual(run.record.physical, Status.UNTESTED)

    def test_substitution_cannot_erase_missing_covariance(self):
        old = run_case(self.stats, "missing")
        new = replace(old.equation, equation_id="third-pilot-equivalent", outputs=(
            OutputPort("impedance", "v*(1/i)", "ohm"), old.equation.outputs[1]))
        registry = EquationRegistry()
        registry.register(new)
        result = substitute(old, registry, new.equation_id, new.revision,
                            plan(new, old.experiment), DECISION)
        self.assertEqual(result.parent_run_digest, old.digest())
        self.assertEqual(result.experiment.diagnostics, old.experiment.diagnostics)
        self.assertEqual(result.outputs, ())
        self.assertEqual(result.record.determination, Status.INDETERMINATE)
        reported = self.inspection["runs"]["missing_covariance_substitution_probe"]
        self.assertEqual(reported["outputs"], [])
        self.assertTrue(any(f["code"] == "INPUT_COVARIANCE_MISSING"
                            for f in reported["record"]["findings"]))

    def test_invalid_covariance_is_determination_failure_not_model_or_sensor_failure(self):
        for vv, ii, cov in ((-1.0, 1.0, 0.0), (1.0, 1.0, 2.0), (0.0, 0.0, 1.0),
                            (float("nan"), 1.0, 0.0), (1.0, 1.0, True)):
            record = covariance_record(vv, ii, cov)
            self.assertEqual(record.determination, Status.FAILED)
            self.assertEqual(record.physical, Status.UNTESTED)
            self.assertEqual(record.instrument, Status.UNTESTED)

    def test_psd_check_cannot_round_a_negative_determinant_into_zero(self):
        cov = 1.0000000000000002
        ii = 1.0000000000000004
        self.assertEqual(cov*cov, ii)  # Binary multiplication hides the exact violation.
        self.assertGreater(Fraction(cov)**2, Fraction(ii))
        self.assertEqual(covariance_record(1.0, ii, cov).determination, Status.FAILED)

    def test_missing_covariance_does_not_mask_a_known_invalid_diagonal(self):
        record = covariance_record(-1.0, 1.0, None)
        self.assertEqual(record.determination, Status.FAILED)
        self.assertEqual({f.code for f in record.findings},
                         {"INVALID_INPUT_VARIANCE_DIAGONAL", "INPUT_COVARIANCE_MISSING"})
        self.assertEqual(record.instrument, Status.UNTESTED)
        self.assertEqual(record.physical, Status.UNTESTED)

    def test_non_psd_input_budget_cannot_be_executed(self):
        stats = dict(self.stats, cov=Fraction(1, 1000))
        run = run_case(stats)
        self.assertEqual(run.outputs, ())
        self.assertEqual(run.record.determination, Status.FAILED)
        self.assertEqual(run.record.physical, Status.UNTESTED)

    def test_wrong_through_current_observer_is_outside_equation_domain(self):
        run = run_case(self.stats, observer="upstream-current-before-bypass")
        self.assertEqual(run.outputs, ())
        self.assertEqual(run.applicability.scope.value, "outside-declared-domain")
        self.assertEqual(run.record.physical, Status.UNTESTED)

    def test_bad_variance_formula_is_a_software_instrument_failure(self):
        experiment, rules = formal_experiment(self.stats)
        good = model(rules)
        bad = replace(good, equation_id="planted-wrong-cross-term",
                      outputs=(good.outputs[0], OutputPort(
                          "variance", "vv/i**2+v**2*ii/i**4", "ohm^2")))
        registry = EquationRegistry()
        registry.register(bad)
        run = execute(registry, bad.equation_id, bad.revision, experiment, plan(bad, experiment), DECISION)
        self.assertEqual(run.outputs, ())
        self.assertEqual(run.record.instrument, Status.FAILED)
        self.assertEqual(run.record.physical, Status.UNTESTED)
        self.assertIsNone(self.bridge(run)["numeric_comparison"])

    def test_zero_type_a_variation_does_not_mean_perfect_measurement(self):
        stats = dict(self.stats, vv=Fraction(0), ii=Fraction(0), cov=Fraction(0))
        run = run_case(stats)
        self.assertEqual(run.outputs[1].value, 0.0)
        self.assertTrue(all(output.uncertainty is None for output in run.outputs))
        result = compare(run, prediction_u=0.0, cross_covariance=0.0)
        self.assertIsNone(result["numeric_comparison"])
        self.assertEqual(result["empirical_support"], "NOT_PROMOTED")

    def test_missing_estimate_prediction_covariance_is_not_automatic_independence(self):
        result = self.bridge(cross_covariance=None)
        self.assertIsNone(result["numeric_comparison"])
        self.assertEqual(result["conditional_scoped_rule"], "UNRESOLVED")
        self.assertTrue(any("independence not inferred" in x for x in result["unresolved"]))

    def test_invalid_residual_covariance_is_not_clipped_to_valid(self):
        result = self.bridge(cross_covariance=1.0)
        self.assertIsNone(result["numeric_comparison"])
        self.assertEqual(result["axis_statuses"]["determination"], "failed")
        self.assertEqual(result["physical_status"], "untested")

    def test_missing_calibration_blocks_scoped_rule_despite_raw_numeric_match(self):
        result = self.bridge(calibration=None)
        self.assertEqual(result["numeric_comparison"]["raw_random_only_rule"], "MET")
        self.assertEqual(result["conditional_scoped_rule"], "UNRESOLVED")
        self.assertEqual(result["axis_statuses"]["instrument"], "indeterminate")

    def test_missing_bypass_inventory_blocks_despite_calibration_fixture(self):
        result = self.bridge(boundary=replace(
            self.boundary, included_terms=REQUIRED_TERMS[:2], unresolved_terms=("bypass-current",)))
        self.assertEqual(result["conditional_scoped_rule"], "UNRESOLVED")
        self.assertEqual(result["numeric_comparison"]["raw_random_only_rule"], "MET")
        self.assertTrue(any("bypass-current" in x for x in result["unresolved"]))

    def test_stale_scope_wrong_units_and_fake_certificate_labels_are_rejected(self):
        for bad in (replace(self.cal, context_digest="other-case"),
                    replace(self.cal, unit="V"), replace(self.cal, correction_bound=-1),
                    replace(self.cal, correction_bound=float("nan")),
                    replace(self.cal, basis="AUTHENTICATED_CERTIFICATE")):
            result = self.bridge(calibration=bad)
            self.assertEqual(result["conditional_scoped_rule"], "UNRESOLVED")
            self.assertEqual(result["axis_statuses"]["determination"], "failed")
            self.assertEqual(result["physical_status"], "untested")

    def test_stale_boundary_and_false_empirical_boundary_labels_are_rejected(self):
        for bad in (replace(self.boundary, context_digest="other-boundary"),
                    replace(self.boundary, basis="ESTABLISHED_PHYSICAL_FACT")):
            result = self.bridge(boundary=bad)
            self.assertEqual(result["conditional_scoped_rule"], "UNRESOLVED")
            self.assertEqual(result["axis_statuses"]["determination"], "failed")

    def test_all_conditional_inputs_only_license_a_conditional_rule_not_empirical_support(self):
        result = self.bridge()
        self.assertEqual(result["conditional_scoped_rule"], "WITHIN_SELECTED_RULE_FOR_ALL_DECLARED_CORRECTIONS")
        self.assertEqual(result["axis_statuses"], dict(physical="untested", instrument="indeterminate",
                                                      determination="indeterminate"))
        self.assertEqual(result["empirical_support"], "NOT_PROMOTED")
        self.assertIn("NOT_SOURCE", result["numeric_comparison"]["prediction_basis"])

    def test_covariance_counterfactual_changes_only_the_conditional_numeric_outcome(self):
        cases = self.inspection["bridge_cases"]
        good = cases["fully_supplied_conditional_fixture"]
        diagonal = cases["zero_covariance_counterfactual_fixture"]
        self.assertTrue(good["conditional_scoped_rule"].startswith("WITHIN_"))
        self.assertTrue(diagonal["conditional_scoped_rule"].startswith("OUTSIDE_"))
        self.assertEqual(good["axis_statuses"], diagonal["axis_statuses"])
        self.assertEqual(good["empirical_support"], diagonal["empirical_support"])
        native = self.inspection["runs"]["paired_covariance"]
        zero = self.inspection["runs"]["explicit_zero_covariance_probe"]
        self.assertNotEqual(native["context_digest"], zero["context_digest"])

    def test_calibration_bound_straddling_keeps_result_unresolved(self):
        result = self.bridge(calibration=replace(self.cal, correction_bound=0.1))
        self.assertEqual(result["conditional_scoped_rule"], "UNRESOLVED_WITHIN_CALIBRATION_BOUND")
        self.assertTrue(any("cross" in x for x in result["unresolved"]))

    def test_exact_selected_inclusive_rule_boundary_is_not_a_square_root_roundoff_decision(self):
        self.assertTrue(bounded_rule(2.0, 1.0, 0.0, 2.0).startswith("WITHIN_"))
        self.assertTrue(bounded_rule(1.0, 1.0, 1.0, 2.0).startswith("WITHIN_"))
        self.assertEqual(bounded_rule(3.0, 1.0, 1.0, 2.0), "UNRESOLVED_WITHIN_CALIBRATION_BOUND")
        self.assertTrue(bounded_rule(4.0, 1.0, 1.0, 2.0).startswith("OUTSIDE_"))
        self.assertTrue(bounded_rule(-4.0, 1.0, 1.0, 2.0).startswith("OUTSIDE_"))
        with self.assertRaises(ValueError):
            bounded_rule(0, 0, 0, 2)

    def test_rejected_nonfinite_fixture_is_retained_without_non_json_nan_or_zero_replacement(self):
        result = self.bridge(calibration=replace(self.cal, correction_bound=float("nan")))
        self.assertIn("nan", result["supplied_calibration"]["rejected_non_json_input_repr"])
        json.dumps(result, allow_nan=False)
        self.assertEqual(result["conditional_scoped_rule"], "UNRESOLVED")

    def test_complete_looking_but_failed_or_indeterminate_software_cannot_be_compared(self):
        for status in (Status.FAILED, Status.INDETERMINATE):
            record = self.paired.record.with_finding(finding(
                Axis.INSTRUMENT, status, "PLANTED_SOFTWARE_QUALITY_DEFECT", "Do not use retained numbers"))
            result = self.bridge(replace(self.paired, record=record))
            self.assertIsNone(result["numeric_comparison"])
            self.assertEqual(result["conditional_scoped_rule"], "UNRESOLVED")
        blocked = self.bridge(replace(self.paired, state=RunState.BLOCKED))
        self.assertIsNone(blocked["numeric_comparison"])

    def test_nonfinite_comparison_inputs_and_dimension_changes_are_rejected(self):
        for args in (dict(prediction=True), dict(prediction=float("nan")),
                     dict(prediction_u=-1), dict(k=0), dict(prediction_u=1e308)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.bridge(**args)
        outputs = (replace(self.paired.outputs[0], unit="V"), self.paired.outputs[1])
        with self.assertRaises(ValueError):
            self.bridge(replace(self.paired, outputs=outputs))

    def test_source_tamper_requires_reinspection_instead_of_refreshing_the_pin(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / SOURCE
            path.parent.mkdir(parents=True)
            path.write_bytes((ROOT / SOURCE).read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "reinspection"):
                read_source(Path(temp))

    def test_reports_are_strict_json_with_code_bindings_and_explicit_limits(self):
        loaded = json.loads((self.output / "measurement-boundary-audit-report.json").read_text(),
                            parse_constant=lambda x: self.fail(f"Invalid JSON {x}"))
        self.assertEqual(loaded, self.report)
        self.assertIn("experimental/playground/equations/substitution.py", loaded["diagnostic_code_sha256"])
        self.assertIn("experimental/playground/validation/test_measurement_audit.py", loaded["diagnostic_code_sha256"])
        text = (self.output / "measurement-boundary-audit-report.md").read_text()
        for phrase in ("What this does not establish", "not a p-value", "formal case weight",
                       "UNTESTED", "https://www.iso.org/"):
            self.assertIn(phrase, text)

    def test_existing_and_in_repository_output_locations_cannot_be_overwritten(self):
        for path in (self.output, ROOT, ROOT / "unwanted-generated-output"):
            with self.subTest(path=path), self.assertRaises((ValueError, FileExistsError)):
                run_pilot(path)


if __name__ == "__main__":
    unittest.main()
