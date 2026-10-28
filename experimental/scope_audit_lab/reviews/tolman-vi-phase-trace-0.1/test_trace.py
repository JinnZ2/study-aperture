"""Bounded authoring tests; passing these is not a scientific validity verdict."""

import hashlib
import json
import math
import random
import socket
import subprocess
import unittest
from unittest.mock import patch

import run_trace as trace


class TraceTests(unittest.TestCase):
    def test_amplitude_derives_compact_formula(self):
        rng=random.Random(735)
        for _ in range(100):
            theta=rng.random()*math.pi/2
            pk,pj=rng.uniform(-10,10),rng.uniform(-10,10)
            self.assertAlmostEqual(trace.probability_from_amplitude(theta,pk,pj),
                                   trace.probability(theta,pk-pj),places=13)

    def test_common_phase_invariance(self):
        for shift in (-40.,0.,.3,20.):
            self.assertAlmostEqual(trace.probability_from_amplitude(.3,1.+shift,.2+shift),
                                   trace.probability_from_amplitude(.3,1.,.2),places=13)

    def test_whole_relative_phase_flip(self):
        for f,s in [(1.,.4),(-5.,2.),(.0024,.00037)]:
            self.assertEqual(trace.probability(.5,f,s),trace.probability(.5,-f,-s))

    def test_eikonal_only_flip_invariance(self):
        self.assertEqual(trace.probability(.4,1.),trace.probability(.4,-1.))

    def test_partial_flip_identity(self):
        for theta,f,s in [(.2,.7,.4),(.5,2.,-.3),(math.pi/4,math.pi/2,math.pi/2)]:
            difference=trace.probability(theta,-f,s)-trace.probability(theta,f,s)
            expected=math.sin(2*theta)**2*math.sin(f)*math.sin(s)
            self.assertAlmostEqual(difference,expected,places=14)

    def test_partial_flip_can_change_formal_probability_fully(self):
        # Algebraic phase example, not an asserted physical realization.
        self.assertAlmostEqual(trace.probability(math.pi/4,math.pi/2,math.pi/2),0.)
        self.assertAlmostEqual(trace.probability(math.pi/4,-math.pi/2,math.pi/2),1.)

    def test_spin_orientation_preserved(self):
        for t in trace.compute()["probability_trials"]:
            self.assertEqual([b["spin_orientation"] for b in t["branches"]],[1,-1])
            self.assertAlmostEqual(t["branches"][0]["source_boost_phase"],
                                   -t["branches"][1]["source_boost_phase"])

    def test_reversing_endpoints_reverses_spin(self):
        p=trace.source_boost(1.75,10,.2,.1,1,2)
        self.assertEqual(p,-trace.source_boost(1.75,10,.2,.1,2,1))

    def test_species_swap_reverses_spin(self):
        self.assertEqual(trace.source_boost(1.75,10,.2,.1,1,2),
                         -trace.source_boost(1.75,10,.1,.2,1,2))

    def test_quartic_eikonal_identity(self):
        for t in trace.compute()["probability_trials"]:
            self.assertAlmostEqual(t["eikonal_only_quartic_probability_delta"],
                                   t["quartic_delta_identity_rhs"],places=14)
            self.assertGreater(abs(t["eikonal_only_quartic_probability_delta"]),1e-14)

    def test_finite_trial_probabilities_and_differences(self):
        for t in trace.compute()["probability_trials"]:
            for b in t["branches"]:
                for key in ["published_probability","conditional_eq8_with_unchanged_boost_probability",
                            "global_phase_sign_flip_probability"]:
                    self.assertGreaterEqual(b[key],0); self.assertLessEqual(b[key],1)
                self.assertGreater(abs(b["conditional_minus_published"]),1e-9)
                self.assertAlmostEqual(b["global_phase_sign_flip_probability"],b["published_probability"],places=14)

    def test_uniform_phase_average_quadrature(self):
        for row in trace.compute()["uniform_phase_averaging"]:
            self.assertAlmostEqual(row["phase_average"],row["uniform_phase_quadrature"],places=13)

    def test_zero_mixing_average_is_one(self):
        self.assertEqual(trace.averaged_probability(0),1.)

    def test_maximal_mixing_average_is_half(self):
        self.assertEqual(trace.averaged_probability(math.pi/4),.5)

    def test_nonmaximal_mixing_average_is_not_half(self):
        self.assertEqual(trace.averaged_probability(math.pi/6),.625)

    def test_zero_width_means_no_averaging(self):
        self.assertAlmostEqual(trace.finite_uniform_phase_average(.3,.7,0),
                               trace.probability(.3,.7),places=14)

    def test_full_uniform_phase_period(self):
        for center in (-5.,0.,.7,8.):
            self.assertAlmostEqual(trace.finite_uniform_phase_average(.3,center,2*math.pi),
                                   trace.averaged_probability(.3),places=14)

    def test_partial_window_retains_phase_dependence(self):
        self.assertNotAlmostEqual(trace.finite_uniform_phase_average(.3,.7,.2),
                                  trace.averaged_probability(.3),places=5)

    def test_log_kernel_matches_weighted_quadrature(self):
        old=trace.old_case()
        theta,c,log_eps=math.pi/6,1.,-3.
        # r=epsilon*exp(-x) converts uniform radial weighting to exp(-x) dx.
        numerical=old.simpson(lambda x:math.exp(-x)*trace.probability(theta,c*(log_eps-x)),0,40,8192)
        self.assertAlmostEqual(numerical,trace.uniform_radial_log_average(theta,c,log_eps),places=10)

    def test_log_kernel_subsequences_do_not_collapse(self):
        rows=trace.compute()["log_phase_response_counterexample"]["subsequences"]
        for row in rows:
            self.assertAlmostEqual(row["uniform_radial_average_high"],.8125,places=13)
            self.assertAlmostEqual(row["uniform_radial_average_low"],.4375,places=13)

    def test_nonfinite_values_rejected(self):
        for bad in (float("nan"),float("inf"),-float("inf")):
            with self.assertRaises(ValueError):trace.probability(.3,bad)
            with self.assertRaises(ValueError):trace.averaged_probability(bad)
            with self.assertRaises(ValueError):trace.uniform_radial_log_average(.3,bad,-2.)

    def test_negative_phase_width_rejected(self):
        with self.assertRaises(ValueError):trace.finite_uniform_phase_average(.3,.2,-1)

    def test_boost_invalid_domains_rejected(self):
        for args in [(0,10,.2,.1,1,2),(1.75,0,.2,.1,1,2),(1.75,10,.2,.1,0,2),
                     (1.75,10,-.2,.1,1,2)]:
            with self.assertRaises(ValueError):trace.source_boost(*args)
        for orientation in (0,2,True):
            with self.assertRaises(ValueError):trace.source_boost(1.75,10,.2,.1,1,2,orientation)

    def test_pinned_sources_and_parent_code(self):
        lock=json.loads((trace.HERE/"source-lock.json").read_text())
        for name,digest in lock["examined_sha256"].items():
            self.assertEqual(hashlib.sha256((trace.LAB/name).read_bytes()).hexdigest(),digest)
        source=json.loads((trace.HERE/"sources.json").read_text())
        self.assertEqual(source["preprint"]["version"],"v1")
        self.assertEqual(set(source["publisher"]["equations"]),set(source["preprint"]["equations"]))
        self.assertIn("sin",source["preprint"]["equations"]["Equ35"][0]["original_alttext"])

    def test_unknown_provenance_not_erased(self):
        source=json.loads((trace.HERE/"sources.json").read_text())
        bundle=trace.evidence_bundle(source,trace.compute())
        report=trace.old_case().load_checker().check_records(bundle["records"])
        self.assertEqual(report["summary"]["finding_counts"]["ERROR"],0)
        self.assertGreater(report["summary"]["finding_counts"]["UNKNOWN"],0)
        self.assertEqual(report["mathematical_or_empirical_validation"],"NOT_PERFORMED")
        self.assertTrue(all(r["record_version"]["value"]==trace.VERSION for r in bundle["records"]))
        outcomes={r["payload"]["criteria"][0]["criterion_id"]:r["payload"]["criteria"][0]["outcome"]
                  for r in bundle["records"] if r["record_type"]=="assessment"}
        self.assertEqual(outcomes["empirical-effect"],"NOT_EVALUATED")
        self.assertEqual(outcomes["global-invariance"],"MET")
        self.assertEqual(outcomes["universal-half"],"NOT_MET")

    def test_no_network_or_submitted_execution(self):
        with patch.object(socket,"socket",side_effect=AssertionError("network")),patch.object(
                subprocess,"run",side_effect=AssertionError("subprocess")):
            result=trace.compute()
        self.assertEqual(result["findings"]["corrected_physical_prediction"],"NOT_ESTABLISHED")

    def test_analytical_assessments_have_explicit_derivation_evidence(self):
        source=json.loads((trace.HERE/"sources.json").read_text())
        bundle=trace.evidence_bundle(source,trace.compute())
        records={r["record_id"]:r for r in bundle["records"]}
        for r in records.values():
            if r["record_type"]=="assessment" and r["payload"]["assessment_kind"]=="ANALYTICAL":
                evidence=r["payload"]["criteria"][0]["evidence_refs"]
                self.assertTrue(evidence)
                self.assertTrue(all(records[e["record_id"]]["record_type"]=="derivation" for e in evidence))


if __name__=="__main__":
    unittest.main()
