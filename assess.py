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
  - A miss can be classified before it is repaired (Card 06 section 4): a RUN tool
    or a CHECKED design check may carry error types from the glyph procedure
    (E1 dropped variable, E2 stale conditions, E3 defaulted slot, E4 unchecked
    observer). A tag needs the miss stated in the output or finding; a tag on a
    tool that did not run, or a check that was not done, is rejected.
  - Averages used as inputs declare their freezing (Card 02). Each input average
    states population, window and stationarity (sentinel UNDECLARED allowed and
    kept). With none of the three stated it is FROZEN: a claim resting on it
    cannot carry a MEASURED_* grade. ASSESSED stationarity needs a basis and a
    stated population and window. Frozen, partial, split, fitted and transferred
    averages are incompleteness, printed first.
  - Every source carries a read depth (Card 07). A record lists its sources once,
    each with depth SNIPPET, PRESS_RELEASE, ABSTRACT, FULL_TEXT (sections named),
    CARRIED (from what named) or UNDECLARED. Every `source` string elsewhere in
    the record must be one of them. A graded claim (support SUPPORTED,
    PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, or a MEASURED_* grade) must
    name the sources and depths it rests on. UNDECLARED depth is allowed, but a
    graded claim resting on it is FLAGGED: the record is valid, not clean.
  - The read-depth ceiling (CEILING table, Card 07 section 4): SNIPPET and
    PRESS_RELEASE carry no SUPPORTED and no MEASURED_*; ABSTRACT no MEASURED_*
    unless the value is quoted from the abstract; CARRIED nothing above UNTESTED.
    A claim above the ceiling of every source it rests on is FLAGGED. A reviewer
    may override one only with a logged reason and a named author.
  - Old records are migrated, never silently. A study-aperture/1 file is read
    through an in-memory migration (all depths UNDECLARED) and is not written;
    commands that change a record refuse it until `migrate` has run. `migrate`
    takes a depth only from a declaration whose basis quote is verbatim in the
    record's own text, and logs every change in the record.

