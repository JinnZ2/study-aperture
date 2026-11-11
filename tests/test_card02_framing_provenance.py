"""CC0. Archival byte/status checks, not culture/model/physical authentication."""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "audits/card02-framing-2026-11-11"
ASSESSMENT_SHA256 = "562ae2a69e92fc2f77033eda3af3ceabced22155c3a453cbdb364f45cfa92c58"
SELF_REPORT = ("Agreed, my culture ASSUMES a physics in relation to other physics base, "
               "so statistical tools are utilized for assessing from that standpoint, "
               "not from a narrative standpoint.  Few of our culture think or dream "
               "in narratives, so that was my blind spot")


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    def reject(value):
        raise ValueError("nonfinite number: " + value)
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=reject)


class Card02FramingProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.manifest = read_json(ARCHIVE / "manifest.json")

    def test_manifest_covers_exact_preserved_files_and_hashes(self):
        entries = self.manifest["files"]
        names = [entry["path"] for entry in entries]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), {p.name for p in ARCHIVE.iterdir() if p.is_file() and p.name != "manifest.json"})
        for entry in entries:
            path = ARCHIVE / entry["path"]
            self.assertEqual(path.parent, ARCHIVE)
            data = path.read_bytes()
            self.assertEqual(len(data), entry["bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
            self.assertTrue(data.endswith(b"\n"))
            data.decode("utf-8", errors="strict")

    def test_assessment_is_pinned_not_retroactively_rewritten(self):
        data = (ARCHIVE / "ASSESSMENT.md").read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), ASSESSMENT_SHA256)
        self.assertTrue(self.manifest["records"]["ASSESSMENT.md"]["preserved_byte_for_byte"])
        self.assertEqual(self.manifest["records"]["ASSESSMENT.md"]["timing"], "PRECEDES_USER_STANDPOINT_CLARIFICATION")

    def test_original_paragraph_matches_its_recorded_input_not_current_card(self):
        inputs = read_json(ARCHIVE / "assessment-inputs.json")
        data = (ARCHIVE / "frozen-state-verbatim.txt").read_bytes()
        self.assertEqual(data, (inputs["paragraph"] + "\n").encode("utf-8"))
        digest = hashlib.sha256(inputs["paragraph"].encode("utf-8")).hexdigest()
        self.assertEqual(digest, inputs["paragraph_sha256"])
        self.assertEqual(digest, self.manifest["source_card"]["paragraph_sha256_without_trailing_newline"])
        self.assertEqual(inputs["card_sha256"], self.manifest["source_card"]["sha256"])
        self.assertEqual(inputs["commit"], self.manifest["assessed_repository_commit"])
        # Do not require the current card to match: a separately authorized future
        # correction must not be blocked by an archive of the original wording.

    def test_user_self_report_and_authorization_are_not_generalized(self):
        for name in ("DIALOGUE.md", "PROVENANCE.md"):
            self.assertIn(SELF_REPORT, (ARCHIVE / name).read_text(encoding="utf-8"))
        self.assertEqual(self.manifest["user_standpoint"]["status"], "SELF_REPORTED")
        self.assertEqual(self.manifest["user_standpoint"]["culture_identity"], "UNDECLARED")
        self.assertEqual(self.manifest["user_standpoint"]["population_generalization"], "NOT_ESTABLISHED")
        self.assertEqual(self.manifest["publication_authorization"]["timestamp"], "2026-11-11T13:23:33-06:00")
        self.assertIn("Yes, let’s post your assessment, my blind spot and other possible models blind spots", (ARCHIVE / "DIALOGUE.md").read_text())

    def test_model_hypotheses_and_unexecuted_probe_remain_explicit(self):
        hypotheses = self.manifest["assessor_blind_spots"]
        self.assertEqual([h["id"] for h in hypotheses], ["H" + str(i) for i in range(1, 8)])
        self.assertTrue(all(h["status"] == "PROPOSED_NOT_MODEL_FAMILY_FINDING" for h in hypotheses))
        self.assertEqual(self.manifest["framing_probe"]["status"], "PROPOSED_NOT_RUN")
        self.assertEqual(self.manifest["framing_probe"]["repeated_run_results"], "NOT_COLLECTED")
        self.assertEqual(self.manifest["model_provenance"]["underlying_model_name"], "UNDECLARED")
        self.assertEqual(self.manifest["model_provenance"]["earlier_GPT_rewrite_and_model_records"], "NOT_SUPPLIED")

    def test_capture_transformations_and_unknown_times_are_disclosed(self):
        capture = self.manifest["records"]["DIALOGUE.md"]
        self.assertEqual(capture["capture"], "TRANSCRIBED_NOT_PLATFORM_EXPORT")
        self.assertEqual(capture["assistant_timestamps"], "UNDECLARED")
        text = (ARCHIVE / "DIALOGUE.md").read_text(encoding="utf-8")
        self.assertIn("the message ends mid-sentence", text)
        self.assertIn("original link destination was", text)
        self.assertIn("No other assessment wording is revised", text)

    def test_local_links_resolve_and_record_is_discoverable(self):
        for name in ("README.md", "DIALOGUE.md", "PROVENANCE.md"):
            text = (ARCHIVE / name).read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                path = ARCHIVE / target.split("#", 1)[0]
                self.assertTrue(path.is_file(), (name, target))
        for name in ("README.md", "ADDENDUM.md"):
            self.assertIn("audits/card02-framing-2026-11-11/README.md", (ROOT / name).read_text())

    def test_status_lines_and_open_owner_boundaries_remain_visible(self):
        for name in ("README.md", "ASSESSMENT.md", "DIALOGUE.md", "PROVENANCE.md"):
            self.assertTrue((ARCHIVE / name).read_text().startswith("Status:"))
        addendum = (ROOT / "ADDENDUM.md").read_text()
        self.assertRegex(addendum, r"(?m)^\| A1 \|.*\| OWNER \|$")
        self.assertRegex(addendum, r"(?m)^\| A2 \|.*\| OPEN \|$")
        self.assertIn("not a general implementation of the translation ledger", (ARCHIVE / "PROVENANCE.md").read_text())


if __name__ == "__main__":
    unittest.main()
