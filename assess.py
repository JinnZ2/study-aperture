#!/usr/bin/env python3
"""assess.py -- study-aperture: record validator and report generator. CC0, stdlib only.

This tool does NOT judge scientific validity. It holds one assessment record,
validates it against the study-aperture vocabulary, and renders a report that
keeps incompleteness visible. A missing value is a value; it is never silently
converted into a negative finding, a zero, or a completion.

Enforcement notes (the prohibitions are enforced in code, not promised in prose):

  - No silent resolution. The ONLY path into RESOLVED is the `resolve` command,
    which requires --answer AND --by, both non-sentinel. `decide --state RESOLVED`
    is rejected. An invalid mutation exits nonzero and leaves the file unchanged.
  - No defaults for unknowns. A declined tool without a reason is invalid; an
    unresolved decision is the headline of the report, printed first.
  - Validity and completeness are separate. A record can be VALID and INCOMPLETE;
    incompleteness is a state, not an error. Missing evidence stays visibly
    missing; it never becomes a negative finding.

Schema (study-aperture/1):

  record = {
    "title": str,
    "pub_type": one of PUB_TYPES,
    "citation": str,            # where the study itself lives
    "materials": str,           # what you actually had access to (be honest here)
    "decision_context": str,    # what the assessment is FOR; may be UNDECLARED
    "claims": [ {id, text, evidence_location | NO_EVIDENCE_LOCATION,
                 support: one of SUPPORT} ],
    "tools": [ {id, card, state: one of TOOL_STATES, output?, declined_reason?} ],
    "decisions": [ {id, text, state: one of DECISION_STATES,
                    answer?, by?, deferred_reason?} ],
    "notes": str
  }

Commands:
  init --file s.json --title "..." --type EMPIRICAL [--citation ...] [--materials ...]
  claim --file s.json --id C1 --text "..." --evidence "p. 4, Table 1" [--support ...]
        [--measurand ...] [--grade ...] [--falsifiers ...] [--label OBSERVED|DERIVED|PROPOSED] [--source <url>]
        [--range ...] [--instrument ...] [--resolution ...]
  tool  --file s.json --id T1 --card 03 --state RUN --output "..." [--source <url>]
        [--declined-reason ...]
  design --file s.json --check confounding --state CHECKED|NOT_CHECKED|NOT_APPLICABLE
        [--finding "..."] [--source <url>]
  decide --file s.json --id D1 --text "..." --state DETECTED|UNRESOLVED|NOT_APPLICABLE
  resolve --file s.json --id D1 --by user --answer "..."   # the only path to RESOLVED
  defer  --file s.json --id D1 --by user --reason "..."
  check  --file s.json          # validate; exit 1 on violations; file never changed
  report --file s.json          # markdown report; INVALID banner if violations
  selftest
"""
import argparse, json, sys

SCHEMA = "study-aperture/1"

PUB_TYPES = frozenset([
    "EMPIRICAL",        # study generating data from the world
    "REVIEW",           # synthesis of prior studies (incl. meta-analysis)
    "THEORETICAL",      # argument, derivation, model
    "SIMULATION",       # computational experiment on constructed inputs
    "COMMENTARY",       # essay, editorial, position, research note
    "UNDECLARED",       # declared absence: assessor has not recorded a type
])

SUPPORT = frozenset([
    "SUPPORTED",             # later record agrees with the claim as stated
    "PARTIALLY_SUPPORTED",  # agrees in part or under a narrower reading
    "UNSUPPORTED",          # tested; record does not agree
    "CONTRADICTED",         # later record asserts the opposite
    "UNTESTED",             # no later record bears on it
    "UNDETERMINED",         # assessment incomplete; evidence in hand insufficient
])

TOOL_STATES = frozenset([
    "RUN",            # executed; see output
    "DECLINED",       # deliberately not run; reason is the headline, not a gap
    "BLOCKED",        # inputs unavailable; a blocked tool is always incompleteness
    "NOT_APPLICABLE", # publication type or material makes the card inapplicable
])

DECISION_STATES = frozenset([
    "DETECTED",        # decision surface located; nothing more known
    "UNRESOLVED",     # exposed; no answer on record
    "RESOLVED",       # answer + named author on record (only via `resolve`)
    "DEFERRED",       # deliberately postponed; owned
    "NOT_APPLICABLE", # bears no consequence here
])

