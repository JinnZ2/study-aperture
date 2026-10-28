# Vendored tools — provenance record

These two files are vendored verbatim from the Simulators repository
(CC0-1.0, no rights reserved; attribution not required, recorded anyway).

| File | Upstream path | Upstream commit | Upstream state |
|---|---|---|---|
| `provenance_graph.py` | `tools/provenance_graph.py` | `0655e8b` (2026-10-25) | executable, has selftest |
| `false_agree.py` | `tools/false_agree.py` | `0655e8b` (2026-10-25) | executable, has selftest |
| `conditional_claims.py` | `tools/conditional_claims.py` | `0655e8b` (2026-10-25) | executable, has selftest |
| `safe_provenance.py` | toolbox-written adapter (not upstream) | — | wraps `provenance_graph.py`; selftest |

`SHA256SUMS` records the SHA-256 of the three upstream files, checked against
Simulators `0655e8be2d090030f8e568a8b68b36afdc98fbec` (`tools/`).
`tests/test_repo_integrity.py` fails if a vendored file changes or an
unregistered `.py` file appears here. On a deliberate re-vendor, update this
table and `SHA256SUMS` together (`sha256sum provenance_graph.py false_agree.py conditional_claims.py`).

Run their selftests from this folder:

```sh
python3 provenance_graph.py selftest
python3 false_agree.py selftest
python3 conditional_claims.py selftest
python3 safe_provenance.py selftest
```

Their upstream limitations carry over unchanged:

- `provenance_graph.py` proves a property of the graph you declare. It judges
  no truth, and an incomplete graph can only ever return "no shared ancestor
  found in the declared graph" — never "independent in the world."
- `false_agree.py` routes by the provenance fields you record. Missing
  lineage fields return `UNDERDETERMINED`, not a verdict.
- `conditional_claims.py` checks the *form* of conditional claims
  (restatement fidelity). It judges no truth.
- `safe_provenance.py` is a toolbox-written adapter, not upstream code: it
  renames `provenance_graph`'s outputs to what is actually proven and refuses
  unknown nodes (the raw tool scores them INDEPENDENT).

Upstream license: CC0-1.0 (Simulators `LICENSE`).
