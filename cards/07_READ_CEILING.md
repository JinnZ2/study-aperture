# Card 07 — Read ceiling: read depth per source

**Provenance:** JinnZ2/Simulators `mining-increment/SOURCE_DROP_V2.md`, paragraph "READ CEILING", and the audit claim `MI_010` in `mining-increment/CLAIM_TABLE.md` (CC0, co-authored; read at Simulators `main` `38a77bc`). Status: documented procedure adapted from one upstream instance. The depth vocabulary below is this card's, not upstream's: upstream states one depth (abstracts and citation metadata) in prose. **Not enforced by `assess.py`**: there is no per-source field and no check; the declaration lives in `source` / `notes` text by convention. Co-authored.

## 1. What the card is for

Card 00 asks for the material held, once per record. A record usually rests on several sources read to different depths, and one record-level line hides which claim rests on which depth.

Upstream's case: a source was entered from its abstract, the row is right at that depth, and the content the assessment actually needs (a model's boundary condition) is not visible at that depth. That is its own state:

```text
not CARRIED-and-unverified   the source was read, at a stated depth
not absent                   the source exists and is cited
below ceiling                the load-bearing content sits deeper than the read
```

Upstream: "This is a capability limit on the audit, not an open question about the work."

## 2. Read depth, per source

Declare one depth for every source a claim, tool output or design check rests on.

| Depth | Meaning |
|---|---|
| `SNIPPET` | a search-result fragment or index entry; not the document |
| `PRESS_RELEASE` | coverage or a release about the work, not the work |
| `ABSTRACT` | the abstract and citation metadata only |
| `FULL_TEXT` | the document itself, read; name the sections if only some were |
| `CARRIED` | not read: taken from another document's report of it, or from memory |
| `UNDECLARED` | depth not stated; kept, never read as `FULL_TEXT` |

Rules:
- Depth is per source, not per record. Two sources in one claim can have two depths.
- `CARRIED` names what it was carried from.
- A preprint, a corrected version and a published version are different sources, not different depths.
- `FULL_TEXT` of some sections (methods only, figures only) is written as `FULL_TEXT` plus the sections read. Anything outside them is at the next depth down that was actually read.

## 3. The ceiling declaration

When a claim needs content a source's depth cannot show, write the three parts upstream's paragraph has (counted in `MI_010`):

1. **Depth read at.** For example `ABSTRACT`.
2. **What is not visible at that depth**, named: the exact quantity, method detail or formulation the claim needs.
3. **The retrieval step**, routed into the method as a next step, not as a caveat.

## 4. What the ceiling forbids

- No support grade may rest on content above a source's read depth. If the claim needs it, the claim's support stays `UNTESTED` or `UNDETERMINED` until the retrieval step runs.
- Nothing may be filled in to stand where the unread content would be: no reconstructed formulation, figure or number.
- Compliance can be checked in both directions (upstream's falsifier): the record should contain nothing that only a deeper read could have supplied. Upstream checks this mechanically on its scaffold; here it is a reviewer check, because no field exists.

## 5. Where to write it now

Until `assess.py` has a field (it does not; adding one is a schema change, see CLAUDE.md):

- `--source` on `claim`, `tool` and `design`: give the location, then the depth. For example `doi:10.x/abc (ABSTRACT)`.
- `materials` on `init`: list each source with its depth.
- A ceiling declaration (section 3) goes in `notes`, or in the tool output that hit it.

Two existing examples already do this in free text: `examples/aaiw-reversal-2026/` ("Press coverage only", with a separate fetched PDF) and `examples/arase-may2024/` ("not checkable at press-release depth").

## 6. Limits

- One upstream instance. The vocabulary in section 2 is a proposal, not upstream's and not tested across records.
- No validator: a record can state no depth at all and still check `VALID`.
- A declared depth is recorded provenance, not verified provenance (same rule as every `source` field).
- The card says nothing about whether a source is right, only about how deeply it was read.
