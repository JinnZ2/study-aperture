Status: bounded reviewer interpretation of four user-supplied assessment records, checked against the publication pages and passages cited below on 2026-11-11. The studies were not reproduced, the original model session was not inspected, and the specimens were not converted to or executed as `assess.py` records.

# Review of the preserved assessment specimens

The originals are retained separately in `data/`; no correction below changes
their text. Attempt 02 follows an attempted correction according to the user,
but assesses a different publication, so it is not a controlled before/after
comparison.

## Attempt 01: three records

- **Demographic-bias identity and claim:** arXiv:2611.00496 concerns a
  demographic-bias audit across three benchmarks and twelve models plus an
  ablation, not FAZE gaze-tracking performance.
  ([Named publication](https://arxiv.org/abs/2611.00496))
  The reported FAZE numbers, 2.44° accuracy, 1.63° STD precision, and 0.47° RMS
  precision, occur in Saxena, Fink, and Lange's gaze study, with calibration,
  offline inference, and winsorized aggregation over retained participants.
  ([Measurement source](https://pmc.ncbi.nlm.nih.gov/articles/PMC11133145/))
  A later webcam paper repeats the trio as prior-work findings.
  ([Intermediate citation](https://arxiv.org/html/2611.04946v1))
  This is a claim-to-publication mismatch, not evidence that the numbers
  themselves are false; finding their donor does not repair the original
  citation or its description of an unconstrained population.

- **Agency evidence retained:** the correctly named Agency paper describes
  the Unix-domain-socket architecture in §4.1, five optimizations in §4.2,
  and benchmarks 2–3× shorter than real-world traces in token count and agent
  turns in §5.1.
  ([Agency full text](https://arxiv.org/html/2611.12122v1))
  The paper explicitly discusses this trace-length difference; that does not
  establish the specimen's additional allegation that compounding state drift
  was omitted.
  ([Agency §§3.1 and 5.1](https://arxiv.org/html/2611.12122v1))
  These full-text locations need reconciliation with the specimen's declared
  abstract-only materials; the record does not establish whether the problem
  was unlogged access, paraphrase, or unsupported generation.
  Its bare `INDEPENDENT_CONVERGENCE` also supplies no named pair or lineage
  basis, and the paper's independent-subtask analysis addresses a different
  kind of independence.
  ([Agency §3.6](https://arxiv.org/html/2611.12122v1))

- **RL/BRACE identity and safety:** arXiv:2611.12865 is Xinjie Shen's study
  of reward–context conflicts, not Choi and colleagues' robotics study.
  ([Named RL publication](https://arxiv.org/abs/2611.12865))
  The matching robotics source is BRACE, arXiv:2611.10938, which reports
  simulated switching wind and Crazyflie hardware with fan disturbances.
  ([BRACE full text](https://arxiv.org/html/2611.10938v1))
  The explicit 27 g description in the inspected passage belongs to the
  simulated Crazyflie, while the hardware passage names Crazyflie 2.1; this
  is not a located basis for fusing those descriptions into one hardware
  statement.
  ([BRACE experimental setup](https://arxiv.org/html/2611.10938v1))
  BRACE disclaims a-priori closed-loop safety guarantees and reports
  a-posteriori Monte Carlo confidence bounds under a specified disturbance
  law.
  ([BRACE safety analysis](https://arxiv.org/html/2611.10938v1))
  No preregistration assertion was found in the inspected text, which does
  not establish that no registration exists.
  ([Inspected BRACE text](https://arxiv.org/html/2611.10938v1))
  The specimen's assessed-stationarity label contains no assessment basis;
  matching a wind law alone must not become a deployment guarantee.

## Attempt 02: early stopping

### What is supported and what was rendered differently

The identifier, title, and Nguyen attribution match the early-stopping paper,
whose abstract reports experiments in which correctness can decrease at later
positions beyond a fitted decoding-noise model's prediction.
([Publication abstract](https://arxiv.org/abs/2611.00166))
Thus the central non-monotonicity claim is substantively grounded, unlike the
cross-paper substitutions in attempt 01.
([Abstract and findings](https://arxiv.org/html/2611.00166v1))

However, the specimen's quoted C1 combines wording rather than retaining one
verbatim passage: §6 uses the heading "Reasoning correctness is not strictly
monotonic" and the sentence "A correct intermediate answer can become
incorrect after additional reasoning," while §1 documents cases of additional
reasoning changing correct answers into incorrect ones.
([Introduction and §6](https://arxiv.org/html/2611.00166v1))
Treat the specimen as a close rendering, not an authenticated verbatim quote
at its declared location; a wording error is not proof of conceptual error.

### Cost accounting: retain both inclusion and exclusion

Section 4.2 defines total generated-token cost as reasoning tokens plus
final-answer tokens plus verifier/sufficiency-probe tokens plus temporary-answer
tokens, and says token-efficiency comparisons use that total unless otherwise
stated.
([Cost accounting](https://arxiv.org/html/2611.00166v1))
The paper separately excludes KV-cache management overhead and says token
costs do not directly establish latency, memory, or energy reductions.
([Assumptions and limitations](https://arxiv.org/html/2611.00166v1))

The specimen's final sentence is therefore too underspecified to treat as
a demonstrated omission: probe-token costs are included, while deployment
resource costs remain outside the reported accounting.
([Cost accounting and limitations](https://arxiv.org/html/2611.00166v1))
Do not equate generated-token count with measured FLOPs, wall-clock latency,
memory, or energy, and do not turn those unmeasured deployment quantities into
evidence that the paper ignored probe tokens.

The source defines \(\pi_m\) as the verifier, \(S_m\) as the checkpoint
function, and \(v_m\) as the number of required probe tokens.
([Early-stopping framework and replay protocol](https://arxiv.org/html/2611.00166v1))
These are distinct objects; neither the notation nor a generic concern about
overhead substitutes for a located accounting gap.

### Thresholds and independence

Section 3.3 explicitly describes increasing the code-task probe-answer budget
by five times and reducing the threshold score by 0.99, and it excludes
answer-based methods from the main coding comparison because complete
provisional code solutions increase cost substantially.
([Adjustments from original implementations](https://arxiv.org/html/2611.00166v1))
These are documented domain-specific adjustments, so a reading that the paper
made no such adjustments would be incorrect; they do not by themselves
establish an adequate recalibration protocol or production transfer.
([Implementation adjustments](https://arxiv.org/html/2611.00166v1))
The specimen says "without domain-specific recalibration," which is not
automatically equivalent to "without any adjustment." Its E3 classification
remains unsubstantiated until the specific threshold, transfer assumption,
calibration criterion, and supporting passage are identified.

The audit compares methods on the same observed prefix streams and shared
probe collection, rather than establishing independence among research
lineages.
([Shared replay methodology](https://arxiv.org/html/2611.00166v1))
Its shared measurement substrate is not itself a defect, but the specimen's
bare `INDEPENDENT_CONVERGENCE` is not a demonstrated pairwise provenance result.

### Unresolved diagnostic and decision scope

- **Design checks:** the specimen supplies bare `CHECKED` states without
  individual findings or passage-level bases. This does not demonstrate
  completed design review, but it also does not prove that no inspection
  occurred; `CHECKED` must not be read as `PASSED`.
- **Input dependency:** the specimen links an undeclared mean of token savings
  to its correctness-reversal claim without showing how that mean enters the
  claim. Do not invent an average or silently assert that dependency.
- **Falsifier:** a new finite sample with no reversals would not, by itself,
  refute an existential observation in another sample. A reproduction test
  needs the original population, protocol, measurement definition, and
  statistical uncertainty.
- **Deployment:** a cost preference does not demonstrate acceptable
  reliability. Preserve the proposed trade-off and any actual operational
  acceptance criteria separately from empirical performance.
- **Provenance:** the supplied text does not establish who originated the
  decision context, which exact HTML portions were held, or whether code
  execution or repository validation occurred. These remain unresolved.

## What this does not establish

- **No model ranking:** four selected records with unknown prompts and
  settings cannot establish Gemini's general reliability, a model comparison,
  or an improvement rate after correction.
- **No study-validity verdict:** an assessment's source mismatch is not a
  failed experiment in the underlying publication. A correctly cited author
  report is also not independent empirical validation.
- **No universal failure label:** identity binding, quote fidelity, diagnostic
  evidence, aggregation scope, decision framing, and physical adequacy remain
  distinct.
- **No automatic source authentication:** the parent validator checks fields
  and vocabulary, not whether a quoted passage belongs to its cited paper.
  ([Pinned validator](https://raw.githubusercontent.com/JinnZ2/study-aperture/faff5800ea5a4ac7c4c38f4780a13f5eb59e5ada/assess.py))
  The parent prompt already asks for verbatim, located claims and explicitly
  supports an LLM-only path.
  ([Pinned entry prompt](https://raw.githubusercontent.com/JinnZ2/study-aperture/faff5800ea5a4ac7c4c38f4780a13f5eb59e5ada/AI_ENTRY_PROMPT.md))

Any later correction should retain these specimens and this review, state the
new material and reviewer decision, and remain separately addressable. Source
checks, diagnostic adequacy, and evidential support must not be merged.