# Routing DEFAULTS: publication type -> cards suggested. The table is a default,
# not a gate: a claim-level override may add a card (e.g. a COMMENTARY citing
# empirical lineage still runs card 03) — record the override as a tool run
# with its reason. UNDECLARED type routes to nothing.
ROUTER = {
    "EMPIRICAL":   {"00", "01", "02", "03", "04", "05", "06"},
    "REVIEW":      {"00", "01", "02", "03", "04", "06"},
    "THEORETICAL": {"00", "01", "04", "06"},
    "SIMULATION":  {"00", "01", "02", "04", "06"},
    "COMMENTARY":  {"00", "01", "06"},
    "UNDECLARED":  set(),
}

MISSING_VALUES = frozenset(["UNDECLARED", "NODATA", "NOTFOUND"])  # values, not errors

MEASUREMENT_GRADES = frozenset([
    "MEASURED_PRESENT", "MEASURED_ABSENT", "MEASURED_DISCARDED",
    "UNMEASURED", "UNDERPOWERED", "IMPOSED", "UNDECLARED",
])

CLAIM_LABELS = frozenset(["OBSERVED", "DERIVED", "PROPOSED", "UNDECLARED"])

DESIGN_CHECK_STATES = frozenset([
    "CHECKED", "NOT_CHECKED", "NOT_APPLICABLE", "UNDECLARED",
])


def load(path):
    with open(path) as f:
        d = json.load(f)
    if d.get("schema") != SCHEMA:
        raise SystemExit(f"{path}: wrong or missing schema field (want {SCHEMA})")
    for key in ("title", "pub_type", "citation", "materials", "decision_context"):
        d.setdefault(key, "UNDECLARED")
    d.setdefault("claims", []); d.setdefault("tools", [])
    d.setdefault("decisions", []); d.setdefault("design_checks", [])
    d.setdefault("notes", "UNDECLARED")
    return d


def save(d, path):
    with open(path, "w") as f:
        json.dump(d, f, indent=2)


def _is_missing(v):
    return v is None or (isinstance(v, str) and v.strip() == "")


def _is_sentinel(v):
    """A declared absence is not an answer. UNDECLARED/NODATA/NOTFOUND never
    satisfy a required field."""
    return _is_missing(v) or (isinstance(v, str) and v.strip() in MISSING_VALUES)


def check(d):
    """Return list of violation strings. Empty list = valid record."""
    v = []
    if d["pub_type"] not in PUB_TYPES:
        v.append(f"pub_type {d['pub_type']!r} not in vocabulary")
    for c in d["claims"]:
        cid = c.get("id", "?")
        if _is_missing(c.get("text")):
            v.append(f"claim {cid}: text missing")
        if c.get("support") not in (SUPPORT | {"UNDECLARED"}):
            v.append(f"claim {cid}: support {c.get('support')!r} not in vocabulary")
        if c.get("support") in ("SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED",
                                 "CONTRADICTED"):
            loc = c.get("evidence_location", "")
            if _is_sentinel(loc) or loc == "NO_EVIDENCE_LOCATION":
                v.append(f"claim {cid}: support graded without a located evidence "
                         f"(UNDECLARED/NODATA/NOTFOUND are absences, not locations; "
                         f"record NO_EVIDENCE_LOCATION and support UNDETERMINED instead)")
        if c.get("label") not in (None,) and c.get("label") not in CLAIM_LABELS:
            v.append(f"claim {cid}: label {c.get('label')!r} not in vocabulary")
        if c.get("grade") not in (None,) and c.get("grade") not in MEASUREMENT_GRADES:
            v.append(f"claim {cid}: grade {c.get('grade')!r} not in vocabulary")
    for t in d["tools"]:
        tid = t.get("id", "?")
        if t.get("state") not in TOOL_STATES:
            v.append(f"tool {tid}: state {t.get('state')!r} not in vocabulary")
        if t.get("state") == "DECLINED" and _is_missing(t.get("declined_reason")):
            v.append(f"tool {tid}: DECLINED without a reason (a decline is the headline)")
        if _is_missing(t.get("card")):
            v.append(f"tool {tid}: card missing")
    for k in d.get("design_checks", []):
        if k.get("state") not in DESIGN_CHECK_STATES:
            v.append(f"design check {k.get('check', '?')}: state {k.get('state')!r} not in vocabulary")
    for x in d["decisions"]:
        did = x.get("id", "?")
        if x.get("state") not in DECISION_STATES:
            v.append(f"decision {did}: state {x.get('state')!r} not in vocabulary")
        if x.get("state") == "RESOLVED":
            if _is_sentinel(x.get("answer")) or _is_sentinel(x.get("by")):
                v.append(f"decision {did}: RESOLVED requires answer AND by "
                         f"(no silent resolution; sentinels are not answers)")
        if x.get("state") == "DEFERRED" and _is_missing(x.get("deferred_reason")):
            v.append(f"decision {did}: DEFERRED without a reason")
    return v


