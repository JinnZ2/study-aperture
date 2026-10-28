"""Repository integrity tests for study-aperture. CC0, stdlib only.

These checks turn three written rules into enforced ones:

  1. Vendored upstream files are byte-identical to the recorded copies
     (vendored/SHA256SUMS). Upstream oddities are data, not defects.
  2. Example reports are generated, never hand-edited: each
     examples/*/report.md must equal `assess.py report` on its assessment.json,
     and every example record (and TEMPLATE.json) must pass `assess.py check`.
  3. Vocabulary is defined once, in assess.py. The sets written in README.md,
     CLAUDE.md, and AI_ENTRY_PROMPT.md must match it.

Run from anywhere:  python3 -m unittest discover -s tests
"""

import hashlib
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSESS = ROOT / "assess.py"
VENDORED = ROOT / "vendored"
SUMS = VENDORED / "SHA256SUMS"

# Toolbox-written files in vendored/ that are NOT upstream copies and may change.
TOOLBOX_WRITTEN = {"safe_provenance.py"}

_spec = importlib.util.spec_from_file_location("assess", ASSESS)
assess = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(assess)

# Universal missing-value sentinel: accepted in several sets, documented
# separately ("UNDECLARED, NODATA, NOTFOUND are values"), so docs may omit it.
SENTINEL = "UNDECLARED"

# Doc label (lowercased) -> name of the set in assess.py.
VOCAB = {
    "publication types": "PUB_TYPES",
    "claim support": "SUPPORT",
    "measurement grades": "MEASUREMENT_GRADES",
    "epistemic labels": "CLAIM_LABELS",
    "tool states": "TOOL_STATES",
    "decision states": "DECISION_STATES",
    "design check states": "DESIGN_CHECK_STATES",
    "lab report statuses": "LAB_REPORT_STATUSES",
    "stationarity states": "STATIONARITY_STATES",
    "error types": "ERROR_TYPES",
}

# Sets AI_ENTRY_PROMPT.md must teach the model (it does not define design-check
# states; the CLI handoff table covers those).
PROMPT_SETS = ["PUB_TYPES", "SUPPORT", "MEASUREMENT_GRADES", "CLAIM_LABELS",
               "TOOL_STATES", "DECISION_STATES", "STATIONARITY_STATES",
               "ERROR_TYPES"]

TOKEN = re.compile(r"\b[A-Z][A-Z0-9_]*[A-Z]\b")  # digits allowed inside (E1_DROPPED_VARIABLE)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _code_set(name):
    return set(getattr(assess, name)) - {SENTINEL}


def _run(*args):
    return subprocess.run([sys.executable, str(ASSESS), *args],
                          cwd=ROOT, capture_output=True, text=True)


class VendoredFilesUnchanged(unittest.TestCase):

    def _recorded(self):
        self.assertTrue(SUMS.exists(), f"missing {SUMS.relative_to(ROOT)}")
        recorded = {}
        for n, line in enumerate(SUMS.read_text().splitlines(), 1):
            if not line.strip() or line.startswith("#"):
                continue
            digest, _, name = line.partition("  ")
            self.assertRegex(digest, r"^[0-9a-f]{64}$", f"SHA256SUMS line {n} malformed")
            recorded[name.strip()] = digest
        return recorded

    def test_hashes_match(self):
        for name, digest in self._recorded().items():
            with self.subTest(file=name):
                path = VENDORED / name
                self.assertTrue(path.exists(), f"vendored/{name} listed but missing")
                self.assertEqual(
                    _sha256(path), digest,
                    f"vendored/{name} differs from the recorded upstream copy. "
                    "Vendored files are verbatim; put changes in an adapter or upstream. "
                    "If this is a deliberate re-vendor, update SHA256SUMS and PROVENANCE.md together.")

    def test_every_vendored_file_is_registered(self):
        recorded = set(self._recorded())
        for path in sorted(VENDORED.glob("*.py")):
            if path.name in TOOLBOX_WRITTEN:
                continue
            with self.subTest(file=path.name):
                self.assertIn(path.name, recorded,
                              f"vendored/{path.name} is not in SHA256SUMS "
                              "(or add it to TOOLBOX_WRITTEN if it is toolbox-written)")

    def test_registered_files_have_provenance(self):
        provenance = (VENDORED / "PROVENANCE.md").read_text()
        for name in self._recorded():
            with self.subTest(file=name):
                self.assertIn(f"`{name}`", provenance,
                              f"vendored/{name} has no row in PROVENANCE.md")


