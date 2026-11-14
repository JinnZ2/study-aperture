Status: an extract of arXiv 2611.05459v1 (quotes only, each one checked verbatim against the paper text and located to a PDF page) and four checks plus a frame note, each tagged OBSERVED / DERIVED / PROPOSED. Co-authored. Not established: any verdict on the paper's validity, on the tools tested, or on literature outside its 102-article corpus. No `assess.py` record is part of this audit.

# Audit: arXiv 2611.05459, "Can Large Language Models Review the Scientific Literature? A Test Against a 102-Article Benchmark"

Source: <https://arxiv.org/abs/2611.05459> (v1, submitted 3 Nov 2026, CC BY 4.0). Read 2026-11-14 from the arXiv HTML and PDF renderings. The authors' public repository <https://github.com/abx40/spanish-plume-llm-literature-review> was read at commit `f2f565bf8502ee294a74945f7dcad158bab9091d` for items the paper points to it for. Hashes are in `manifest.json`.

## Files

| File | Role |
|---|---|
| `quotes.json` | The extract as data: per item, section, verbatim quote. A field the paper does not state is an `UNKNOWN` entry naming the field and what was searched. |
| `EXTRACT.md` | Generated from `quotes.json` + `located.json` by `extract.py --verify`. Quotes only, no reasoning. |
| `located.json` | Per quote: verbatim match (true/false), PDF page, which rendering it was matched in. |
| `CHECKS.md` | C1 constraint, C2 practitioner, C3 cyclical baseline, C4 load withheld / denominator, and the frame note. Reasoning only, tagged. |
| `extract.py` | `--verify ABS PAPER_HTML PDF_TXT` rebuilds `located.json` and `EXTRACT.md` from locally fetched copies; `--check` is the structural check run by `run_checks.sh` (no paper needed). |
| `manifest.json` | Source URLs, retrieval time, sha256 of the three fetched files, the authors' repository commit, hashes of this record's files. |

## Boundaries

- The paper's PDF and HTML are not committed. Their sha256 values let a re-fetched copy be checked; `--verify` needs the local copies.
- Quotes are matched after whitespace normalisation only. A quote that does not match is a failure, never kept silently. PDF pages were found by matching with whitespace, hyphens and quote marks removed, because `pdftotext` breaks lines inside words.
- One quote comes from the arXiv listing page, whose abstract differs from the abstract in the paper body. It is labelled as such and has no PDF page.
- The benchmark review (Schultz et al. 2025) and its database were not read. Facts about them are as this paper states them.
- Voids stay as `UNKNOWN`. They are not filled from general knowledge and not dropped.
- `CHECKS.md` says nothing about the authors; it addresses the study design and the tools' outputs as reported.