Schema (study-aperture/2):

  record = {
    "title": str,
    "pub_type": one of PUB_TYPES,
    "citation": str,            # where the study itself lives
    "materials": str,           # what you actually had access to (be honest here)
    "decision_context": str,    # what the assessment is FOR; may be UNDECLARED
    "sources": [ {id, location, depth: one of READ_DEPTHS,
                  detail?,             # required: FULL_TEXT sections, CARRIED from
                  basis?} ],           # where the depth statement comes from
    "claims": [ {id, text, evidence_location | NO_EVIDENCE_LOCATION,
                 support: one of SUPPORT,
                 rests_on: [ {source: source id, depth: that source's depth} ]} ],
    "tools": [ {id, card, state: one of TOOL_STATES, output?, declined_reason?,
                error_types?: [one of ERROR_TYPES]} ],
    "decisions": [ {id, text, state: one of DECISION_STATES,
                    answer?, by?, deferred_reason?} ],
    "lab_refs": [ {id, report_path (relative to the record file), report_sha256,
                   procedure, status: one of LAB_REPORT_STATUSES, finding_counts,
                   inputs: [{name, sha256?}], claims: [claim ids]} ],   # optional
    "averages": [ {id, text, value?, population, window,             # optional
                   stationarity: one of STATIONARITY_STATES | UNDECLARED,
                   stationarity_basis?, claims: [claim ids], split_of?,
                   fitted_to?, estimated_from?, source?} ],
    "notes": str,
    "migrations": [ {from, to, by, changes: [str]} ]   # written by `migrate` only
  }

Commands:
  init --file s.json --title "..." --type EMPIRICAL [--citation ...] [--materials ...]
  source --file s.json --id S1 --location <url> --depth ABSTRACT [--detail ...] [--basis ...]
                                # FULL_TEXT needs --detail (sections); CARRIED needs --detail (from)
  migrate --file s.json [--depths decl.json]   # study-aperture/1 -> /2; logs every change
  claim --file s.json --id C1 --text "..." --evidence "p. 4, Table 1" [--support ...]
        [--measurand ...] [--grade ...] [--falsifiers ...] [--label OBSERVED|DERIVED|PROPOSED] [--source <url>]
        [--range ...] [--instrument ...] [--resolution ...] [--rests-on S1 ...]
                                # --source adds its source to rests_on
        [--quoted S1=<value as quoted in the abstract>]   # lifts an ABSTRACT grade ceiling
  override --file s.json --id C1 --by <who> --reason "..."   # logged ceiling override
  tool  --file s.json --id T1 --card 03 --state RUN --output "..." [--source <url>]
        [--declined-reason ...] [--error-type E1_DROPPED_VARIABLE ...]
  design --file s.json --check confounding --state CHECKED|NOT_CHECKED|NOT_APPLICABLE
        [--finding "..."] [--source <url>] [--error-type E3_DEFAULTED_SLOT ...]
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
  check  --file s.json [--strict]   # validate; exit 1 on violations; flags print
                                # "VALID — FLAGGED" (exit 0, or 3 with --strict)
  report --file s.json          # markdown report; INVALID banner if violations
  selftest
"""
import argparse, hashlib, json, os, sys

SCHEMA = "study-aperture/2"
LEGACY_SCHEMAS = frozenset(["study-aperture/1"])   # read through migrate(), never written

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
    "EMPIRICAL":   {"00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10"},
    "REVIEW":      {"00", "01", "02", "03", "04", "06", "07", "08", "09", "10"},
    "THEORETICAL": {"00", "01", "04", "06", "07", "10"},
    "SIMULATION":  {"00", "01", "02", "04", "06", "07", "08", "09", "10"},
    "COMMENTARY":  {"00", "01", "06", "07", "10"},
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

# Card 07: how deeply a source was read. One depth per source, not per record.
READ_DEPTHS = frozenset([
    "SNIPPET",        # a search-result fragment or index entry; not the document
    "PRESS_RELEASE",  # coverage or a release about the work, not the work
    "ABSTRACT",       # the abstract and citation metadata only
    "FULL_TEXT",      # the document itself; detail names the sections read
    "CARRIED",        # not read: taken from another report of it; detail names from what
    "UNDECLARED",     # depth not stated; kept, never read as FULL_TEXT
])
DEPTH_DETAIL = {"FULL_TEXT": "the sections read", "CARRIED": "what it was carried from"}
# A claim is graded when its support or its measurement grade asserts something
# about the evidence. These must name the sources and depths they rest on.
LOCATED_SUPPORT = frozenset(["SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "CONTRADICTED"])

# Card 07 section 4, the mechanical part: the highest grade a read depth can carry.
# A claim exceeds the ceiling when NO source it rests on permits its support (or its
# measurement grade). Exceeding it is a FLAG, not a violation; a reviewer may override
# one with a logged reason and author (`override`). FULL_TEXT and UNDECLARED have no
# row here (UNDECLARED is already flagged on its own).
CEILING = {
    "SNIPPET":       {"support": frozenset(["SUPPORTED"]), "grade": MEASURED_GRADES,
                      "quote_lifts_grade": False},
    "PRESS_RELEASE": {"support": frozenset(["SUPPORTED"]), "grade": MEASURED_GRADES,
                      "quote_lifts_grade": False},
    "ABSTRACT":      {"support": frozenset(), "grade": MEASURED_GRADES,
                      "quote_lifts_grade": True},   # a MEASURED_* value quoted from the abstract
    "CARRIED":       {"support": LOCATED_SUPPORT, "grade": MEASURED_GRADES,
                      "quote_lifts_grade": False},  # nothing above UNTESTED
}


def is_graded(c):
    return c.get("support") in LOCATED_SUPPORT or c.get("grade") in MEASURED_GRADES


def depth_label(src):
    """FULL_TEXT(methods, Table 2) / CARRIED(review X) / ABSTRACT."""
    dep = src.get("depth", "UNDECLARED")
    det = src.get("detail")
    return f"{dep}({det})" if dep in DEPTH_DETAIL and not _is_missing(det) else str(dep)

# Card 06 section 4: classify a miss before repairing it. From the glyph procedure,
# JinnZ2/Simulators tools/glyph_reasoning.md (CC0, delivered 2026-10-25): "the glyph
# holds; the reasoning fails". Each type calls for a different repair.
ERROR_TYPES = frozenset([
    "E1_DROPPED_VARIABLE",     # a variable the environment holds was left out
    "E2_STALE_CONDITIONS",     # values from earlier conditions used after they changed
    "E3_DEFAULTED_SLOT",       # a slot assumed from history or a claim, not tested
    "E4_UNCHECKED_OBSERVER",   # the observer's own state, frame or calibration unchecked
])

LAB_SCOPE_NOTE = ("bundle integrity only: references, version bindings, condition "
                  "coverage; not mathematical, empirical, or claim support")


def load(path):
    with open(path) as f:
        d = json.load(f)
    if d.get("schema") in LEGACY_SCHEMAS:
        legacy = d.get("schema")
        d, _ = migrate(d)
        d["_read_from"] = legacy   # in memory only; save() refuses this record
    elif d.get("schema") != SCHEMA:
        raise SystemExit(f"{path}: wrong or missing schema field (want {SCHEMA})")
    for key in ("title", "pub_type", "citation", "materials", "decision_context"):
        d.setdefault(key, "UNDECLARED")
    d.setdefault("claims", []); d.setdefault("tools", [])
    d.setdefault("decisions", []); d.setdefault("design_checks", [])
    d.setdefault("notes", "UNDECLARED")
    d.setdefault("sources", [])
    return d


class LegacyRecord(Exception):
    pass


def save(d, path):
    if d.get("_read_from"):
        raise LegacyRecord(f"{path} is {d['_read_from']}; run `assess.py migrate --file "
                           f"{path}` first (a legacy record is never rewritten implicitly)")
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


def _check_error_types(v, label, tags, state_ok, state_name, text, text_name):
    if tags is None:
        return
    if not isinstance(tags, list) or not tags:
        v.append(f"{label}: error_types must be a non-empty list when present")
        return
    for e in tags:
        if e not in ERROR_TYPES:
            v.append(f"{label}: error type {e!r} not in vocabulary")
    if len(set(tags)) != len(tags):
        v.append(f"{label}: error type listed twice")
    if not state_ok:
        v.append(f"{label}: error types need {state_name} (a miss is classified only "
                 f"where something was run or checked)")
    if _is_sentinel(text):
        v.append(f"{label}: error types need the miss stated in the {text_name} "
                 f"(classify a stated miss, not an empty field)")


def _record_text(d):
    """All string values in a record, for checking that a basis quote is in it."""
    out = []
    def walk(x):
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(d)
    return "\n".join(out)


def migrate(d, declarations=None):
    """study-aperture/1 -> /2. Return (new record, change log). Pure: d is not changed.

    Sources are created from the record itself, values kept verbatim:
      S0 = the publication (location = citation); every distinct `source` string
      on a claim, tool, design check or average becomes S1, S2, ... in order.
    Depth is UNDECLARED unless `declarations` gives one, keyed by source id or
    location: {"depth": ..., "detail": ..., "basis": "<quote>"}. The basis quote
    must appear verbatim in the record's own text, so a migrated depth is one the
    record already stated. Each claim rests on its own source if it names one,
    else on S0 (its evidence location is inside the publication)."""
    if d.get("schema") not in LEGACY_SCHEMAS:
        raise ValueError(f"migrate expects {sorted(LEGACY_SCHEMAS)}, got {d.get('schema')!r}")
    declarations = declarations or {}
    text = _record_text(d)
    new = json.loads(json.dumps(d))
    log = [f"schema {d.get('schema')} -> {SCHEMA}"]
    locs = [new.get("citation") if not _is_missing(new.get("citation")) else "UNDECLARED"]
    for key in ("claims", "tools", "design_checks", "averages"):
        for item in new.get(key, []):
            s = item.get("source")
            if not _is_sentinel(s) and s not in locs:
                locs.append(s)
    used = set()
    sources = []
    for i, loc in enumerate(locs):
        sid = f"S{i}"
        decl = declarations.get(sid) or declarations.get(loc) or {}
        used.update(k for k in (sid, loc) if k in declarations)
        src = {"id": sid, "location": loc, "depth": decl.get("depth", "UNDECLARED")}
        if decl:
            basis = decl.get("basis")
            if _is_missing(basis) or basis not in text:
                raise ValueError(f"declaration for {sid} ({loc}): basis quote not found "
                                 f"verbatim in the record; a migrated depth must be one "
                                 f"the record already states")
            if not _is_missing(decl.get("detail")):
                src["detail"] = decl["detail"]
            src["basis"] = basis
        role = "the publication (citation)" if i == 0 else "a source string in the record"
        log.append(f"source {sid} added for {role}: {loc} -> depth {depth_label(src)}"
                   + (f" (basis quoted from the record: {src['basis']!r})" if decl else
                      " (no depth stated in the record)"))
        sources.append(src)
    unused = set(declarations) - used
    if unused:
        raise ValueError(f"declarations name no source in the record: {sorted(unused)}")
    by_loc = {s["location"]: s for s in sources}
    for c in new.get("claims", []):
        s = c.get("source")
        src = by_loc.get(s) if not _is_sentinel(s) else sources[0]
        c["rests_on"] = [{"source": src["id"], "depth": src["depth"]}]
        log.append(f"claim {c.get('id')}: rests_on {src['id']} ({src['depth']})"
                   + ("" if not _is_sentinel(s) else " -- no source of its own; the publication"))
    new["sources"] = sources
    new["schema"] = SCHEMA
    new.setdefault("migrations", []).append(
        {"from": d.get("schema"), "to": SCHEMA, "by": "assess.py migrate", "changes": log})
    return new, log


def _check_sources(d, v):
    """Card 07 read-depth rules. Appends violations to v."""
    sources = d.get("sources", [])
    ids, locs = set(), {}
    for s in sources:
        sid = s.get("id", "?")
        if _is_missing(s.get("id")):
            v.append("source ?: id missing")
        if sid in ids:
            v.append(f"source {sid}: duplicate id")
        ids.add(sid)
        if _is_missing(s.get("location")):
            v.append(f"source {sid}: location missing (record UNDECLARED if unknown)")
        elif s["location"] in locs and not _is_sentinel(s["location"]):
            v.append(f"source {sid}: same location as {locs[s['location']]}")
        locs.setdefault(s.get("location"), sid)
        dep = s.get("depth")
        if _is_missing(dep):
            v.append(f"source {sid}: depth missing; record one of READ_DEPTHS or UNDECLARED "
                     f"(an absent field is not a declared absence)")
        elif dep not in READ_DEPTHS:
            v.append(f"source {sid}: depth {dep!r} not in vocabulary")
        elif dep in DEPTH_DETAIL and _is_sentinel(s.get("detail")):
            v.append(f"source {sid}: {dep} needs --detail naming {DEPTH_DETAIL[dep]}")
    for key, label in (("claims", "claim"), ("tools", "tool"),
                       ("design_checks", "design check"), ("averages", "average")):
        for item in d.get(key, []):
            s = item.get("source")
            if not _is_sentinel(s) and s not in locs:
                name = item.get("id", item.get("check", "?"))
                v.append(f"{label} {name}: source {s!r} is not a listed source; list it "
                         f"with its read depth (`source` command)")
    by_id = {s.get("id"): s for s in sources}
    for c in d.get("claims", []):
        cid = c.get("id", "?")
        rests = c.get("rests_on")
        if rests is None:
            rests = []
        if not isinstance(rests, list):
            v.append(f"claim {cid}: rests_on must be a list")
            continue
        for r in rests:
            src = by_id.get(r.get("source")) if isinstance(r, dict) else None
            if src is None:
                v.append(f"claim {cid}: rests on {r!r}, which is not a listed source")
            elif r.get("depth") != src.get("depth"):
                v.append(f"claim {cid}: rests on {src.get('id')} at depth {r.get('depth')!r}, "
                         f"but the source's depth is {src.get('depth')!r}")
        named = {r.get("source") for r in rests if isinstance(r, dict)}
        own = locs.get(c.get("source")) if not _is_sentinel(c.get("source")) else None
        if own and own not in named:
            v.append(f"claim {cid}: names source {c.get('source')!r} ({own}) but does not "
                     f"rest on it")
        for r in rests:
            if isinstance(r, dict) and "quoted" in r:
                src = by_id.get(r.get("source")) or {}
                if src.get("depth") != "ABSTRACT":
                    v.append(f"claim {cid}: a quoted value lifts only an ABSTRACT source; "
                             f"{r.get('source')} is {src.get('depth')}")
                elif _is_sentinel(r.get("quoted")):
                    v.append(f"claim {cid}: quoted value on {r.get('source')} is empty")
        o = c.get("ceiling_override")
        if o is not None and (not isinstance(o, dict) or _is_sentinel(o.get("reason"))
                              or _is_sentinel(o.get("by"))):
            v.append(f"claim {cid}: ceiling_override needs a reason AND a named author "
                     f"(an override is logged, never silent)")
        if is_graded(c) and not rests:
            v.append(f"claim {cid}: graded ({c.get('support')}, grade {c.get('grade')}) "
                     f"without naming the sources and depths it rests on")


def _permits(src, rest, field, value):
    row = CEILING.get(src.get("depth"))
    if row is None or value not in row[field]:
        return True
    return field == "grade" and row["quote_lifts_grade"] and not _is_sentinel(rest.get("quoted"))


def ceiling_breaches(c, by_id):
    """Card 07 ceiling, mechanical part. Return a list of breach strings for one claim."""
    rests = [(r, by_id[r.get("source")]) for r in c.get("rests_on") or []
             if isinstance(r, dict) and r.get("source") in by_id]
    if not rests:
        return []
    out = []
    for field, value in (("support", c.get("support")), ("grade", c.get("grade"))):
        if value is None or all(_permits(src, r, field, value) for r, src in rests):
            continue
        if any(_permits(src, r, field, value) for r, src in rests):
            continue
        where = ", ".join(f"{src.get('id')} {src.get('depth')}" for r, src in rests)
        extra = (" (an ABSTRACT source lifts this only with the value quoted from the abstract)"
                 if field == "grade" and any(src.get("depth") == "ABSTRACT" for _, src in rests)
                 else "")
        out.append(f"{field} {value} exceeds the read-depth ceiling of every source it rests "
                   f"on: {where}{extra}")
    return out


def overrides(d):
    """Ceiling breaches a reviewer overrode, with the logged reason and author."""
    by_id = {s.get("id"): s for s in d.get("sources", [])}
    out = []
    for c in d.get("claims", []):
        o = c.get("ceiling_override")
        if isinstance(o, dict):
            for b in ceiling_breaches(c, by_id) or ["(nothing exceeds the ceiling now)"]:
                out.append(f"claim {c.get('id')}: {b} -- overridden by {o.get('by')}: {o.get('reason')}")
    return out


def flags(d):
    """Valid, but not clean: graded claims resting on an UNDECLARED read depth, and
    claims above the read-depth ceiling of every source they rest on (unless overridden)."""
    by_id = {s.get("id"): s for s in d.get("sources", [])}
    out = []
    for c in d.get("claims", []):
        if not is_graded(c):
            continue
        undeclared = [r.get("source") for r in c.get("rests_on") or []
                      if isinstance(r, dict) and by_id.get(r.get("source"), {}).get("depth")
                      == "UNDECLARED"]
        if undeclared:
            out.append(f"claim {c.get('id')}: graded {c.get('support')}"
                       + (f" / {c.get('grade')}" if c.get("grade") else "")
                       + f" resting on UNDECLARED read depth: {', '.join(undeclared)}")
        if not isinstance(c.get("ceiling_override"), dict):
            out += [f"claim {c.get('id')}: {b}" for b in ceiling_breaches(c, by_id)]
    for c in d.get("claims", []):
        if isinstance(c.get("ceiling_override"), dict) and not ceiling_breaches(c, by_id):
            out.append(f"claim {c.get('id')}: ceiling override recorded, but nothing exceeds "
                       f"the ceiling now (stale override; remove it)")
    return out


def check(d, base_dir=None):
    """Return list of violation strings. Empty list = valid record.
    base_dir (the record file's folder) enables lab-report hash verification."""
    v = []
    if d["pub_type"] not in PUB_TYPES:
        v.append(f"pub_type {d['pub_type']!r} not in vocabulary")
    _check_sources(d, v)
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
        _check_error_types(v, f"tool {tid}", t.get("error_types"),
                           t.get("state") == "RUN", "state RUN",
                           t.get("output"), "output")
    for k in d.get("design_checks", []):
        if k.get("state") not in DESIGN_CHECK_STATES:
            v.append(f"design check {k.get('check', '?')}: state {k.get('state')!r} not in vocabulary")
        _check_error_types(v, f"design check {k.get('check', '?')}", k.get("error_types"),
                           k.get("state") == "CHECKED", "state CHECKED",
                           k.get("finding"), "finding")
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
    if d.get("_read_from"):
        lines += [f"**Read from {d['_read_from']} through an in-memory migration; the file is "
                  f"unchanged and every source depth is UNDECLARED. Run `assess.py migrate`.**", ""]
    v = check(d, base_dir)
    if v:
        lines.append("## RECORD INVALID — the violations below are not findings; fix them")
        lines += [f"- {x}" for x in v]
        lines.append("")
    fl = flags(d)
    if fl:
        lines.append("## FLAGGED — valid, not clean: read depth undeclared or below the "
                     "grade (Card 07)")
        lines += [f"- {x}" for x in fl]
        lines.append("")
    ov = overrides(d)
    if ov:
        lines.append("## Read-depth ceiling overrides (logged; Card 07)")
        lines += [f"- {x}" for x in ov]
        lines.append("")
    lines += [f"- citation: {d['citation']}",
              f"- publication type: {d['pub_type']}",
              f"- materials actually held: {d['materials']}",
              f"- decision context: {d['decision_context']}",
              ""]
    lines.append("## Sources and read depth (Card 07)")
    if not d.get("sources"):
        lines.append("- NODATA (no sources listed)")
    for src in d.get("sources", []):
        lines.append(f"- **{src.get('id')}** {depth_label(src)} — {src.get('location')}")
        if not _is_missing(src.get("basis")):
            lines.append(f"  - depth basis: {src.get('basis')}")
    lines.append("")
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
        if k.get("error_types"):
            lines.append(f"  - error types: {', '.join(k['error_types'])}")
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
        if c.get("rests_on"):
            lines.append("  - rests on: " + ", ".join(
                f"{r.get('source')} ({r.get('depth')}"
                + (f", quoted: {r['quoted']}" if not _is_missing(r.get("quoted")) else "") + ")"
                for r in c["rests_on"]))
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
        if t.get("error_types"):
            lines.append(f"  - error types: {', '.join(t['error_types'])}")
    lines.append("")
    tagged = [(t.get("id"), e) for t in d["tools"] for e in t.get("error_types") or []]
    tagged += [(f"design:{k.get('check')}", e) for k in d.get("design_checks", [])
               for e in k.get("error_types") or []]
    if tagged:  # optional section; absent records render as before
        lines.append("## Misses classified (glyph E1-E4; Card 06 section 4)")
        lines.append("- classification of stated misses, not a score; untagged entries are unclassified, not clean")
        for e in sorted(ERROR_TYPES):
            ids = [i for i, x in tagged if x == e]
            if ids:
                lines.append(f"- {e}: {', '.join(ids)}")
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
    for m in d.get("migrations", []):  # optional section; absent records render as before
        lines.append("")
        lines.append(f"## Migration log: {m.get('from')} -> {m.get('to')} ({m.get('by')})")
        lines += [f"- {x}" for x in m.get("changes", [])]
    return "\n".join(lines)


def _base_dir(record_path):
    return os.path.dirname(os.path.abspath(record_path))


def _commit(d, path, ok_msg):
    """Save only if the mutated record validates. Exit nonzero, no write, if not."""
    if d.get("_read_from"):
        print(f"REJECTED (file unchanged): {path} is {d['_read_from']}; run `assess.py migrate "
              f"--file {path}` first", file=sys.stderr)
        return 1
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
                                   "labref", "average", "source", "override", "migrate", "check", "report",
                                   "selftest"])
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
    p.add_argument("--error-type", dest="error_types", action="append")
    p.add_argument("--location"); p.add_argument("--depth"); p.add_argument("--detail")
    p.add_argument("--rests-on", dest="rests_on", action="append")
    p.add_argument("--quoted", action="append",
                   help="claim: S1=<value as quoted in the abstract>; lifts an ABSTRACT ceiling")
    p.add_argument("--depths", help="migrate: JSON of depth declarations with verbatim basis quotes")
    p.add_argument("--strict", action="store_true", help="check: exit 3 when FLAGGED")
    args = p.parse_args(argv)

    if args.cmd == "selftest":
        return selftest()
    if args.cmd == "init":
        d = {"schema": SCHEMA, "title": args.title or "UNDECLARED",
             "pub_type": args.pub_type or "UNDECLARED",
             "citation": args.citation or "UNDECLARED",
             "materials": args.materials or "UNDECLARED",
             "decision_context": args.context or "UNDECLARED",
             "sources": [], "claims": [], "tools": [], "decisions": [], "notes": "UNDECLARED"}
        v = check(d)
        if v:  # bad --type value
            for x in v: print(f"REJECTED (file unchanged): {x}", file=sys.stderr)
            return 1
        save(d, args.file); print(f"-> {args.file}"); return 0
    if args.cmd == "migrate":
        with open(args.file) as fh:
            raw = json.load(fh)
        if raw.get("schema") == SCHEMA:
            print(f"REJECTED (file unchanged): {args.file} is already {SCHEMA}", file=sys.stderr)
            return 1
        decl = {}
        if args.depths:
            with open(args.depths) as fh:
                decl = json.load(fh)
        try:
            new, log = migrate(raw, decl)
        except ValueError as e:
            print(f"REJECTED (file unchanged): {e}", file=sys.stderr)
            return 1
        v = check(new, _base_dir(args.file))
        if v:
            for x in v: print(f"REJECTED (file unchanged): {x}", file=sys.stderr)
            return 1
        save(new, args.file)
        for x in log: print(f"MIGRATED: {x}")
        for x in flags(new): print(f"FLAG: {x}")
        return 0
    d = load(args.file)
    if args.cmd == "source":
        if _is_missing(args.id) or _is_missing(args.location) or _is_missing(args.depth):
            print("REJECTED (file unchanged): source requires --id, --location and --depth "
                  "(UNDECLARED is a legal depth; an omitted one is not).", file=sys.stderr)
            return 1
        if any(x.get("id") == args.id for x in d["sources"]):
            print(f"REJECTED (file unchanged): source {args.id!r} already exists; use a new id.",
                  file=sys.stderr)
            return 1
        src = {"id": args.id, "location": args.location, "depth": args.depth}
        if args.detail: src["detail"] = args.detail
        if args.basis: src["basis"] = args.basis
        d["sources"].append(src)
        return _commit(d, args.file, f"source {args.id} recorded ({depth_label(src)})")
    if args.cmd == "override":
        if _is_sentinel(args.deferred_reason) or _is_sentinel(args.by):
            print("REJECTED (file unchanged): override requires --reason AND --by "
                  "(an override is logged, never silent).", file=sys.stderr)
            return 1
        by_id = {x.get("id"): x for x in d["sources"]}
        for c in d["claims"]:
            if c.get("id") == args.id:
                if not ceiling_breaches(c, by_id):
                    print(f"REJECTED (file unchanged): claim {args.id} does not exceed the "
                          f"read-depth ceiling; there is nothing to override.", file=sys.stderr)
                    return 1
                c["ceiling_override"] = {"reason": args.deferred_reason, "by": args.by}
                return _commit(d, args.file, f"claim {args.id}: ceiling override logged "
                                             f"(by {args.by})")
        print(f"REJECTED (file unchanged): no claim {args.id!r} in {args.file}", file=sys.stderr)
        return 1
    if args.cmd == "claim":
        c = {"id": args.id, "text": args.text,
             "evidence_location": args.evidence or "",
             "support": args.support}
        for opt in ("measurand", "grade", "falsifiers", "label", "source",
                    "claim_range", "instrument", "resolution"):
            if getattr(args, opt):
                c["range" if opt == "claim_range" else opt] = getattr(args, opt)
        by_id = {x.get("id"): x for x in d["sources"]}
        by_loc = {x.get("location"): x for x in d["sources"]}
        names = list(args.rests_on or [])
        if args.source and args.source in by_loc and by_loc[args.source]["id"] not in names:
            names.append(by_loc[args.source]["id"])
        quoted = {}
        for q in args.quoted or []:
            sid, sep, val = q.partition("=")
            if not sep:
                print("REJECTED (file unchanged): --quoted takes S1=<value as quoted>",
                      file=sys.stderr)
                return 1
            quoted[sid.strip()] = val.strip()
            if sid.strip() not in names:
                names.append(sid.strip())
        if names:
            c["rests_on"] = [{"source": n, "depth": by_id[n].get("depth") if n in by_id else None,
                              **({"quoted": quoted[n]} if n in quoted else {})}
                             for n in dict.fromkeys(names)]
        d["claims"].append(c)
        return _commit(d, args.file, f"claim {args.id} recorded")
    if args.cmd == "tool":
        t = {"id": args.id, "card": args.card, "state": args.state}
        if args.output: t["output"] = args.output
        if args.declined_reason: t["declined_reason"] = args.declined_reason
        if args.source: t["source"] = args.source
        if args.error_types: t["error_types"] = list(args.error_types)
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
        if args.error_types: k["error_types"] = list(args.error_types)
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
        if v:
            print(f"{len(v)} violations")
            return 1
        fl = flags(d)
        for x in fl: print(f"FLAG: {x}")
        for x in overrides(d): print(f"OVERRIDE: {x}")
        if d.get("_read_from"):
            print(f"NOTE: read from {d['_read_from']} through an in-memory migration; "
                  f"file unchanged; run migrate")
        if fl:
            print(f"VALID — FLAGGED ({len(fl)})")
            return 3 if args.strict else 0
        print("VALID")
        return 0
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
    assert cli("source", "--id", "S1", "--location", "https://example.org",
               "--depth", "ABSTRACT").returncode == 0
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
    assert cli3("source", "--id", "S0", "--location", "doc", "--depth", "FULL_TEXT",
                "--detail", "all").returncode == 0
    assert cli3("claim", "--id", "C1", "--text", "x", "--evidence", "p. 2", "--rests-on", "S0",
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
    # 16. error types (glyph E1-E4): classify a stated miss, never an empty or unrun one
    assert "## Misses classified" not in report(load(f3))  # optional section absent
    before = open(f3).read()
    # 16a. unknown type rejected
    r = cli3("tool", "--id", "T1", "--card", "02", "--state", "RUN", "--output", "pi assumed",
             "--error-type", "E5_GUESS")
    assert r.returncode != 0 and "not in vocabulary" in r.stderr
    # 16b. a tag on a tool that did not run is rejected
    r = cli3("tool", "--id", "T1", "--card", "02", "--state", "NOT_APPLICABLE",
             "--output", "x", "--error-type", "E3_DEFAULTED_SLOT")
    assert r.returncode != 0 and "need state RUN" in r.stderr
    # 16c. a tag with no stated miss is rejected
    r = cli3("tool", "--id", "T1", "--card", "02", "--state", "RUN",
             "--error-type", "E3_DEFAULTED_SLOT")
    assert r.returncode != 0 and "miss stated" in r.stderr
    # 16d. a tag on a design check that was not done is rejected
    r = cli3("design", "--check", "selection", "--state", "NOT_CHECKED",
             "--finding", "x", "--error-type", "E1_DROPPED_VARIABLE")
    assert r.returncode != 0 and "need state CHECKED" in r.stderr
    assert open(f3).read() == before  # every rejection left the file byte-identical
    # 16e. valid tags render under the entry and in the classification section
    assert cli3("tool", "--id", "T1", "--card", "02", "--state", "RUN",
                "--output", "pi assumed from another population",
                "--error-type", "E3_DEFAULTED_SLOT", "--error-type", "E2_STALE_CONDITIONS").returncode == 0
    assert cli3("design", "--check", "selection", "--state", "CHECKED",
                "--finding", "calibration set's selection not discussed",
                "--error-type", "E3_DEFAULTED_SLOT").returncode == 0
    rep3 = report(load(f3))
    assert "error types: E3_DEFAULTED_SLOT, E2_STALE_CONDITIONS" in rep3
    assert "## Misses classified" in rep3
    assert "- E3_DEFAULTED_SLOT: T1, design:selection" in rep3 and "- E2_STALE_CONDITIONS: T1" in rep3
    assert "E1_DROPPED_VARIABLE:" not in rep3  # an empty type is not printed as a clean count
    # 16f. duplicate and forged tags caught in the file
    d = load(f3); d["tools"][0]["error_types"] = ["E3_DEFAULTED_SLOT", "E3_DEFAULTED_SLOT"]
    assert any("listed twice" in x for x in check(d))
    d["tools"][0]["error_types"] = []
    assert any("non-empty list" in x for x in check(d))
    # 17. read depth per source (Card 07)
    f4 = os.path.join(tmp, "s4.json")
    cli4 = lambda *a: subprocess.run([sys.executable, me, *a, "--file", f4],
                                     capture_output=True, text=True)
    cli4("init", "--title", "t", "--type", "EMPIRICAL", "--materials", "x", "--context", "y")
    before = open(f4).read()
    # 17a. a depth is required; UNDECLARED is legal, an omitted depth is not
    r = cli4("source", "--id", "S1", "--location", "u1")
    assert r.returncode != 0 and "--depth" in r.stderr
    r = cli4("source", "--id", "S1", "--location", "u1", "--depth", "SKIMMED")
    assert r.returncode != 0 and "not in vocabulary" in r.stderr
    # 17b. FULL_TEXT needs sections, CARRIED needs its origin
    r = cli4("source", "--id", "S1", "--location", "u1", "--depth", "FULL_TEXT")
    assert r.returncode != 0 and "the sections read" in r.stderr
    r = cli4("source", "--id", "S1", "--location", "u1", "--depth", "CARRIED")
    assert r.returncode != 0 and "what it was carried from" in r.stderr
    assert open(f4).read() == before  # every rejection left the file byte-identical
    assert cli4("source", "--id", "S1", "--location", "u1", "--depth", "CARRIED",
                "--detail", "review R, Table 3").returncode == 0
    assert cli4("source", "--id", "S2", "--location", "u2", "--depth", "UNDECLARED").returncode == 0
    r = cli4("source", "--id", "S1", "--location", "u3", "--depth", "ABSTRACT")
    assert r.returncode != 0 and "already exists" in r.stderr
    # 17c. a source string elsewhere must be a listed source
    r = cli4("design", "--check", "selection", "--state", "CHECKED", "--finding", "x",
             "--source", "u9")
    assert r.returncode != 0 and "not a listed source" in r.stderr
    # 17d. a graded claim must name what it rests on; an ungraded one need not
    r = cli4("claim", "--id", "C1", "--text", "x", "--evidence", "p. 1", "--support", "SUPPORTED")
    assert r.returncode != 0 and "without naming the sources and depths" in r.stderr
    r = cli4("claim", "--id", "C1", "--text", "x", "--evidence", "p. 1", "--support", "UNTESTED")
    assert r.returncode == 0
    r = cli4("claim", "--id", "C2", "--text", "x", "--evidence", "p. 1",
             "--support", "SUPPORTED", "--rests-on", "S9")
    assert r.returncode != 0 and "not a listed source" in r.stderr
    # 17e. --source adds its source to rests_on; the depth is copied from the source
    assert cli4("claim", "--id", "C2", "--text", "x", "--evidence", "p. 1",
                "--support", "UNTESTED", "--source", "u1").returncode == 0
    d = load(f4)
    assert d["claims"][1]["rests_on"] == [{"source": "S1", "depth": "CARRIED"}]
    assert check(d) == [] and flags(d) == []
    rep4 = report(d)
    assert "**S1** CARRIED(review R, Table 3) — u1" in rep4 and "rests on: S1 (CARRIED)" in rep4
    assert "FLAGGED" not in rep4
    # 17f. a graded claim on an UNDECLARED depth is valid but FLAGGED, not clean
    assert cli4("claim", "--id", "C3", "--text", "x", "--evidence", "p. 2",
                "--support", "PARTIALLY_SUPPORTED", "--rests-on", "S2").returncode == 0
    r = cli4("check")
    assert r.returncode == 0 and "VALID — FLAGGED (1)" in r.stdout and "C3" in r.stdout
    assert cli4("check", "--strict").returncode == 3
    assert "## FLAGGED" in report(load(f4))
    # 17g. a restated depth must match the source; a named source must be rested on
    d = load(f4); d["claims"][1]["rests_on"][0]["depth"] = "FULL_TEXT"
    assert any("but the source's depth is" in x for x in check(d))
    d = load(f4); d["claims"][1]["rests_on"] = [{"source": "S2", "depth": "UNDECLARED"}]
    assert any("does not rest on it" in x for x in check(d))
    d = load(f4); del d["sources"][0]["depth"]
    assert any("depth missing" in x for x in check(d))
    # 18. migration: v1 is read, never rewritten implicitly; values kept; depth only from a quote
    v1 = {"schema": "study-aperture/1", "title": "t", "pub_type": "EMPIRICAL",
          "citation": "doi:1", "materials": "Abstract only; the press release P was also read.",
          "decision_context": "UNDECLARED",
          "claims": [{"id": "C1", "text": "a", "evidence_location": "p. 1", "support": "SUPPORTED"},
                     {"id": "C2", "text": "b", "evidence_location": "x", "support": "UNSUPPORTED",
                      "source": "P"}],
          "tools": [], "decisions": [], "design_checks": [], "notes": "n"}
    f5 = os.path.join(tmp, "s5.json")
    with open(f5, "w") as fh:
        json.dump(v1, fh)
    raw = open(f5).read()
    cli5 = lambda *a: subprocess.run([sys.executable, me, *a, "--file", f5],
                                     capture_output=True, text=True)
    # 18a. check reads v1 through an in-memory migration: all depths UNDECLARED, so FLAGGED
    r = cli5("check")
    assert r.returncode == 0 and "FLAGGED (2)" in r.stdout and "in-memory migration" in r.stdout
    assert "Read from study-aperture/1" in report(load(f5))
    # 18b. a mutation on a v1 file is refused, file unchanged
    r = cli5("decide", "--id", "D1", "--text", "q", "--state", "UNRESOLVED")
    assert r.returncode != 0 and "run `assess.py migrate" in r.stderr and open(f5).read() == raw
    # 18c. a declaration whose basis is not in the record is refused
    bad = os.path.join(tmp, "bad.json")
    with open(bad, "w") as fh:
        json.dump({"S0": {"depth": "FULL_TEXT", "detail": "all", "basis": "full text read"}}, fh)
    r = cli5("migrate", "--depths", bad)
    assert r.returncode != 0 and "not found verbatim" in r.stderr and open(f5).read() == raw
    with open(bad, "w") as fh:
        json.dump({"S7": {"depth": "ABSTRACT", "basis": "Abstract only"}}, fh)
    r = cli5("migrate", "--depths", bad)
    assert r.returncode != 0 and "name no source" in r.stderr
    # 18d. migrate with a quoted declaration: depth taken, the rest UNDECLARED, all logged
    good = os.path.join(tmp, "good.json")
    with open(good, "w") as fh:
        json.dump({"S0": {"depth": "ABSTRACT", "basis": "Abstract only"}}, fh)
    r = cli5("migrate", "--depths", good)
    assert r.returncode == 0, r.stderr
    assert "source S1 added" in r.stdout and "FLAG: claim C2" in r.stdout
    d = load(f5)
    assert d["schema"] == SCHEMA and "_read_from" not in d
    assert [s["depth"] for s in d["sources"]] == ["ABSTRACT", "UNDECLARED"]
    assert d["claims"][0]["rests_on"] == [{"source": "S0", "depth": "ABSTRACT"}]
    assert d["claims"][1]["rests_on"] == [{"source": "S1", "depth": "UNDECLARED"}]
    for k in v1:  # no v1 value changed
        if k != "schema" and k != "claims":
            assert d[k] == v1[k], k
    for old, c in zip(v1["claims"], d["claims"]):
        assert {k: c[k] for k in old} == old
    assert d["migrations"][0]["from"] == "study-aperture/1"
    assert "## Migration log" in report(d)
    assert cli5("migrate").returncode != 0  # already migrated
    # 19. the read-depth ceiling (Card 07 section 4): above it -> FLAG; override logged
    f6 = os.path.join(tmp, "s6.json")
    cli6 = lambda *a: subprocess.run([sys.executable, me, *a, "--file", f6],
                                     capture_output=True, text=True)
    cli6("init", "--title", "t", "--type", "EMPIRICAL", "--materials", "x", "--context", "y")
    for sid, dep, *det in (("P", "PRESS_RELEASE"), ("A", "ABSTRACT"), ("N", "SNIPPET"),
                           ("C", "CARRIED", "review R"), ("F", "FULL_TEXT", "Results")):
        extra = ["--detail", det[0]] if det else []
        assert cli6("source", "--id", sid, "--location", sid.lower(), "--depth", dep,
                    *extra).returncode == 0
    def claim6(cid, support, *a):
        r = cli6("claim", "--id", cid, "--text", "x", "--evidence", "p. 1", "--support", support, *a)
        assert r.returncode == 0, r.stderr
    claim6("K1", "SUPPORTED", "--rests-on", "P")                         # above PRESS_RELEASE
    claim6("K2", "PARTIALLY_SUPPORTED", "--rests-on", "P")               # within
    claim6("K3", "UNTESTED", "--rests-on", "N", "--grade", "MEASURED_PRESENT")   # above SNIPPET
    claim6("K4", "UNTESTED", "--rests-on", "A", "--grade", "MEASURED_PRESENT")   # above ABSTRACT
    claim6("K5", "UNTESTED", "--quoted", "A=d = 0.41 (95% CI 0.1-0.7)",
           "--grade", "MEASURED_PRESENT")                                 # lifted by a quote
    claim6("K6", "PARTIALLY_SUPPORTED", "--rests-on", "C")               # above CARRIED
    claim6("K7", "UNTESTED", "--rests-on", "C")                          # within
    claim6("K8", "SUPPORTED", "--rests-on", "P", "--rests-on", "F")      # F permits it
    d = load(f6)
    assert check(d) == []
    fl = " | ".join(flags(d))
    for cid in ("K1", "K3", "K4", "K6"):
        assert f"claim {cid}:" in fl, (cid, fl)
    for cid in ("K2", "K5", "K7", "K8"):
        assert f"claim {cid}:" not in fl, (cid, fl)
    assert d["claims"][4]["rests_on"] == [{"source": "A", "depth": "ABSTRACT",
                                          "quoted": "d = 0.41 (95% CI 0.1-0.7)"}]
    assert "quoted: d = 0.41" in report(d)
    # 19a. a quote lifts only an ABSTRACT source; an override needs reason AND author
    before = open(f6).read()
    r = cli6("claim", "--id", "K9", "--text", "x", "--evidence", "p", "--support", "UNTESTED",
             "--quoted", "P=x")
    assert r.returncode != 0 and "lifts only an ABSTRACT source" in r.stderr
    r = cli6("override", "--id", "K1", "--by", "reviewer")
    assert r.returncode != 0 and "requires --reason AND --by" in r.stderr
    r = cli6("override", "--id", "K2", "--by", "reviewer", "--reason", "x")
    assert r.returncode != 0 and "nothing to override" in r.stderr
    assert open(f6).read() == before
    # 19b. a logged override removes the flag and is printed with its reason
    r = cli6("override", "--id", "K1", "--by", "reviewer", "--reason",
             "press release reproduces the paper's Table 2 verbatim")
    assert r.returncode == 0, r.stderr
    d = load(f6)
    assert "claim K1:" not in " | ".join(flags(d))
    r = cli6("check")
    assert "OVERRIDE: claim K1: support SUPPORTED exceeds" in r.stdout and "by reviewer" in r.stdout
    assert "## Read-depth ceiling overrides" in report(d)
    # 19c. a forged override without an author is a violation; a stale one is FLAGGED
    d["claims"][0]["ceiling_override"] = {"reason": "x"}
    assert any("needs a reason AND a named author" in x for x in check(d))
    d = load(f6); d["claims"][0]["rests_on"].append({"source": "F", "depth": "FULL_TEXT"})
    assert any("stale override" in x for x in flags(d))
    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