def incompleteness(d):
    """Everything that keeps this assessment from counting as complete.
    Incompleteness is a state, not an error: the record stays VALID."""
    out = []
    if d["pub_type"] == "UNDECLARED":
        out.append("publication type UNDECLARED (no cards routed)")
    else:
        if not d["claims"]:
            out.append("claims: NODATA (none extracted)")
        if not d["tools"]:
            out.append("tools: NODATA (no cards run)")
        if not d["decisions"] and not _is_sentinel(d.get("decision_context")):
            out.append("decisions: NODATA (context declared but no surfaces recorded)")
    for c in d["claims"]:
        loc = c.get("evidence_location", "")
        if _is_sentinel(loc) or loc == "NO_EVIDENCE_LOCATION":
            out.append(f"claim {c.get('id')}: evidence location missing (NODATA)")
        if c.get("support") in ("UNDETERMINED", None, "UNDECLARED"):
            out.append(f"claim {c.get('id')}: support UNDETERMINED")
    if d["pub_type"] == "EMPIRICAL" and not d.get("design_checks"):
        out.append("design checks: NODATA (EMPIRICAL record without ordinary design "
                   "checks is incomplete)")
    for k in d.get("design_checks", []):
        if k.get("state") == "NOT_CHECKED":
            out.append(f"design check {k.get('check')}: NOT_CHECKED")
    for t in d["tools"]:
        if t.get("state") == "BLOCKED":
            out.append(f"tool {t.get('id')}: BLOCKED (inputs unavailable; always incompleteness)")
        elif t.get("state") == "RUN" and _is_missing(t.get("output")):
            out.append(f"tool {t.get('id')}: RUN with no output recorded")
    for x in d["decisions"]:
        if x.get("state") == "UNRESOLVED":
            out.append(f"decision {x.get('id')}: UNRESOLVED")
        if x.get("state") == "DETECTED":
            out.append(f"decision {x.get('id')}: DETECTED (located, nothing more known)")
        if x.get("state") == "DEFERRED":
            out.append(f"decision {x.get('id')}: DEFERRED (owned, still open)")
    return out


