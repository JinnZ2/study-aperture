Status: list of open-access research hosts approved by the repository owner for study pulls. Reachability below is from one cloud session on 2026-11-14 (one request per host). Not established: that any host stays reachable, that a source's licence permits redistribution (check per item), or anything about the content's validity.

# Sources for study pulls

A study pull fetches the publication (and its data or code, if any) from an
open-access host so an assessment can quote it. Record the URL, the retrieval
time and the sha256 of what was fetched (see `audits/*/manifest.json`).

| Host | For | Reachable 2026-11-14 |
|---|---|---|
| arxiv.org | arXiv abstracts, HTML and PDF full text | yes |
| export.arxiv.org | arXiv API (metadata queries) | yes |
| www.biorxiv.org | bioRxiv biology preprints, including PDF and supplementary paths on this host | no (network policy) |
| api.biorxiv.org | bioRxiv / medRxiv metadata API | no (network policy) |
| www.medrxiv.org | medRxiv medical preprints | no (network policy) |
| www.ncbi.nlm.nih.gov | PubMed Central open-access papers | no (network policy) |
| eutils.ncbi.nlm.nih.gov | NCBI E-utilities API (PubMed / PMC search and fetch) | no (network policy) |
| europepmc.org | Europe PMC open papers | no (network policy) |
| papers.ssrn.com | SSRN social-science and economics papers | no (network policy) |
| osf.io | OSF preprints, preregistrations, data | no (network policy) |
| api.osf.io | OSF API | no (network policy) |
| zenodo.org | datasets and code | no (network policy) |
| api.openalex.org | OpenAlex citation graph and metadata | no (network policy) |
| api.semanticscholar.org | Semantic Scholar paper search and citations | no (network policy) |
| doaj.org | Directory of Open Access Journals | no (network policy) |

"No (network policy)" means the session's proxy refused the connection
(`connect_rejected`); the site itself was not reached. A host becomes
reachable once it is added to the cloud environment's allowed domains.

## Rules for using these hosts

- One host's reachability is not another's: test before relying on it, and
  record a refused host as BLOCKED, never as "not found".
- Quote from what was fetched; a fact the source does not state stays
  UNKNOWN.
- Do not commit fetched papers unless their licence allows it; commit their
  hashes instead.
- Hosts not on this list are not approved by this file.
