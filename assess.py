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
  - Lab evidence is linked, never promoted. `labref` binds a Scope Audit Lab
    integrity report (by SHA-256) to claims; it never touches claim support or
    decisions. A clean lab report establishes bundle integrity only. A changed
    report file is a violation; a missing one is incompleteness.
  - Averages used as inputs declare their freezing (Card 02). Each input average
    states population, window and stationarity (sentinel UNDECLARED allowed and
    kept). With none of the three stated it is FROZEN: a claim resting on it
    cannot carry a MEASURED_* grade. ASSESSED stationarity needs a basis and a
    stated population and window. Frozen, partial, split, fitted and transferred
    averages are incompleteness, printed first.

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
    "lab_refs": [ {id, report_path (relative to the record file), report_sha256,
                   procedure, status: one of LAB_REPORT_STATUSES, finding_counts,
                   inputs: [{name, sha256?}], claims: [claim ids]} ],   # optional
    "averages": [ {id, text, value?, population, window,             # optional
                   stationarity: one of STATIONARITY_STATES | UNDECLARED,
                   stationarity_basis?, claims: [claim ids], split_of?,
                   fitted_to?, estimated_from?, source?} ],
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
  labref --file s.json --id L1 --lab-report integrity-report.json --claim C1 [--claim C2]
                                # link a lab integrity report; never changes support
  average --file s.json --id A1 --text "..." --population "..." --window "..."
        --stationarity ASSESSED|ASSUMED|UNASSESSED|UNDECLARED --claim C1 [--claim C2]
        [--value ...] [--basis ...] [--split-of A0] [--fitted-to ...]
        [--estimated-from ...] [--source <url>]
                                # an average used as a model input (Card 02 frozen-state check)
  check  --file s.json         # validate; exit 1 on violations; file never changed
  report --file s.json          # markdown report; INVALID banner if violations
  selftest