def report(d):
    lines = [f"# Assessment: {d['title']}",
             f"schema {SCHEMA} — generated by study-aperture; this report is a record, not a verdict.",
             ""]
    v = check(d)
    if v:
        lines.append("## RECORD INVALID — the violations below are not findings; fix them")
        lines += [f"- {x}" for x in v]
        lines.append("")
    lines += [f"- citation: {d['citation']}",
              f"- publication type: {d['pub_type']}",
              f"- materials actually held: {d['materials']}",
              f"- decision context: {d['decision_context']}",
              ""]
    inc = incompleteness(d)
    lines.append("## Incompleteness (printed first, on purpose)")
    if inc:
        lines += [f"- {x}" for x in inc]
        lines.append("- => this assessment is INCOMPLETE; treat every graded field below accordingly")
    else:
        lines.append("- none recorded; claims and decisions below carry their states")
    lines.append("")
    routed = ROUTER.get(d["pub_type"], set())
    if routed:
        lines.append(f"cards routed by DEFAULT for type {d['pub_type']}: "
                     + ", ".join(sorted(routed))
                     + " (claim-level overrides may add cards; record them as tool runs)")
    else:
        lines.append("cards routed: none (publication type UNDECLARED)")
    lines.append("")
    lines.append("## Design checks (ordinary study-design appraisal, run before the cards)")
    if not d.get("design_checks"):
        lines.append("- NODATA (no ordinary design checks recorded; an EMPIRICAL record "
                     "without them is incomplete)")
    for k in d.get("design_checks", []):
        lines.append(f"- **{k.get('check')}** ({k.get('state')})")
        if not _is_missing(k.get("finding")):
            lines.append(f"  - finding: {k.get('finding')}")
        if not _is_missing(k.get("source")):
            lines.append(f"  - source: {k.get('source')}")
    lines.append("")
    lines.append("## Claims")
    if not d["claims"]:
        lines.append("- NODATA (no claims extracted yet)")
    for c in d["claims"]:
        loc = c.get("evidence_location", "")
        loc = "NO_EVIDENCE_LOCATION" if _is_missing(loc) else loc
        sup = c.get("support", "UNDECLARED")
        label = f" [{c.get('label')}]" if c.get("label") else ""
        lines.append(f"- **{c.get('id')}**{label} ({sup}) — {c.get('text')}")
        lines.append(f"  - evidence location: {loc}")
        if c.get("measurand"):
            lines.append(f"  - measurand: {c.get('measurand')}")
        if c.get("range"):
            lines.append(f"  - range: {c.get('range')}")
        if c.get("instrument"):
            lines.append(f"  - instrument: {c.get('instrument')}")
        if c.get("grade"):
            lines.append(f"  - grade: {c.get('grade')}")
        if c.get("resolution"):
            lines.append(f"  - resolution: {c.get('resolution')}")
        if c.get("falsifiers"):
            lines.append(f"  - falsifiers: {c.get('falsifiers')}")
        if c.get("source"):
            lines.append(f"  - source: {c.get('source')}")
    lines.append("")
    lines.append("## Tool runs (by card)")
    if not d["tools"]:
        lines.append("- NODATA (no cards run yet)")
    for t in d["tools"]:
        lines.append(f"- **{t.get('id')}** card {t.get('card')} — {t.get('state')}")
        if t.get("state") == "DECLINED":
            lines.append(f"  - declined reason: {t.get('declined_reason')}")
        if not _is_missing(t.get("output")):
            lines.append(f"  - output: {t.get('output')}")
        if t.get("source"):
            lines.append(f"  - source: {t.get('source')}")
    lines.append("")
    lines.append("## Decisions")
    if not d["decisions"]:
        lines.append("- NODATA (no decision surfaces recorded)")
    for x in d["decisions"]:
        lines.append(f"- **{x.get('id')}** ({x.get('state')}) — {x.get('text')}")
        if x.get("state") == "RESOLVED":
            lines.append(f"  - answer: {x.get('answer')} (by {x.get('by')})")
        if x.get("state") == "DEFERRED":
            lines.append(f"  - deferred reason: {x.get('deferred_reason')}")
    lines.append("")
    lines.append("## Notes")
    lines.append(str(d["notes"]))
    return "\n".join(lines)


