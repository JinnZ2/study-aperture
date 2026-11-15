Status: an extract of three papers on London taxi drivers' hippocampi, plus eight checks, a proposed study and open questions. Every quote is checked verbatim against the fetched source text. Checks are tagged OBSERVED / DERIVED / PROPOSED. Co-authored. Not established: any verdict on the papers' validity, anything in the 2006 paper's body or the 2011 supplement (neither was read), and any premise marked "carried" in `CHECKS.md`. No `assess.py` record is part of this audit.

# Audit: Maguire et al. 2000, Maguire et al. 2006, Woollett & Maguire 2011

| Short name | Paper | Read |
|---|---|---|
| M2000 | Navigation-related structural change in the hippocampi of taxi drivers. *PNAS* 97(8):4398–4403. doi:10.1073/pnas.070039597 | full text (PMC HTML) |
| M2006 | London taxi drivers and bus drivers: a structural MRI and neuropsychological analysis. *Hippocampus* 16(12):1091–1101. doi:10.1002/hipo.20233 | abstract only |
| W2011 | Acquiring "the Knowledge" of London's layout drives structural brain changes. *Current Biology* 21(24):2109–2114. doi:10.1016/j.cub.2011.11.018 | main text (Europe PMC, CC BY 3.0); supplement not read |

The checks also name two more sources, read as Europe PMC records:
- Dahmani & Bohbot 2020: abstract.
- Draganski et al. 2004: title only, since the record carries no abstract.

## Files

| File | Role |
|---|---|
| `quotes.json` | The extract as data. Each entry has a source, a section and a verbatim quote. A field the fetched text does not state is an `UNKNOWN` entry naming the field and what was searched. |
| `EXTRACT.md` | Generated from `quotes.json` + `located.json` by `extract.py --verify`. Quotes only. |
| `located.json` | Per quote: verbatim match against its source. Per source: hit counts for `stress`, `cortisol`, `passenger`, `emotion`, `fare`. |
| `CHECKS.md` | Checks C1–C8, the proposed five-arm study (with an optional responder arm), and OPEN QUESTIONS. Reasoning only, tagged. |
| `extract.py` | `--verify SRC_DIR` rebuilds `located.json` and `EXTRACT.md` from local copies, checking their sha256 first. `--check` is the structural check run by `run_checks.sh`; it needs no paper. |
| `manifest.json` | URLs, retrieval times and sha256 of the fetched files; what was blocked and why; hashes of this record's files. |

## Boundaries

- No fetched text is committed. The sha256 values let a re-fetched copy be checked.
- Matching ignores whitespace only, because tag stripping puts spaces around inline citation links. Every other character must match. A quote that does not match fails `--verify`.
- Several sources were blocked (details in `manifest.json`):
  - www.pnas.org returned a bot challenge, so the PMC copy of M2000 was used.
  - M2006's full text was not reachable: the Wiley and UCL hosts were refused, and Europe PMC lists the paper as subscription-only.
  - W2011's supplement was not fetched.
- The fetch hosts were added to this session's environment for this task: `pmc.ncbi.nlm.nih.gov`, `www.ebi.ac.uk` (Europe PMC REST), `eutils.ncbi.nlm.nih.gov`, `europepmc.org` and `www.pnas.org`. `SOURCES.md` lists the hosts approved for study pulls; `pmc.ncbi.nlm.nih.gov`, `www.ebi.ac.uk` and `www.pnas.org` are not on it.
- Voids stay `UNKNOWN`. They are not filled from general knowledge.
- Practitioner input appears only as "a practitioner reports", as a single unverified report (C7).
- `CHECKS.md` says nothing about the authors. It addresses the designs and the results as reported.
