#!/usr/bin/env python3
"""safe_provenance.py -- adapter over provenance_graph that scopes its outputs.
CC0. stdlib only.

Why this adapter exists: the raw tool prints "INDEPENDENT" when two nodes share
no ancestor IN THE DECLARED GRAPH, and "SHARED ... agreement is one source
echoed" when they share one. Both overstate:

  - Disjoint declared graphs do not establish real-world independence. The
    graph is only what you declared; absence of a shared node may just mean
    you did not draw the edge.
  - A shared ancestor (a methods paper, a common background assumption) does
    not by itself establish that two measurements are "one source echoed".
    That is a property of WHAT the shared node contributes, which a human must
    inspect.

This adapter renames the outputs to what is actually proven, and refuses to
score nodes that are not in the graph at all (the raw tool returns INDEPENDENT
for unknown nodes, which is silently wrong).

Usage:
  python3 safe_provenance.py check prov.json Ranehill2015 Ronay2016
  python3 safe_provenance.py checkset prov.json A B C
  python3 safe_provenance.py selftest
"""
import argparse, sys

import provenance_graph as pg


def safe_check(g, a, b):
    nodes = set(g.edges)
    unknown = [n for n in (a, b) if n not in nodes]
    if unknown:
        return {"status": "UNKNOWN_NODE", "unknown": unknown,
                "note": "these nodes are not in the declared graph; no result"}
    ok, wit = pg.independent(g, a, b)
    if ok:
        return {"status": "NO_SHARED_ANCESTOR_IN_DECLARED_GRAPH", "witness": [],
                "note": "proves a property of the declared graph only; does not "
                        "establish real-world independence"}
    return {"status": "SHARED_ANCESTOR_IN_DECLARED_GRAPH", "witness": wit,
            "note": "shared ancestry is proven; whether it makes the agreement "
                    "'one source echoed' depends on what the shared node "
                    "contributes -- inspect the witness, do not score it"}


def safe_checkset(g, nodes):
    unknown = [n for n in nodes if n not in set(g.edges)]
    if unknown:
        return {"status": "UNKNOWN_NODE", "unknown": unknown,
                "note": "these nodes are not in the declared graph; no result"}
    all_ind, results = pg.check_set(g, nodes)
    return {"status": "ALL_PAIRS_NO_SHARED_ANCESTOR_IN_DECLARED_GRAPH" if all_ind
            else "SOME_PAIRS_SHARE_ANCESTORS_IN_DECLARED_GRAPH",
            "pairs": results,
            "note": "set-level: pairs are reported individually. A dependent pair "
                    "does not by itself invalidate the whole set -- identify the "
                    "affected pairs, retain the independently supported portions, "
                    "and record what the shared node actually contributes"}


def main(argv=None):
    p = argparse.ArgumentParser(description="scoped provenance check")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("path"); c.add_argument("a"); c.add_argument("b")
    cs = sub.add_parser("checkset"); cs.add_argument("path"); cs.add_argument("nodes", nargs="+")
    sub.add_parser("selftest")
    args = p.parse_args(argv)
    if args.cmd == "selftest":
        return selftest()
    g = pg.load(args.path)
    if args.cmd == "check":
        r = safe_check(g, args.a, args.b)
        print(f"{r['status']}" + (f" witness={r['witness']}" if r.get("witness") else "")
              + (f" unknown={r['unknown']}" if r.get("unknown") else ""))
        print(f"  {r['note']}")
        return 0
    if args.cmd == "checkset":
        r = safe_checkset(g, args.nodes)
        print(r["status"])
        for a, b, ok, wit in r.get("pairs", []):
            print(f"  {a}~{b}\t{'NO_SHARED_ANCESTOR' if ok else 'SHARED:' + ','.join(wit)}")
        print(f"  {r['note']}")
        return 0


def selftest():
    g = pg.Graph()
    pg.add_edge(g, "S1", "Smith2019"); pg.add_edge(g, "S2", "Smith2019")
    pg.add_edge(g, "S3", "fieldA")
    # unknown nodes are refused, not scored INDEPENDENT
    r = safe_check(g, "Ranehill2015", "S1")
    assert r["status"] == "UNKNOWN_NODE" and "Ranehill2015" in r["unknown"]
    # shared ancestor: renamed, witness flagged for inspection
    r = safe_check(g, "S1", "S2")
    assert r["status"] == "SHARED_ANCESTOR_IN_DECLARED_GRAPH" and r["witness"] == ["Smith2019"]
    # disjoint declared graphs: renamed, does not claim real-world independence
    r = safe_check(g, "S1", "S3")
    assert r["status"] == "NO_SHARED_ANCESTOR_IN_DECLARED_GRAPH"
    # set-level keeps pairs individual
    r = safe_checkset(g, ["S1", "GHOST", "S3"])
    assert r["status"] == "UNKNOWN_NODE" and "GHOST" in r["unknown"]
    r = safe_checkset(g, ["S1", "S2", "S3"])
    assert r["status"] == "SOME_PAIRS_SHARE_ANCESTORS_IN_DECLARED_GRAPH"
    assert len(r["pairs"]) == 3
    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