class ExampleReportsRegenerate(unittest.TestCase):

    def test_template_is_valid(self):
        r = _run("check", "--file", "TEMPLATE.json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_examples(self):
        examples = sorted(ROOT.glob("examples/*/assessment.json"))
        self.assertTrue(examples, "no example records found")
        for record in examples:
            rel = record.relative_to(ROOT)
            report = record.with_name("report.md")
            with self.subTest(example=str(rel.parent)):
                r = _run("check", "--file", str(rel))
                self.assertEqual(r.returncode, 0, f"{rel} is not VALID:\n{r.stdout}{r.stderr}")
                self.assertTrue(report.exists(), f"{rel.parent}/report.md missing")
                r = _run("report", "--file", str(rel))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(
                    r.stdout, report.read_text(),
                    f"{rel.parent}/report.md does not match its record. Reports are generated; "
                    f"regenerate with: python3 assess.py report --file {rel} > {rel.parent}/report.md")


class AuditsRegenerate(unittest.TestCase):

    def test_final_json_matches_consolidate(self):
        for script in sorted(ROOT.glob("audits/*/consolidate.py")):
            final = script.parent / "data" / "final.json"
            with self.subTest(audit=script.parent.name):
                self.assertTrue(final.exists(), f"{final.relative_to(ROOT)} missing")
                before = final.read_bytes()
                r = subprocess.run([sys.executable, "-B", str(script)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                after = final.read_bytes()
                if after != before:
                    final.write_bytes(before)  # leave the tree as found
                self.assertEqual(after, before,
                                 f"{final.relative_to(ROOT)} does not match its data; "
                                 f"regenerate with: python3 {script.relative_to(ROOT)}")


class VocabularyInSync(unittest.TestCase):

    def _check_doc(self, doc_sets, source):
        for label, name in VOCAB.items():
            with self.subTest(doc=source, set=label):
                self.assertIn(label, doc_sets, f"{source}: no '{label}' entry")
                got = doc_sets[label] - {SENTINEL}
                want = _code_set(name)
                self.assertEqual(
                    got, want,
                    f"{source} '{label}' disagrees with assess.py {name}: "
                    f"missing {sorted(want - got)}, extra {sorted(got - want)}")

    def test_readme(self):
        text = (ROOT / "README.md").read_text()
        doc = {}
        for m in re.finditer(r"^- \*\*(.+?):\*\*(.+)$", text, re.M):
            label = m.group(1).strip().lower()
            if label in VOCAB:
                doc[label] = set(TOKEN.findall(m.group(2)))
        self._check_doc(doc, "README.md")

    def test_claude_md(self):
        text = (ROOT / "CLAUDE.md").read_text()
        doc = {}
        for m in re.finditer(r"^\|\s*([a-z][a-z ]+?)\s*\|(.+)\|\s*$", text, re.M):
            label = m.group(1).strip().lower()
            if label in VOCAB:
                doc[label] = set(TOKEN.findall(m.group(2)))
        self._check_doc(doc, "CLAUDE.md")

    def test_ai_entry_prompt_mentions_every_value(self):
        words = set(TOKEN.findall((ROOT / "AI_ENTRY_PROMPT.md").read_text()))
        for name in PROMPT_SETS:
            with self.subTest(set=name):
                missing = _code_set(name) - words
                self.assertFalse(missing, f"AI_ENTRY_PROMPT.md never mentions {sorted(missing)} from {name}")


if __name__ == "__main__":
    unittest.main()
