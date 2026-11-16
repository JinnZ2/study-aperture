"""README claim register: concrete README sentences, bound to assess.py behaviour.

Status: a register of README sentences that state a concrete, runnable result,
each paired with a check of what assess.py does, plus a re-run of the README
Quick start block as written. It fails if a quoted sentence leaves the README
(the prose changed: update the register) or if assess.py no longer does what
the sentence says. Not established: that every concrete README sentence is
registered, or anything about any assessed publication. Run

    python3 tests/test_readme_claims.py --hunt

to list README lines that look like concrete behaviour statements and are not
covered by a registered quote. Those lines are UNCHECKED, not wrong; the
selection rule is a heuristic (PROPOSED). Co-authored. Stdlib only.
"""
import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
LAB_REPORT = ROOT / "examples" / "lab-link" / "integrity-report.json"


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


class Sandbox:
    """A scratch directory holding a copy of assess.py; nothing in the repo is written."""

    def __enter__(self):
        self.dir = Path(tempfile.mkdtemp())
        shutil.copy(ROOT / "assess.py", self.dir)
        shutil.copy(LAB_REPORT, self.dir / "integrity-report.json")
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.dir)

    def run(self, *args):
        r = subprocess.run([sys.executable, "assess.py", *args], cwd=self.dir,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def record(self):
        return json.loads((self.dir / "s.json").read_text())


def quick_start_lines():
    block = README.read_text().split("## Quick start", 1)[1].split("```sh", 1)[1]
    block = block.split("```", 1)[0].replace("\\\n", " ")
    lines = []
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(shlex.split(line, comments=True))
    return lines


def base(sb, depth="FULL_TEXT"):
    sb.run("init", "--file", "s.json", "--title", "t", "--type", "EMPIRICAL")
    sb.run("source", "--file", "s.json", "--id", "S1", "--location", "u", "--depth", depth,
           *(["--detail", "Methods"] if depth == "FULL_TEXT" else []))


def no_evidence_claim():
    with Sandbox() as sb:
        base(sb)
        rc, _ = sb.run("claim", "--file", "s.json", "--id", "C1", "--text", "x",
                       "--support", "UNTESTED", "--label", "OBSERVED")
        _, report = sb.run("report", "--file", "s.json")
        return (rc, sb.record()["claims"][0].get("evidence_location"),
                "evidence location: NO_EVIDENCE_LOCATION" in report,
                "evidence location missing" in report)


def graded_without_sources():
    with Sandbox() as sb:
        base(sb)
        return sb.run("claim", "--file", "s.json", "--id", "C1", "--text", "x",
                      "--evidence", "p1", "--support", "SUPPORTED", "--label", "OBSERVED")[0]


def source_without_depth():
    with Sandbox() as sb:
        sb.run("init", "--file", "s.json", "--title", "t", "--type", "EMPIRICAL")
        return sb.run("source", "--file", "s.json", "--id", "S1", "--location", "u")[0]


def above_ceiling():
    with Sandbox() as sb:
        base(sb, depth="SNIPPET")
        sb.run("claim", "--file", "s.json", "--id", "C1", "--text", "x", "--evidence", "p1",
               "--support", "SUPPORTED", "--label", "OBSERVED", "--source", "u")
        rc, out = sb.run("check", "--file", "s.json")
        rc_strict, _ = sb.run("check", "--strict", "--file", "s.json")
        return rc, "FLAGGED" in out, rc_strict


def frozen_average_rejects_measured():
    with Sandbox() as sb:
        base(sb)
        sb.run("claim", "--file", "s.json", "--id", "C1", "--text", "x", "--evidence", "p1",
               "--support", "UNDETERMINED", "--label", "OBSERVED", "--grade", "MEASURED_PRESENT",
               "--source", "u")
        before = (sb.dir / "s.json").read_text()
        rc, out = sb.run("average", "--file", "s.json", "--id", "A1", "--text", "a",
                         "--value", "0.25", "--population", "UNDECLARED", "--window", "UNDECLARED",
                         "--stationarity", "UNDECLARED", "--claim", "C1")
        return rc, "frozen average" in out, (sb.dir / "s.json").read_text() == before


def not_applicable_is_legal():
    with Sandbox() as sb:
        base(sb)
        sb.run("tool", "--file", "s.json", "--id", "T1", "--card", "03",
               "--state", "NOT_APPLICABLE")
        return sb.run("check", "--file", "s.json")[0]


def check_exits_1_on_violation():
    with Sandbox() as sb:
        base(sb)
        rec = sb.record()
        rec["pub_type"] = "NOT_A_TYPE"
        (sb.dir / "s.json").write_text(json.dumps(rec))
        return sb.run("check", "--file", "s.json")[0]


# (id, quote from README.md, observed(), expected). Quotes match after
# whitespace is collapsed.
CLAIMS = [
    ("no-evidence-is-not-yet-a-claim",
     "A claim without an evidence location is not yet a claim.",
     no_evidence_claim,
     (0, "", True, True)),     # recorded (empty field), shown as NO_EVIDENCE_LOCATION, listed as incomplete
    ("check-exit-1",
     "python3 assess.py check --file s.json     # exit 1 on violations",
     check_exits_1_on_violation,
     1),
    ("frozen-average",
     "a claim resting on a FROZEN average cannot carry a MEASURED_* grade",
     frozen_average_rejects_measured,
     (1, True, True)),                            # rejected, reason given, file unchanged
    ("frozen-average-workflow",
     "with none stated it is FROZEN, and a claim resting on it cannot be graded as measured",
     frozen_average_rejects_measured,
     (1, True, True)),
    ("ceiling-enforced",
     "the depth field and the ceiling table (§4a) are enforced by `assess.py` (above the "
     "ceiling of every source rested on = FLAGGED; `check --strict` exits 3)",
     above_ceiling,
     (0, True, 3)),
    ("not-applicable-legal",
     "Cards that don't apply return `NOT_APPLICABLE` — a legal output.",
     not_applicable_is_legal,
     0),
    ("graded-needs-sources",
     "every source carries its read depth (Card 07)",
     lambda: (graded_without_sources(), source_without_depth()),
     (1, 1)),
]

# Quick start, as written: the exit code each line must give, in order.
QUICK_START_EXPECTED = {"average": 1}             # rejected on purpose; the README says so


class TestReadmeClaims(unittest.TestCase):
    def test_every_quote_is_still_in_the_readme(self):
        text = norm(README.read_text())
        for cid, quote, _, _ in CLAIMS:
            with self.subTest(claim=cid):
                self.assertIn(norm(quote), text,
                              f"{cid}: quote no longer in README.md; the prose changed. "
                              "Re-check the behaviour and update the register.")

    def test_every_quote_matches_behaviour(self):
        for cid, quote, observed, expected in CLAIMS:
            with self.subTest(claim=cid):
                self.assertEqual(observed(), expected,
                                 f"{cid}: README says {quote!r}; assess.py does otherwise")

    def test_quick_start_runs_as_written(self):
        lines = quick_start_lines()
        self.assertGreater(len(lines), 5)
        with Sandbox() as sb:
            for argv in lines:
                self.assertEqual(argv[:2], ["python3", "assess.py"], argv)
                cmd = argv[2]
                with self.subTest(command=cmd):
                    rc, out = sb.run(*argv[2:])
                    self.assertEqual(rc, QUICK_START_EXPECTED.get(cmd, 0),
                                     f"quick start `{cmd}`: exit {rc}\n{out[:400]}")


SIGNAL = re.compile(r"exit \d|exits \d|REJECTED|rejected|FLAGGED|cannot carry|cannot be|"
                    r"is enforced|are enforced|returns? `?[A-Z_]{4,}|never ")


def hunt():
    quotes = [norm(q) for _, q, _, _ in CLAIMS]
    out, in_code = [], False
    for n, line in enumerate(README.read_text().splitlines(), 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        body = norm(line)
        if in_code or not SIGNAL.search(body):
            continue                               # the quick start block is run as a whole
        if any(q in body or body in q for q in quotes):
            continue
        out.append((n, body[:160]))
    return out


if __name__ == "__main__":
    if "--hunt" in sys.argv:
        rows = hunt()
        print(f"README claim hunt: {len(CLAIMS)} registered + quick start run as written; "
              f"{len(rows)} lines UNCHECKED (heuristic selection, PROPOSED; unchecked is not wrong)")
        for n, line in rows:
            print(f"  README.md:{n}: {line}")
    else:
        unittest.main()