def _commit(d, path, ok_msg):
    """Save only if the mutated record validates. Exit nonzero, no write, if not."""
    v = check(d)
    if v:
        for x in v:
            print(f"REJECTED (file unchanged): {x}", file=sys.stderr)
        return 1
    save(d, path)
    print(ok_msg)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="study-aperture record validator and report generator")
    p.add_argument("cmd", choices=["init", "claim", "tool", "design", "decide", "resolve", "defer",
                                   "check", "report", "selftest"])
    p.add_argument("--file", default="assessment.json")
    p.add_argument("--title"); p.add_argument("--type", dest="pub_type")
    p.add_argument("--citation"); p.add_argument("--materials"); p.add_argument("--context")
    p.add_argument("--id"); p.add_argument("--text"); p.add_argument("--evidence")
    p.add_argument("--support", default="UNDETERMINED")
    p.add_argument("--card"); p.add_argument("--state"); p.add_argument("--output")
    p.add_argument("--measurand"); p.add_argument("--grade"); p.add_argument("--falsifiers")
    p.add_argument("--label"); p.add_argument("--source")
    p.add_argument("--range", dest="claim_range"); p.add_argument("--instrument")
    p.add_argument("--resolution")
    p.add_argument("--check", dest="design_check"); p.add_argument("--finding")
    p.add_argument("--declined-reason"); p.add_argument("--answer"); p.add_argument("--by")
    p.add_argument("--reason", dest="deferred_reason")
    args = p.parse_args(argv)

    if args.cmd == "selftest":
        return selftest()
    if args.cmd == "init":
        d = {"schema": SCHEMA, "title": args.title or "UNDECLARED",
             "pub_type": args.pub_type or "UNDECLARED",
             "citation": args.citation or "UNDECLARED",
             "materials": args.materials or "UNDECLARED",
             "decision_context": args.context or "UNDECLARED",
             "claims": [], "tools": [], "decisions": [], "notes": "UNDECLARED"}
        v = check(d)
        if v:  # bad --type value
            for x in v: print(f"REJECTED (file unchanged): {x}", file=sys.stderr)
            return 1
        save(d, args.file); print(f"-> {args.file}"); return 0
    d = load(args.file)
    if args.cmd == "claim":
        c = {"id": args.id, "text": args.text,
             "evidence_location": args.evidence or "",
             "support": args.support}
        for opt in ("measurand", "grade", "falsifiers", "label", "source",
                    "claim_range", "instrument", "resolution"):
            if getattr(args, opt):
                c["range" if opt == "claim_range" else opt] = getattr(args, opt)
        d["claims"].append(c)
        return _commit(d, args.file, f"claim {args.id} recorded")
    if args.cmd == "tool":
        t = {"id": args.id, "card": args.card, "state": args.state}
        if args.output: t["output"] = args.output
        if args.declined_reason: t["declined_reason"] = args.declined_reason
        if args.source: t["source"] = args.source
        d["tools"].append(t)
        return _commit(d, args.file, f"tool run {args.id} recorded")
    if args.cmd == "design":
        if not args.design_check or not args.state:
            print("REJECTED (file unchanged): design requires --check and --state.",
                  file=sys.stderr)
            return 1
        k = {"check": args.design_check, "state": args.state}
        if args.finding: k["finding"] = args.finding
        if args.source: k["source"] = args.source
        d["design_checks"].append(k)
        return _commit(d, args.file, f"design check {args.design_check} recorded")
    if args.cmd == "decide":
        if args.state == "RESOLVED":
            print("REJECTED (file unchanged): `decide --state RESOLVED` is the silent-"
                  "resolution path. Use `decide --state UNRESOLVED` then `resolve "
                  "--id ... --by ... --answer ...`.", file=sys.stderr)
            return 1
        if args.state == "DEFERRED" and _is_missing(args.deferred_reason):
            print("REJECTED (file unchanged): DEFERRED requires --reason (use the "
                  "`defer` command).", file=sys.stderr)
            return 1
        x = {"id": args.id, "text": args.text, "state": args.state}
        if args.deferred_reason: x["deferred_reason"] = args.deferred_reason
        d["decisions"].append(x)
        return _commit(d, args.file, f"decision {args.id} recorded")
    if args.cmd == "resolve":
        if _is_sentinel(args.answer) or _is_sentinel(args.by):
            print("REJECTED (file unchanged): resolve requires --answer AND --by, "
                  "both real values (sentinels are not answers).", file=sys.stderr)
            return 1
        for x in d["decisions"]:
            if x["id"] == args.id:
                x["state"] = "RESOLVED"; x["answer"] = args.answer; x["by"] = args.by
                return _commit(d, args.file, f"decision {args.id} RESOLVED by {args.by}")
        print(f"REJECTED (file unchanged): no decision {args.id!r} in {args.file}",
              file=sys.stderr)
        return 1
    if args.cmd == "defer":
        if _is_missing(args.deferred_reason):
            print("REJECTED (file unchanged): defer requires --reason.", file=sys.stderr)
            return 1
        for x in d["decisions"]:
            if x["id"] == args.id:
                x["state"] = "DEFERRED"
                x["deferred_reason"] = args.deferred_reason
                if args.by: x["by"] = args.by
                return _commit(d, args.file, f"decision {args.id} DEFERRED by {args.by or 'UNDECLARED'}")
        print(f"REJECTED (file unchanged): no decision {args.id!r} in {args.file}",
              file=sys.stderr)
        return 1
    if args.cmd == "check":
        v = check(d)
        for x in v: print(f"VIOLATION: {x}")
        print("VALID" if not v else f"{len(v)} violations")
        return 0 if not v else 1
    if args.cmd == "report":
        print(report(d))
        return 0
    return 0


