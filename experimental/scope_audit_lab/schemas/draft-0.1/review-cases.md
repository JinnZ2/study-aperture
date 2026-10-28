# Draft schema review cases

Status: Proposed lab review cases, NOT RUN as a lab validator test suite. A subset was exercised separately as [drafting-time structural probes](drafting-review.md); that note records exactly what was checked and does not change the NOT RUN status of the lab acceptance matrix.

## Structural cases

| Proposed case | Intended result |
|---|---|
| One example of each of the five record types | Accept the proposed record shapes; do not infer evidence completeness or truth |
| A record lacks its schema ID, producer, scope field, or other required field | Reject structurally and identify the field |
| An equation payload is relabeled as an observation | Reject incompatible payload shape rather than coerce types |
| A numeric observation contains present `0` | Accept zero as present |
| A missing/invalid numeric value also contains `value: 0` | Reject the contradictory value object |
| A present numeric value contains a numeric string or null | Reject; no implicit conversion |
| Invalid measurement includes `raw_text` and a reason, but no usable value | Preserve invalid state structurally |
| Unknown record or schema version | Do not claim conformance to draft 0.1; preserve separately as opaque input |
| A criterion claims MET/NOT_MET without any evidence references | Reject structurally |
| A criterion is NOT_EVALUATED with explicit missing evidence | Accept the unresolved record |
| A top-level or payload `verified: true` is added | Reject the undeclared field; do not introduce a universal correctness flag |
| An assumption/artifact/source-specific reference uses a different expected type | Reject that structurally contradictory reference |

## Semantic cases requiring more than JSON Schema

| Proposed case | Required separate review |
|---|---|
| A reference says RESOLVED but the target is absent | Resolver must report the unsupported resolution assertion |
| A reference target has the wrong type/version | Report mismatch; never substitute a similarly worded record |
| Two stored records reuse an ID with different content | Ledger conflict; no last-write-wins evidence replacement |
| Two sources repeat the same statement | Preserve identities and source links; repetition is not independent verification |
| A synthetic observation is cited as physical measurement evidence | Report evidence-kind mismatch |
| An assumption declares SOURCE_EXPLICIT without source provenance | Record missing provenance and do not attribute it to an invented source |
| Derivation step IDs repeat, point forward, or form a cycle | Report invalid dependency structure |
| A step cancels a factor that may be zero | Examine the domain restriction and preserve a failure or unresolved prerequisite as appropriate |
| A present value carries an absence sentinel as free text | Diagnose semantic absence rather than treating the sentinel as substantive evidence |
| A finite set of samples matches an equation | Do not report a universal proof |
| Units match but physical quantities differ | Block unsupported comparison pending compatibility analysis |
| Dimensional checks pass while a coefficient lacks derivation | Keep the dimensional result separate from coefficient justification |
| Covariance is absent | Do not insert zero covariance; distinguish ordinary residual from combined-uncertainty availability |
| A subject or procedure version is missing | Keep missing state visible; do not claim version-reusable verification |
| A criterion has an evidence reference but the procedure never ran | A nonempty reference list is not proof of evaluation |
| A timestamp parses but clocks are unaligned | Do not infer valid cross-clock durations |
| A JSON parser accepts NaN or Infinity extensions | Strict ingestion must reject the nonstandard number or preserve raw input with an invalid diagnostic |

## Empirical and execution limits

No structural or semantic test above establishes that a physical model fits nature. Neither schema text, synthetic fixtures, reviewer agreement, nor successful execution alone establishes empirical adequacy.

No code referenced by these examples is automatically authorized to execute. Voice work remains deferred, and Prototype 0.1 compatibility remains UNKNOWN.
