#!/usr/bin/env python3
"""Offline extraction of selected publisher HTML math; no scientific inference."""

import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path


URL = "https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w"
SELECTED = {"Equ1", "Equ2", "Equ7", "Equ8", "Equ11", "Equ12", "Equ13", "Equ14"}


class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.divs = []
        self.capture = False
        self.buffer = []
        self.equations = {}
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and a.get("name", "").startswith("citation_"):
            self.meta.setdefault(a["name"], []).append(a.get("content"))
        if tag == "div":
            self.divs.append(a.get("id"))
        if tag == "span" and "mathjax-tex" in a.get("class", ""):
            selected = next((item for item in reversed(self.divs) if item in SELECTED), None)
            if selected:
                self.capture = selected
                self.buffer = []

    def handle_data(self, value):
        if self.capture:
            self.buffer.append(value)

    def handle_endtag(self, tag):
        if tag == "span" and self.capture:
            if self.capture in self.equations:
                raise ValueError("Repeated equation ID; no latest-wins extraction.")
            self.equations[self.capture] = "".join(self.buffer)
            self.capture = False
        if tag == "div" and self.divs:
            self.divs.pop()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("html_file", type=Path)
    p.add_argument("--acquired-at", required=True)
    args = p.parse_args()
    raw = args.html_file.read_bytes()
    parser = Extractor()
    parser.feed(raw.decode("utf-8"))
    if set(parser.equations) != SELECTED:
        raise ValueError("Missing/ambiguous selected publisher equations.")
    result = {
        "artifact_kind": "SELECTED_PUBLISHER_HTML_EQUATIONS",
        "source_url": URL, "source_html_sha256": hashlib.sha256(raw).hexdigest(),
        "acquired_at_utc": args.acquired_at,
        "acquisition_time_basis": "Local downloaded-file modification time; not a publisher timestamp or independent clock attestation.",
        "method": "HTMLParser extraction of original publisher mathjax-tex spans; no formula repair.",
        "citation_metadata": parser.meta, "equations": parser.equations,
        "inspection_limits": [
            "Selected HTML TeX inspected; PDF rendering was not inspected.",
            "Full HTML bytes not redistributed; digest binds the acquired page, selected formulas are bundled.",
            "HTML, text extraction, authoring transcription, and execution are distinct evidence stages.",
        ],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