"""
import argparse, hashlib, json, os, sys

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

# Scope Audit Lab offline integrity checker (experimental/scope_audit_lab/
# integrity_checker.py). These are the checker's own summary statuses, copied
# verbatim. Neither one is a claim-support grade: NO_GAPS_DETECTED means the
# supplied evidence bundle's references, version bindings, and condition
# coverage showed no gaps; it says nothing about whether a claim is true.
LAB_REPORT_KIND = "OFFLINE_EVIDENCE_INTEGRITY"
LAB_PROCEDURE = "scope_audit_lab.integrity_checker"
LAB_REPORT_STATUSES = frozenset([
    "NO_GAPS_DETECTED_WITHIN_CHECKED_SCOPE",
    "INTEGRITY_GAPS_RECORDED",
])
# Card 02 frozen-state check: is the population an input average was taken
# from assumed not to change within and beyond its window?
STATIONARITY_STATES = frozenset([
    "ASSESSED",     # checked; basis recorded
    "ASSUMED",      # taken as stationary without a check
    "UNASSESSED",   # not considered
])
MEASURED_GRADES = frozenset(["MEASURED_PRESENT", "MEASURED_ABSENT", "MEASURED_DISCARDED"])

LAB_SCOPE_NOTE = ("bundle integrity only: references, version bindings, condition "
                  "coverage; not mathematical, empirical, or claim support")


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


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def read_lab_report(path):
    """Read a lab integrity report (local JSON only; nothing is fetched or run).
    Return the fields a lab_ref stores. Raise ValueError if it is not one."""
    try:
        with open(path) as f:
            r = json.load(f)
    except (OSError, ValueError) as e:
        raise ValueError(f"cannot read lab report {path!r}: {e}")
    if not isinstance(r, dict) or r.get("report_kind") != LAB_REPORT_KIND:
        raise ValueError(f"{path!r} is not a lab integrity report "
                         f"(report_kind must be {LAB_REPORT_KIND})")
    proc = r.get("procedure") or {}
    if proc.get("identity") != LAB_PROCEDURE:
        raise ValueError(f"{path!r}: procedure identity {proc.get('identity')!r} "
                         f"is not {LAB_PROCEDURE}")
    summary = r.get("summary") or {}
    if summary.get("status") not in LAB_REPORT_STATUSES:
        raise ValueError(f"{path!r}: summary status {summary.get('status')!r} not in vocabulary")
    return {
        "procedure": f"{LAB_PROCEDURE} {proc.get('version', 'UNDECLARED')}",
        "status": summary["status"],
        "finding_counts": dict(summary.get("finding_counts") or {}),
        "inputs": [{k: i[k] for k in ("name", "sha256") if k in i}
                   for i in r.get("inputs", []) if isinstance(i, dict)],
    }


def lab_report_state(ref, base_dir):
    """VERIFIED | REPORT_NOT_FOUND | HASH_MISMATCH | NOT_CHECKED (no base_dir)."""
    if base_dir is None:
        return "NOT_CHECKED"
    path = os.path.join(base_dir, ref.get("report_path", ""))
    if _is_missing(ref.get("report_path")) or not os.path.isfile(path):
        return "REPORT_NOT_FOUND"
    return "VERIFIED" if _sha256_file(path) == ref.get("report_sha256") else "HASH_MISMATCH"


def average_state(a):
    """DECLARED | PARTIAL | FROZEN, derived from the three declarations (never set by hand).
    DECLARED: population and window stated and stationarity ASSESSED.
    FROZEN: none of population, window, stationarity stated."""
    pop, win = not _is_sentinel(a.get("population")), not _is_sentinel(a.get("window"))
    st = a.get("stationarity")
    if pop and win and st == "ASSESSED":
        return "DECLARED"
    if not pop and not win and _is_sentinel(st):
        return "FROZEN"
    return "PARTIAL"


def _average_gaps(a):
    gaps = [f for f in ("population", "window") if _is_sentinel(a.get(f))]
    st = a.get("stationarity")
    if _is_sentinel(st):
        gaps.append("stationarity")
    elif st != "ASSESSED":
        gaps.append(f"stationarity {st}")
    return gaps


def check(d, base_dir=None):
    """Return list of violation strings. Empty list = valid record.
    base_dir (the record file's folder) enables lab-report hash verification."""
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
    claim_ids = {c.get("id") for c in d["claims"]}
    seen = set()
    for ref in d.get("lab_refs", []):
        lid = ref.get("id", "?")
        if lid in seen:
            v.append(f"lab ref {lid}: duplicate id")
        seen.add(lid)
        if ref.get("status") not in LAB_REPORT_STATUSES:
            v.append(f"lab ref {lid}: status {ref.get('status')!r} not in vocabulary")
        sha = ref.get("report_sha256") or ""
        if len(sha) != 64 or any(ch not in "0123456789abcdef" for ch in sha):
            v.append(f"lab ref {lid}: report_sha256 missing or malformed "
                     f"(a lab ref binds one exact report)")
        for cid in ref.get("claims", []):
            if cid not in claim_ids:
                v.append(f"lab ref {lid}: linked claim {cid!r} not in record")
        if lab_report_state(ref, base_dir) == "HASH_MISMATCH":
            v.append(f"lab ref {lid}: {ref.get('report_path')} no longer matches its recorded "
                     f"SHA-256 (the bound report changed; link the new report as a new lab ref)")
    avg_ids = [a.get("id") for a in d.get("averages", [])]
    seen = set()
    for a in d.get("averages", []):
        aid = a.get("id", "?")
        if _is_missing(a.get("id")):
            v.append("average ?: id missing")
        if aid in seen:
            v.append(f"average {aid}: duplicate id")
        seen.add(aid)
        if _is_missing(a.get("text")):
            v.append(f"average {aid}: text missing (say what is averaged)")
        for fld in ("population", "window"):
            if _is_missing(a.get(fld)):
                v.append(f"average {aid}: {fld} missing; state it or record UNDECLARED "
                         f"(an absent field is not a declared absence)")
        st = a.get("stationarity")
        if _is_missing(st):
            v.append(f"average {aid}: stationarity missing; record ASSESSED, ASSUMED, "
                     f"UNASSESSED or UNDECLARED")
        elif st not in (STATIONARITY_STATES | {"UNDECLARED"}):
            v.append(f"average {aid}: stationarity {st!r} not in vocabulary")
        if st == "ASSESSED":
            if _is_sentinel(a.get("stationarity_basis")):
                v.append(f"average {aid}: stationarity ASSESSED without a basis")
            if _is_sentinel(a.get("population")) or _is_sentinel(a.get("window")):
                v.append(f"average {aid}: stationarity ASSESSED but population or window "
                         f"unstated (stationarity of what, over when?)")
        links = a.get("claims") or []
        if not links:
            v.append(f"average {aid}: linked to no claim (record averages that enter a claim)")
        for cid in links:
            if cid not in claim_ids:
                v.append(f"average {aid}: linked claim {cid!r} not in record")
        so = a.get("split_of")
        if so is not None and (so == aid or so not in avg_ids):
            v.append(f"average {aid}: split_of {so!r} is not another average in the record")
        if average_state(a) == "FROZEN":
            for c in d["claims"]:
                if c.get("id") in links and c.get("grade") in MEASURED_GRADES:
                    v.append(f"claim {c.get('id')}: grade {c.get('grade')} rests on frozen "
                             f"average {aid} (population, window, stationarity unstated); "
                             f"grade it IMPOSED or UNDECLARED")
    return v


def incompleteness(d, base_dir=None):
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
    for ref in d.get("lab_refs", []):
        lid = ref.get("id")
        if ref.get("status") == "INTEGRITY_GAPS_RECORDED":
            counts = ref.get("finding_counts") or {}
            detail = ", ".join(f"{k} {counts[k]}" for k in ("ERROR", "UNKNOWN") if k in counts)
            out.append(f"lab ref {lid}: integrity gaps recorded in the linked evidence bundle"
                       + (f" ({detail})" if detail else ""))
        if not ref.get("claims"):
            out.append(f"lab ref {lid}: linked to no claim")
        if lab_report_state(ref, base_dir) == "REPORT_NOT_FOUND":
            out.append(f"lab ref {lid}: report file not found at {ref.get('report_path')} "
                       f"(hash binding cannot be re-verified)")
    for a in d.get("averages", []):
        aid, state = a.get("id"), average_state(a)
        if state == "FROZEN":
            out.append(f"average {aid}: FROZEN (population, window, stationarity unstated) "
                       f"-> IMPOSED; claims resting on it: {', '.join(a.get('claims') or [])}")
        elif state == "PARTIAL":
            out.append(f"average {aid}: frozen in part (unstated or unchecked: "
                       f"{', '.join(_average_gaps(a))})")
        if a.get("split_of"):
            out.append(f"average {aid}: split from {a['split_of']} (the distribution "
                       f"reappearing; adds a free value)")
        if not _is_missing(a.get("fitted_to")):
            out.append(f"average {aid}: fitted to {a['fitted_to']}; reproducing that target "
                       f"carries no information about mechanism")
        ef = a.get("estimated_from")
        if not _is_missing(ef) and ef != a.get("population"):
            out.append(f"average {aid}: estimated from {ef}, used for {a.get('population')} "
                       f"(carried across populations; INCOMMENSURABLE(range) unless a bridge "
                       f"is stated)")
    return out


def report(d, base_dir=None):
    lines = [f"# Assessment: {d['title']}",
             f"schema {SCHEMA} — generated by study-aperture; this report is a record, not a verdict.",
             ""]
    v = check(d, base_dir)
    if v:
        lines.append("## RECORD INVALID — the violations below are not findings; fix them")
        lines += [f"- {x}" for x in v]
        lines.append("")
    lines += [f"- citation: {d['citation']}",
              f"- publication type: {d['pub_type']}",
              f"- materials actually held: {d['materials']}",
              f"- decision context: {d['decision_context']}",
              ""]
    inc = incompleteness(d, base_dir)
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
        linked = [r.get("id") for r in d.get("lab_refs", []) if c.get("id") in r.get("claims", [])]
        if linked:
            lines.append(f"  - lab refs: {', '.join(linked)} (bundle integrity only; "
                         f"support above is the assessor's grade, unchanged by the link)")
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
    if d.get("lab_refs"):  # optional section; absent records render as before
        lines.append(f"## Lab evidence references ({LAB_SCOPE_NOTE})")
        for ref in d["lab_refs"]:
            state = lab_report_state(ref, base_dir)
            lines.append(f"- **{ref.get('id')}** {ref.get('status')} — {ref.get('procedure')}")
            lines.append(f"  - report: {ref.get('report_path')} "
                         f"(sha256 {str(ref.get('report_sha256'))[:12]}…, {state})")
            counts = ref.get("finding_counts") or {}
            if counts:
                lines.append("  - findings: " + ", ".join(f"{k} {n}" for k, n in counts.items()))
            for i in ref.get("inputs", []):
                sha = f" (sha256 {i['sha256'][:12]}…)" if i.get("sha256") else ""
                lines.append(f"  - input: {i.get('name')}{sha}")
            lines.append(f"  - linked claims: {', '.join(ref.get('claims', [])) or 'none'}")
        lines.append("")
    if d.get("averages"):  # optional section; absent records render as before
        lines.append("## Input averages (Card 02 frozen-state check)")
        for a in d["averages"]:
            val = f" = {a['value']}" if not _is_missing(a.get("value")) else ""
            lines.append(f"- **{a.get('id')}** ({average_state(a)}) — {a.get('text')}{val}")
            lines.append(f"  - population: {a.get('population')}")
            lines.append(f"  - window: {a.get('window')}")
            basis = (f" (basis: {a['stationarity_basis']})"
                     if not _is_missing(a.get("stationarity_basis")) else "")
            lines.append(f"  - stationarity: {a.get('stationarity')}{basis}")
            for k, label in (("estimated_from", "estimated from"), ("split_of", "split of"),
                             ("fitted_to", "fitted to"), ("source", "source")):
                if not _is_missing(a.get(k)):
                    lines.append(f"  - {label}: {a[k]}")
            lines.append(f"  - claims resting on it: {', '.join(a.get('claims') or [])}")
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


def _base_dir(record_path):
    return os.path.dirname(os.path.abspath(record_path))


def _commit(d, path, ok_msg):
    """Save only if the mutated record validates. Exit nonzero, no write, if not."""
    v = check(d, _base_dir(path))
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
                                   "labref", "average", "check", "report", "selftest"])
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
    p.add_argument("--lab-report"); p.add_argument("--claim", dest="link_claims", action="append")
    p.add_argument("--value"); p.add_argument("--population"); p.add_argument("--window")
    p.add_argument("--stationarity"); p.add_argument("--basis")
    p.add_argument("--split-of"); p.add_argument("--fitted-to"); p.add_argument("--estimated-from")
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
    if args.cmd == "labref":
        if _is_missing(args.id) or _is_missing(args.lab_report):
            print("REJECTED (file unchanged): labref requires --id and --lab-report.",
                  file=sys.stderr)
            return 1
        if any(r.get("id") == args.id for r in d.get("lab_refs", [])):
            print(f"REJECTED (file unchanged): lab ref {args.id!r} already exists; a lab ref "
                  f"binds one report and is not overwritten. Use a new id.", file=sys.stderr)
            return 1
        try:
            fields = read_lab_report(args.lab_report)
        except ValueError as e:
            print(f"REJECTED (file unchanged): {e}", file=sys.stderr)
            return 1
        ref = {"id": args.id,
               "report_path": os.path.relpath(os.path.abspath(args.lab_report),
                                              _base_dir(args.file)),
               "report_sha256": _sha256_file(args.lab_report),
               **fields,
               "claims": list(dict.fromkeys(args.link_claims or []))}
        d.setdefault("lab_refs", []).append(ref)
        # Only lab_refs is touched: claim support and decisions are never changed here.
        return _commit(d, args.file, f"lab ref {args.id} recorded ({ref['status']}; "
                                     f"{LAB_SCOPE_NOTE})")
    if args.cmd == "average":
        if any(a.get("id") == args.id for a in d.get("averages", [])):
            print(f"REJECTED (file unchanged): average {args.id!r} already exists; use a new id.",
                  file=sys.stderr)
            return 1
        a = {"id": args.id, "text": args.text, "population": args.population,
             "window": args.window, "stationarity": args.stationarity,
             "claims": list(dict.fromkeys(args.link_claims or []))}
        for opt, key in (("value", "value"), ("basis", "stationarity_basis"),
                         ("split_of", "split_of"), ("fitted_to", "fitted_to"),
                         ("estimated_from", "estimated_from"), ("source", "source")):
            if getattr(args, opt):
                a[key] = getattr(args, opt)
        d.setdefault("averages", []).append(a)
        return _commit(d, args.file, f"average {args.id} recorded ({average_state(a)})")
    if args.cmd == "check":
        v = check(d, _base_dir(args.file))
        for x in v: print(f"VIOLATION: {x}")
        print("VALID" if not v else f"{len(v)} violations")
        return 0 if not v else 1
    if args.cmd == "report":
        print(report(d, _base_dir(args.file)))
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
    # 14. lab refs: linked, hash-bound, never promoted
    assert "## Lab evidence references" not in report(d3)  # optional section absent
    def lab_json(name, status, counts):
        path = os.path.join(tmp, name)
        with open(path, "w") as fh:
            json.dump({"report_kind": LAB_REPORT_KIND,
                       "procedure": {"identity": LAB_PROCEDURE, "version": "0.2.0"},
                       "inputs": [{"name": "bundle.json", "sha256": "ab" * 32}],
                       "summary": {"status": status, "finding_counts": counts}}, fh)
        return path
    clean = lab_json("clean.json", "NO_GAPS_DETECTED_WITHIN_CHECKED_SCOPE",
                     {"ERROR": 0, "UNKNOWN": 0, "INFO": 1})
    gaps = lab_json("gaps.json", "INTEGRITY_GAPS_RECORDED", {"ERROR": 1, "UNKNOWN": 3, "INFO": 0})
    not_lab = os.path.join(tmp, "other.json")
    with open(not_lab, "w") as fh:
        json.dump({"status": "PASS"}, fh)
    before = open(f).read()
    # 14a. a non-lab JSON is refused; file unchanged
    r = cli("labref", "--id", "L1", "--lab-report", not_lab, "--claim", "C1")
    assert r.returncode != 0 and "not a lab integrity report" in r.stderr
    # 14b. link to a claim that does not exist is refused
    r = cli("labref", "--id", "L1", "--lab-report", clean, "--claim", "NOPE")
    assert r.returncode != 0 and "not in record" in r.stderr
    assert open(f).read() == before
    # 14c. a clean lab report never changes claim support or decisions
    claims_before = json.dumps(load(f)["claims"]); decisions_before = json.dumps(load(f)["decisions"])
    r = cli("labref", "--id", "L1", "--lab-report", clean, "--claim", "C1")
    assert r.returncode == 0, r.stderr
    d = load(f)
    assert json.dumps(d["claims"]) == claims_before
    assert json.dumps(d["decisions"]) == decisions_before
    assert d["claims"][0]["support"] == "UNDETERMINED"
    ref = d["lab_refs"][0]
    assert ref["report_path"] == "clean.json" and len(ref["report_sha256"]) == 64
    # 14d. rendered with its scope and verification state
    rep = report(d, tmp)
    assert "## Lab evidence references (bundle integrity only" in rep
    assert "VERIFIED" in rep and "lab refs: L1" in rep
    # 14e. a lab ref id is never overwritten
    r = cli("labref", "--id", "L1", "--lab-report", gaps, "--claim", "C1")
    assert r.returncode != 0 and "already exists" in r.stderr
    # 14f. gaps in the bundle are incompleteness
    r = cli("labref", "--id", "L2", "--lab-report", gaps, "--claim", "C1")
    assert r.returncode == 0
    assert "L2: integrity gaps recorded in the linked evidence bundle (ERROR 1, UNKNOWN 3)" \
        in report(load(f), tmp)
    # 14g. a missing report file is incompleteness, not a violation
    os.remove(gaps)
    assert check(load(f), tmp) == []
    assert "L2: report file not found" in report(load(f), tmp)
    # 14h. a changed report file is a violation (the binding broke)
    with open(clean, "a") as fh:
        fh.write(" ")
    r = cli("check")
    assert r.returncode != 0 and "no longer matches its recorded SHA-256" in r.stdout
    # 14i. a forged status in the record is a violation
    d = load(f); d["lab_refs"][0]["status"] = "SUPPORTED"
    assert any("not in vocabulary" in x for x in check(d))
    # 15. input averages: the freezing is declared, never silently assumed
    f3 = os.path.join(tmp, "s3.json")
    cli3 = lambda *a: subprocess.run([sys.executable, me, *a, "--file", f3],
                                     capture_output=True, text=True)
    cli3("init", "--title", "t", "--type", "THEORETICAL", "--materials", "full text",
         "--context", "UNDECLARED")
    assert cli3("claim", "--id", "C1", "--text", "x", "--evidence", "p. 2",
                "--support", "UNTESTED", "--grade", "MEASURED_PRESENT").returncode == 0
    assert cli3("claim", "--id", "C2", "--text", "y", "--evidence", "p. 3",
                "--support", "UNTESTED", "--grade", "IMPOSED").returncode == 0
    assert "## Input averages" not in report(load(f3))  # optional section absent
    before = open(f3).read()
    # 15a. missing population/window/stationarity rejected
    r = cli3("average", "--id", "A1", "--text", "prevalence", "--claim", "C2")
    assert r.returncode != 0 and "population missing" in r.stderr
    assert "stationarity missing" in r.stderr
    # 15b. bad stationarity value rejected
    r = cli3("average", "--id", "A1", "--text", "p", "--population", "UNDECLARED",
             "--window", "UNDECLARED", "--stationarity", "STABLE", "--claim", "C2")
    assert r.returncode != 0 and "not in vocabulary" in r.stderr
    # 15c. ASSESSED needs a basis and a stated population and window
    r = cli3("average", "--id", "A1", "--text", "p", "--population", "UNDECLARED",
             "--window", "2010", "--stationarity", "ASSESSED", "--claim", "C2")
    assert r.returncode != 0 and "without a basis" in r.stderr
    assert "stationarity of what" in r.stderr
    # 15d. unknown linked claim, and no linked claim, rejected
    r = cli3("average", "--id", "A1", "--text", "p", "--population", "UNDECLARED",
             "--window", "UNDECLARED", "--stationarity", "UNDECLARED", "--claim", "NOPE")
    assert r.returncode != 0 and "not in record" in r.stderr
    r = cli3("average", "--id", "A1", "--text", "p", "--population", "UNDECLARED",
             "--window", "UNDECLARED", "--stationarity", "UNDECLARED")
    assert r.returncode != 0 and "linked to no claim" in r.stderr
    # 15e. a frozen average under a MEASURED_* claim grade is rejected
    r = cli3("average", "--id", "A1", "--text", "p", "--population", "UNDECLARED",
             "--window", "UNDECLARED", "--stationarity", "UNDECLARED", "--claim", "C1")
    assert r.returncode != 0 and "rests on frozen average" in r.stderr
    assert open(f3).read() == before  # every rejection left the file byte-identical
    # 15f. a frozen average under an IMPOSED claim is valid and is incompleteness
    r = cli3("average", "--id", "A1", "--text", "prevalence", "--value", "0.25",
             "--population", "UNDECLARED", "--window", "UNDECLARED",
             "--stationarity", "UNDECLARED", "--claim", "C2", "--fitted-to", "rate X")
    assert r.returncode == 0 and "FROZEN" in r.stdout, r.stderr
    rep3 = report(load(f3))
    assert "average A1: FROZEN" in rep3 and "-> IMPOSED" in rep3
    assert "fitted to rate X" in rep3 and "INCOMPLETE" in rep3
    assert "**A1** (FROZEN) — prevalence = 0.25" in rep3
    # 15g. partial, split and transferred averages are incompleteness; split_of must exist
    r = cli3("average", "--id", "A2", "--text", "p2", "--population", "subset B",
             "--window", "UNDECLARED", "--stationarity", "ASSUMED", "--claim", "C2",
             "--split-of", "A9")
    assert r.returncode != 0 and "split_of" in r.stderr
    r = cli3("average", "--id", "A2", "--text", "p2", "--population", "subset B",
             "--window", "UNDECLARED", "--stationarity", "ASSUMED", "--claim", "C2",
             "--split-of", "A1", "--estimated-from", "set Z")
    assert r.returncode == 0, r.stderr
    rep3 = report(load(f3))
    assert "A2: frozen in part (unstated or unchecked: window, stationarity ASSUMED)" in rep3
    assert "A2: split from A1" in rep3
    assert "A2: estimated from set Z, used for subset B (carried across populations" in rep3
    # 15h. a fully declared average is DECLARED and adds no incompleteness of its own
    r = cli3("average", "--id", "A3", "--text", "mean", "--population", "cohort 1",
             "--window", "2001-2005", "--stationarity", "ASSESSED",
             "--basis", "flat trend, Table 2", "--claim", "C1")
    assert r.returncode == 0 and "DECLARED" in r.stdout, r.stderr
    rep3 = report(load(f3))
    assert "average A3" not in rep3.split("## Incompleteness")[1].split("\n## ")[0]
    # 15i. an average id is never overwritten; a forged state in the file is caught
    r = cli3("average", "--id", "A3", "--text", "m", "--population", "x", "--window", "y",
             "--stationarity", "ASSUMED", "--claim", "C1")
    assert r.returncode != 0 and "already exists" in r.stderr
    d = load(f3); d["averages"][0]["stationarity"] = "PROBABLY"
    assert any("not in vocabulary" in x for x in check(d))
    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
