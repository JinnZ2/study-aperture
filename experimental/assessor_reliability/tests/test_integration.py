"""CC0. End-to-end constructed controls only; no live models or reviewers."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from experimental.assessor_reliability.common import strict_load
from experimental.assessor_reliability.demo import run_demo
from experimental.assessor_reliability.harness import read_capture
from experimental.assessor_reliability.__main__ import main


class IntegrationTests(unittest.TestCase):
    def test_three_builds_and_frozen_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            demo = root / "demo"
            summary = run_demo(demo)
            self.assertEqual(summary["case_variant_count"], 25)
            self.assertEqual(summary["capture_count"], 30)
            self.assertEqual(summary["perturbation_count"], 10)
            self.assertEqual(summary["live_model_assessments"], 0)
            self.assertEqual(summary["completed_independent_reviews"], 0)
            self.assertEqual(summary["reference_packet_count"], 25)
            self.assertEqual(summary["output_packet_count"], 2)
            records = [read_capture(demo / item["path"]) for item in summary["captures"]]
            self.assertTrue(all(c["constructed"] is True for c in records))
            self.assertTrue(all(c["validation"]["schema_valid"] for c in records))
            self.assertTrue(any(c["mechanical"]["dimensions"]["source_identification"]["FAIL"] for c in records))
            self.assertTrue(any(c["mechanical"]["dimensions"]["quote_fidelity"]["FAIL"] for c in records))
            output_manifest = strict_load(demo / "output-review/manifest.json")
            for descriptor in output_manifest["packets"]:
                packet = strict_load(demo / "output-review" / descriptor["packet_path"])
                self.assertIn("assessment_target", packet)
                self.assertEqual(packet["output"]["raw"]["status"], "ANONYMIZED_COPY")
                self.assertNotIn("observations", packet)
                self.assertNotIn("comparison_spec", packet)
                self.assertNotIn("model", packet)
                template = strict_load(demo / "output-review" / descriptor["template_path"])
                self.assertEqual(template["status"], "PENDING")
            repeated = [str(demo / item["path"]) for item in summary["captures"]
                        if "AR12-repeated_assessment-base-copy-" in item["run_id"]]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = main(["repeats", "--captures", *repeated, "--freeze", str(demo / "freeze"),
                               "--output-dir", str(root / "repeats-cli")])
                self.assertEqual(result, 0)
                result = main(["repeats", "--captures", *repeated, "--freeze", str(demo / "freeze"),
                               "--fields", "new.posthoc.rule", "--output-dir", str(root / "posthoc")])
                self.assertEqual(result, 2)
                self.assertFalse((root / "posthoc").exists())
            self.assertTrue((root / "repeats-cli/report.json").is_file())
            with self.assertRaises(FileExistsError):
                run_demo(demo)


if __name__ == "__main__":
    unittest.main()
