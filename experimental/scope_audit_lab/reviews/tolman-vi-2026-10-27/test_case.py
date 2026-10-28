"""Authoring tests for bounded study probes; no general physics engine claimed."""

import hashlib
import json
import math
import socket
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

import run_case as case
from extract_source import Extractor


class CaseTests(unittest.TestCase):
    def test_simpson_cubic(self):
        self.assertAlmostEqual(case.simpson(lambda x:x**3,0,2,10),4.,places=13)

    def test_simpson_invalid_steps(self):
        for n in (0,1,3,-2,2.5,True):
            with self.subTest(n=n),self.assertRaises(ValueError):
                case.simpson(lambda x:x,0,1,n)

    def test_simpson_nonfinite(self):
        with self.assertRaises(ValueError):
            case.simpson(lambda x:float("nan"),0,1,4)

    def test_invalid_domains_rejected(self):
        for args in ((0,10,1,.2,.1),(-1,10,1,.2,.1),(1,0,0,.2,.1),
                     (1,1,2,.2,.1),(1,1,0,1,.1),(1,10,0,-.2,.1),
                     (float("nan"),10,0,.2,.1)):
            with self.subTest(args=args),self.assertRaises(ValueError):
                case.domain(*args)

    def test_invalid_metric_a(self):
        for a in (0,-1,float("nan")):
            with self.assertRaises(ValueError):
                case.exact_difference(1,10,0,.2,.1,a)

    def test_equal_masses_zero_difference(self):
        self.assertEqual(case.exact_difference(1,10,0,.1,.1,1.75),0)

    def test_mass_order_reverses_exact_phase(self):
        a=case.exact_difference(1,10,1,.2,.1,1.75)
        b=case.exact_difference(1,10,1,.1,.2,1.75)
        self.assertEqual(a,-b)

    def test_rationalization_matches_direct_at_safe_inputs(self):
        r,E,L,mk,mj,a=2.,2.,.2,.4,.2,1.75
        q=case.domain(r,E,L,mk,mj)
        direct=math.sqrt(a)*(math.sqrt(q-mk**2)-math.sqrt(q-mj**2))
        self.assertAlmostEqual(direct,case.exact_difference(r,E,L,mk,mj,a),places=14)

    def test_exact_rational_coefficients(self):
        c=case.compute()["coefficient_check"]
        self.assertTrue(c["pressure_isotropy_and_p_equals_rho_over_3"])
        self.assertEqual(c["trace_coefficient"],"0")

    def test_source_sign_discrepancy_preserved(self):
        for row in case.compute()["numerical_trials"]:
            self.assertLess(row["eq8_difference_convergence"][-1],0)
            self.assertGreater(row["eq12_source_expansion"],0)
            self.assertFalse(row["source_sign_agreement"])

    def test_source_primitive_agrees_only_at_samples(self):
        for row in case.compute()["numerical_trials"]:
            self.assertTrue(row["eq12_eq13_sampled_agreement"])
            self.assertLess(abs(row["eq13_minus_eq12"]),1e-10)

    def test_small_parameters_and_convergence(self):
        for row in case.compute()["numerical_trials"]:
            self.assertLess(row["max_expansion_parameter_m2_over_q"],.001)
            self.assertTrue(row["convergence_difference_below_tolerance"])

    def test_conditional_taylor_remainder(self):
        for row in case.compute()["numerical_trials"]:
            self.assertLess(abs(row["literal_taylor_minus_eq8"]),row["conditional_taylor_remainder_bound"]+1e-13)

    def test_selected_source_date_and_hash(self):
        source=case.HERE/"source-extract.json"
        lock=json.loads((case.HERE/"source-lock.json").read_text())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),lock["source_extract_sha256"])
        parsed=json.loads(source.read_text())
        self.assertIn("2026/10/27",parsed["citation_metadata"]["citation_online_date"])
        self.assertIn("-\\frac{\\Delta m^4",parsed["equations"]["Equ12"])

    def test_extractor_preserves_math_sign_and_html_entities(self):
        p=Extractor()
        p.feed('<div id="Equ12"><div><span class="mathjax-tex">a &amp; +b-c</span></div></div>')
        self.assertEqual(p.equations["Equ12"],"a & +b-c")

    def test_extractor_repeated_id_rejected(self):
        p=Extractor()
        with self.assertRaises(ValueError):
            p.feed('<div id="Equ8"><span class="mathjax-tex">x</span></div>'*2)

    def test_missing_evidence_not_fabricated(self):
        source=json.loads((case.HERE/"source-extract.json").read_text())
        bundle=case.evidence_bundle(source,case.compute())
        report=case.load_checker().check_records(bundle["records"])
        self.assertEqual(report["summary"]["finding_counts"]["ERROR"],0)
        self.assertGreater(report["summary"]["finding_counts"]["UNKNOWN"],0)
        self.assertEqual(report["mathematical_or_empirical_validation"],"NOT_PERFORMED")
        criteria=[r["payload"]["criteria"][0] for r in bundle["records"] if r["record_type"]=="assessment"]
        outcomes={c["criterion_id"]:c["outcome"] for c in criteria}
        self.assertEqual(outcomes["empirical"],"NOT_EVALUATED")
        self.assertEqual(outcomes["coordinate-units"],"INDETERMINATE")
        self.assertEqual(outcomes["phase-expansion"],"NOT_MET")

    def test_mappings_match_exact_declared_criteria(self):
        mappings=json.loads((case.HERE/"mappings.json").read_text())
        source=json.loads((case.HERE/"source-extract.json").read_text())
        rows=case.evidence_bundle(source,case.compute())["records"]
        by_id={r["record_id"]:r for r in rows}
        self.assertEqual(mappings["status"],"DRAFT_NOT_EXECUTABLE")
        ids=[m["mapping_id"] for m in mappings["mappings"]]
        self.assertEqual(len(ids),len(set(ids)))
        for m in mappings["mappings"]:
            assessment=by_id[m["assessment_id"]]
            c=assessment["payload"]["criteria"][0]
            self.assertEqual(assessment["record_version"]["value"],case.VERSION)
            self.assertEqual(c["version"]["value"],mappings["binding_convention"]["criterion_version"])
            self.assertEqual(assessment["payload"]["subjects"][0]["examined_version"]["value"],
                             mappings["binding_convention"]["record_version"])
            self.assertEqual(c["criterion_id"],m["criterion_id"])
            self.assertEqual(c["exact_rule"],m["exact_rule"])
            self.assertEqual(assessment["payload"]["subjects"][0]["subject"]["record_id"],m["subject_id"])

    def test_no_network_or_submitted_execution(self):
        with patch.object(socket,"socket",side_effect=AssertionError("network")),patch.object(
                subprocess,"run",side_effect=AssertionError("subprocess")):
            self.assertEqual(len(case.compute()["numerical_trials"]),3)


if __name__=="__main__":
    unittest.main()
