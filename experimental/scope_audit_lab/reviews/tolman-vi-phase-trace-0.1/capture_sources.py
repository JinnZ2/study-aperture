#!/usr/bin/env python3
"""Extract selected source formulas from already acquired local HTML; no network."""

import argparse
import hashlib
import importlib.util
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "tolman-vi-2026-10-27"
SELECTED = {7, 8, 12, 13, 22, 29, 31, 32, 34, 35}


class PreprintMath(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.equations = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        match = re.fullmatch(r"S\d+\.E(\d+)\.m\d+", attrs.get("id", ""))
        if tag == "math" and match and int(match[1]) in SELECTED:
            key = "Equ" + match[1]
            self.equations.setdefault(key, []).append({
                "math_id": attrs["id"], "original_alttext": attrs.get("alttext"),
            })


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("publisher_html", type=Path)
    p.add_argument("preprint_html", type=Path)
    args = p.parse_args()
    spec = importlib.util.spec_from_file_location("original_capture", PARENT/"extract_source.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SELECTED = {"Equ"+str(i) for i in SELECTED}
    original = args.publisher_html.read_bytes()
    pp = args.preprint_html.read_bytes()
    publisher = module.Extractor()
    publisher.feed(original.decode())
    preprint = PreprintMath()
    preprint.feed(pp.decode())
    expected = module.SELECTED
    if set(publisher.equations) != expected or set(preprint.equations) != expected:
        raise ValueError("Missing selected equation IDs; no formula silently supplied.")
    print(json.dumps({
        "kind": "SELECTED_EQUATION_CAPTURE",
        "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
        "publisher": {
            "url": module.URL, "original_html_sha256": hashlib.sha256(original).hexdigest(),
            "equations": publisher.equations,
        },
        "preprint": {
            "url": "https://arxiv.org/html/2610.11319v1",
            "version_record_url": "https://arxiv.org/abs/2610.11319",
            "version": "v1", "submitted_at_utc": "2026-10-08T06:23:18Z",
            "original_html_sha256": hashlib.sha256(pp).hexdigest(),
            "equations": preprint.equations,
            "acquisition_timestamp": {"status": "MISSING", "reason": "Exact HTTP acquisition time not instrumented."},
            "raw_html_origin": "Raw HTML returned by the URL-fetch tool, copied from its read-only output; no custom HTTP fetch.",
        },
        "limits": [
            "TeX representations differ; no whole-paper byte or semantic equivalence is asserted.",
            "Same source lineage, not independent scientific confirmation.",
            "Signs and definitions are examined in the attributed review; extraction alone validates no equations.",
        ],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