def selftest():
    import os, subprocess, sys, tempfile
    tmp = tempfile.mkdtemp()
    f = os.path.join(tmp, "s.json")
    me = os.path.abspath(__file__)

    def cli(*a):
        return subprocess.run([sys.executable, me, *a, "--file", f],
                              capture_output=True, text=True)

    cli("init", "--title", "t", "--type", "EMPIRICAL",
        "--materials", "abstract only", "--context", "UNDECLARED")
    d = load(f)
    # 1. silent resolution via decide is rejected, file unchanged
    r = cli("decide", "--id", "D1", "--text", "use this?", "--state", "RESOLVED")
    assert r.returncode != 0 and "silent" in r.stderr
    assert not d["decisions"]
    # 2. resolve without answer/by rejected; sentinel answer rejected
    r = cli("resolve", "--id", "D1", "--by", "user")
    assert r.returncode != 0 and "requires --answer" in r.stderr
    r = cli("decide", "--id", "D1", "--text", "use this?", "--state", "UNRESOLVED")
    assert r.returncode == 0
    r = cli("resolve", "--id", "D1", "--by", "user", "--answer", "UNDECLARED")
    assert r.returncode != 0 and "sentinels" in r.stderr
    # 3. resolving a nonexistent id rejected
    r = cli("resolve", "--id", "NOPE", "--by", "user", "--answer", "x")
    assert r.returncode != 0 and "no decision" in r.stderr
    # 4. proper resolve works and stores provenance
    r = cli("resolve", "--id", "D1", "--by", "user", "--answer", "yes, for now")
    assert r.returncode == 0
    d = load(f)
    assert d["decisions"][0]["state"] == "RESOLVED" and d["decisions"][0]["by"] == "user"
    # 5. DECLINED without reason rejected at write time
    r = cli("tool", "--id", "T1", "--card", "03", "--state", "DECLINED")
    assert r.returncode != 0 and "DECLINED without" in r.stderr
    assert not d["tools"]
    # 6. support graded without evidence location rejected; NO_EVIDENCE_LOCATION
    #    + UNDETERMINED accepted and counts as incompleteness
    r = cli("claim", "--id", "C1", "--text", "x", "--evidence", "", "--support", "SUPPORTED")
    assert r.returncode != 0 and "absences, not locations" in r.stderr
    r = cli("claim", "--id", "C1", "--text", "x", "--evidence", "", "--support", "UNDETERMINED")
    assert r.returncode == 0
    d = load(f)
    # 6b. sentinel evidence location does not satisfy graded support
    before = open(f).read()
    r = cli("claim", "--id", "C1b", "--text", "x", "--evidence", "UNDECLARED",
            "--support", "SUPPORTED")
    assert r.returncode != 0 and "absences, not locations" in r.stderr
    assert open(f).read() == before  # rejection left the file byte-identical
    # 6c. claim vocabulary (label/grade) enforced at write time
    r = cli("claim", "--id", "C1c", "--text", "x", "--evidence", "p. 1",
            "--support", "UNTESTED", "--label", "FABRICATED")
    assert r.returncode != 0 and "label" in r.stderr
    r = cli("claim", "--id", "C1d", "--text", "x", "--evidence", "p. 1",
            "--support", "UNTESTED", "--label", "OBSERVED", "--grade", "MEASURED_PRESENT",
            "--falsifiers", "null at power", "--source", "https://example.org")
    assert r.returncode == 0
    # 6d. design command: recorded, rendered, vocabulary-enforced
    r = cli("design", "--check", "confounding", "--state", "CHECKED",
            "--finding", "no adjustment for site", "--source", "https://example.org")
    assert r.returncode == 0
    before = open(f).read()
    r = cli("design", "--check", "preregistration", "--state", "MAYBE")
    assert r.returncode != 0 and "not in vocabulary" in r.stderr
    assert open(f).read() == before  # rejection left the file byte-identical
    rep = report(load(f))
    assert "## Design checks" in rep and "confounding** (CHECKED)" in rep
    assert "[OBSERVED]" in rep                       # claim label rendered
    assert "grade: MEASURED_PRESENT" in rep           # claim grade rendered
    assert "falsifiers: null at power" in rep         # falsifiers rendered
    assert "source: https://example.org" in rep        # source rendered
    # 6e. EMPIRICAL record without design checks counts as INCOMPLETE even when
    #     claims and tools are present and valid
    d = load(f)
    d["design_checks"] = []
    rep = report(d)
    assert check(d) == []
    assert "design checks: NODATA" in rep and "INCOMPLETE" in rep
    # 6f. NOT_CHECKED design check counts as incompleteness
    d["design_checks"] = [{"check": "blinding", "state": "NOT_CHECKED"}]
    assert "design check blinding: NOT_CHECKED" in report(d)
    # 6g. DETECTED decision counts as incompleteness
    d["design_checks"] = [{"check": "confounding", "state": "CHECKED"}]
    d["decisions"].append({"id": "D9", "text": "detected only", "state": "DETECTED"})
    assert "DETECTED (located, nothing more known)" in report(d)
    # 6h. claim range/instrument/resolution render
    d["claims"][0]["range"] = "lab, adults"; d["claims"][0]["instrument"] = "2AFC task"
    d["claims"][0]["resolution"] = "trial-level"
    rep = report(d)
    assert "range: lab, adults" in rep and "instrument: 2AFC task" in rep
    assert "resolution: trial-level" in rep
    # 7. empty typed record: VALID but visibly INCOMPLETE (claims/tools NODATA)
    f2 = os.path.join(tmp, "s2.json")
    cli2 = lambda *a: subprocess.run([sys.executable, me, *a, "--file", f2],
                                     capture_output=True, text=True)
    cli2("init", "--title", "t", "--type", "EMPIRICAL",
         "--materials", "abstract", "--context", "something")
    d_empty = load(f2)
    assert check(d_empty) == []
    rep = report(d_empty)
    assert "claims: NODATA" in rep and "tools: NODATA" in rep and "INCOMPLETE" in rep
    assert "decisions: NODATA" in rep  # context declared, no surfaces recorded
    # 8. BLOCKED always counts as incompleteness, even with explanatory output
    cli("tool", "--id", "T2", "--card", "02", "--state", "BLOCKED",
        "--output", "full text unavailable")
    rep = report(load(f))
    assert "T2: BLOCKED (inputs unavailable; always incompleteness)" in rep
    # 9. invalid vocabulary rejected at write time
    r = cli("claim", "--id", "C2", "--text", "y", "--evidence", "p. 1",
            "--support", "PROBABLY_TRUE")
    assert r.returncode != 0 and "not in vocabulary" in r.stderr
    # 10. report shows INVALID banner for an invalid record
    d = load(f); d["claims"][0]["support"] = "PROBABLY_TRUE"; save(d, f)
    rep = report(d)
    assert "RECORD INVALID" in rep
    d["claims"][0]["support"] = "UNDETERMINED"; save(d, f)  # restore for next steps
    # 11. defer stores by and reason
    cli("decide", "--id", "D2", "--text", "spend resources?", "--state", "UNRESOLVED")
    r = cli("defer", "--id", "D2", "--by", "assessor", "--reason", "waiting on replication")
    assert r.returncode == 0
    d = load(f)
    dd = [x for x in d["decisions"] if x["id"] == "D2"][0]
    assert dd["by"] == "assessor" and dd["deferred_reason"] == "waiting on replication"
    assert "DEFERRED (owned, still open)" in report(d)
    # 12. missing evidence never becomes a negative finding; report keeps it
    d2 = {"schema": SCHEMA, "title": "t", "pub_type": "EMPIRICAL",
          "citation": "x", "materials": "abstract only", "decision_context": "UNDECLARED",
          "claims": [{"id": "C1", "text": "x", "evidence_location": "",
                      "support": "UNDETERMINED"}],
          "tools": [], "decisions": [], "notes": "UNDECLARED"}
    assert check(d2) == []
    r2 = report(d2)
    assert "INCOMPLETE" in r2 and "evidence location missing" in r2
    assert "UNSUPPORTED" not in r2.split("## Claims")[1]
    # 13. COMMENTARY routes quantitative cards out by default (legal output)
    d3 = dict(d2); d3["pub_type"] = "COMMENTARY"
    assert "cards routed by DEFAULT" in report(d3)
    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
