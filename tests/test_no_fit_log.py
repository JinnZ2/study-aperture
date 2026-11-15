"""ADDENDUM A3 NO_FIT log: shape checks only (no vocabulary is added by it). CC0."""
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = ("id", "record", "where", "vocabulary", "observed_structure", "near_fit",
          "reason_none_fits", "forced_value", "info_lost_if_forced", "state")
STATES = ("NO_FIT", "INSUFFICIENT_INFORMATION", "UNRESOLVED")


class NoFitLog(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "no_fit_log.json"), encoding="utf-8") as fh:
            self.log = json.load(fh)

    def test_every_occurrence_has_every_field(self):
        for o in self.log["occurrences"]:
            for f in FIELDS:
                self.assertIn(f, o, (o.get("id"), f))
            self.assertTrue(o["near_fit"], o["id"])
            for n in o["near_fit"]:
                self.assertTrue(n.get("value") and n.get("why_not"), o["id"])

    def test_states_kept_distinct(self):
        states = [o["state"] for o in self.log["occurrences"]]
        self.assertTrue(set(states) <= set(STATES))
        for s in STATES:                          # each state is in use, not merged away
            self.assertIn(s, states)

    def test_records_exist(self):
        for o in self.log["occurrences"]:
            if o["record"].startswith("examples/"):
                self.assertTrue(os.path.isdir(os.path.join(ROOT, o["record"])), o["id"])

    def test_no_new_enum_in_assess(self):
        with open(os.path.join(ROOT, "assess.py"), encoding="utf-8") as fh:
            src = fh.read()
        for s in ("NO_FIT", "INSUFFICIENT_INFORMATION"):
            self.assertNotIn(f'"{s}"', src)


if __name__ == "__main__":
    unittest.main()
