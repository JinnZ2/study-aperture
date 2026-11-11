"""Offline capture-integrity checks, not model or publication validation.

The original user-supplied assessment strings stay separate from the review.
No network, model calls, or assess.py record conversion is performed here.
"""

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "audits" / "gemini-assessment-records-2026-11-11"
# Pin the original capture independently of the descriptive manifest.
CAPTURES = {
    "attempt-01": (
        "6dcc25cb8b77bf5fbd65a1a3d1a3883cb7382aca9798c7f6e6b8f5fe1a4cbd85",
        6274, 42, ["2611.00496", "2611.12122", "2611.12865"],
    ),
    "attempt-02": (
        "a57f43198198d2e2bf3dec17d925e01bdc918d3e8725558834937104cf43b9ca",
        2288, 14, ["2611.00166"],
    ),
}


class AssessmentSpecimenIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (COLLECTION / "manifest.json").read_text(encoding="utf-8")
        )

    def test_capture_inventory_and_no_unregistered_raw_files(self):
        self.assertEqual(
            self.manifest["schema"], "study-aperture/assessment-specimens/1"
        )
        specimens = self.manifest["specimens"]
        self.assertEqual([s["id"] for s in specimens], list(CAPTURES))
        expected = {f"data/{key}.txt" for key in CAPTURES}
        self.assertEqual({s["path"] for s in specimens}, expected)
        self.assertEqual(
            {str(p.relative_to(COLLECTION)) for p in
             (COLLECTION / "data").iterdir() if p.is_file()}, expected
        )

    def test_captured_bytes_match_manifest_and_original_pins(self):
        for specimen in self.manifest["specimens"]:
            with self.subTest(specimen=specimen["id"]):
                digest, size, lines, _ = CAPTURES[specimen["id"]]
                raw = (COLLECTION / specimen["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                self.assertEqual(specimen["sha256"], digest)
                self.assertEqual(len(raw), size)
                self.assertEqual(specimen["bytes"], size)
                self.assertEqual(raw.count(b"\n"), lines)
                self.assertEqual(specimen["lines"], lines)
                self.assertNotIn(b"\r", raw)
                self.assertTrue(raw.endswith(b"\n"))
                raw.decode("utf-8")  # strict decode; never repair capture bytes
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        for specimen in self.manifest["specimens"]:
            path = str((COLLECTION / specimen["path"]).relative_to(ROOT))
            self.assertIn(f"{path} -text -whitespace", attributes)

    def test_record_boundaries_and_original_publication_ids(self):
        for specimen in self.manifest["specimens"]:
            with self.subTest(specimen=specimen["id"]):
                text = (COLLECTION / specimen["path"]).read_text(
                    encoding="utf-8"
                )
                headers = re.findall(r"^PUBLICATION: .+$", text, re.MULTILINE)
                expected = CAPTURES[specimen["id"]][3]
                self.assertTrue(text.startswith("PUBLICATION:"))
                self.assertTrue(text.splitlines()[-1].startswith("INCOMPLETENESS:"))
                self.assertEqual(len(headers), len(expected))
                self.assertEqual(specimen["publication_records"], len(expected))
                self.assertEqual(
                    [re.search(r"arXiv:([0-9.]+)", h).group(1) for h in headers],
                    expected,
                )
                self.assertEqual(specimen["publication_ids_as_supplied"], expected)

    def test_unusual_original_text_is_not_normalized_or_corrected(self):
        first = (COLLECTION / "data/attempt-01.txt").read_bytes()
        second = (COLLECTION / "data/attempt-02.txt").read_bytes()
        self.assertIn("INPUT AVERAGES:\u00a0 \n".encode("utf-8"), first)
        self.assertIn(b"FAZE achieved the best performance", first)
        self.assertIn(b"Choi et al. / BRACE, arXiv:2611.12865", first)
        self.assertIn(b"stationarity: ASSESSED", first)
        self.assertIn(b"\\bm{\\pi_m}", second)
        self.assertIn(b"INDEPENDENCE: INDEPENDENT_CONVERGENCE", second)

    def test_capture_conditions_and_unknowns_remain_explicit(self):
        capture = self.manifest["capture"]
        self.assertFalse(capture["content_corrections_applied"])
        self.assertFalse(capture["authenticated_model_export"])
        self.assertFalse(capture["conversational_prefaces_included"])
        self.assertEqual(capture["encoding"], "UTF-8")
        self.assertEqual(capture["line_endings"], "LF")
        self.assertTrue(capture["terminal_newline"])
        attribution = self.manifest["model_attribution"]
        self.assertEqual(attribution["basis"], "USER_REPORT")
        self.assertFalse(attribution["independently_authenticated"])
        self.assertEqual(attribution["version"], "UNDECLARED")
        self.assertEqual(
            set(self.manifest["unknown_conditions"].values()), {"UNDECLARED"}
        )

    def test_second_attempt_is_not_a_matched_reassessment(self):
        relationship = self.manifest["attempt_relationship"]
        self.assertEqual(relationship["ordering_basis"], "USER_REPORT")
        self.assertTrue(relationship["second_supplied_after_attempted_correction"])
        for key in ("same_publication_reassessment",
                    "controlled_before_after_comparison",
                    "improvement_rate_established"):
            self.assertFalse(relationship[key])
        self.assertTrue(set(CAPTURES["attempt-01"][3]).isdisjoint(
            CAPTURES["attempt-02"][3]
        ))

    def test_review_is_separate_and_records_source_locations(self):
        review = self.manifest["review"]
        self.assertEqual(review["kind"], "SOURCE_COMPARISON_NOT_REPLICATION")
        self.assertFalse(review["specimens_modified"])
        self.assertFalse(review["assess_py_execution_performed_by_reviewer"])
        self.assertFalse(review["source_authentication_implementation_added"])
        self.assertNotIn(review["path"], {
            s["path"] for s in self.manifest["specimens"]
        })
        text = (COLLECTION / review["path"]).read_text(encoding="utf-8")
        self.assertTrue(text.startswith("Status:"))
        for url in review["source_urls"]:
            with self.subTest(url=url):
                self.assertTrue(url.startswith("https://"))
                self.assertIn(f"]({url})", text)
        self.assertGreater(len(review["separate_dimensions"]), 1)

    def test_integrity_does_not_promote_claims_or_establish_validity(self):
        limits = self.manifest["limits"]
        self.assertEqual(
            limits["hash_match_establishes"], "CAPTURED_BYTE_INTEGRITY_ONLY"
        )
        for key, value in limits.items():
            if key != "hash_match_establishes":
                self.assertIs(value, False, key)
        readme = (COLLECTION / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("Status:"))
        self.assertIn("not a model benchmark", (
            ROOT / "README.md"
        ).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
