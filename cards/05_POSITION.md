# Card 05 — Position, frame, and scope guards (optional card)

**Provenance:** four upstream methods: `method-layer/observer_position_control.py` and `frame_probe.py` (executable, `365669b`), Simulators `grounding-layers/` (executable but requires NumPy), and `chain-position-detectability` (research note, documented procedure only). Status: mixed — see each section. **Optional** — these need material or inputs the publication will often not supply; `NOT_APPLICABLE` is a common, correct outcome.

## 1. Observer position (upstream executable: `observer_position_control.py`)

Question: is a label (adaptive/maladaptive, normal/pathological) set by the **described behavior** or by **the describer's position** relative to the described population? The upstream tool codes published sources blind to position, then runs a fixed null sequence (behavior difference → decade → literature type → intensity, jointly) and reports only the residual.

Applied to a study: when a publication classifies a group's behavior, ask whether the same behavior would be classified differently if the describer were inside vs. outside that group, and whether the publication supplies or merely assumes an adaptive account. Upstream prediction structure carried over: describer-inside tends to draw need/adaptation readings; describer-outside draws pathology/artifact readings. Record as a **hypothesis with its nulls**, not a finding.

Upstream limits carried over unchanged: cannot distinguish position from competence, from coding bias in the input, or an observer effect from a selection effect in how sources reached the corpus.

## 2. Frame probes (upstream executable: `frame_probe.py`)

Question: does the term under dispute mean the same thing to the parties citing it? The upstream module estimates a respondent's frame from **hand-authored probes only** — `Probe` rejects any `author_kind` other than `human`, and no probe library ships with it. The module only runs selection and collapse reading.

The rule that transfers: **a model generating its own probes could read its own frame back and call it a finding.** Probes must come from outside the system being probed. If the publication's key term collapses differently across the studies that "agree" on it, that is a definitional split — record it (it also feeds Card 03's `FALSE_AGREE_DEFINITION`).

## 3. Grounding layers (upstream executable, needs NumPy)

Simulators `grounding-layers/` audits claims against a stack where each layer is bounded by every layer below it: L0 physics/causality, L1 thermodynamics, L2 planetary mass balance, L3 ecological homeostasis, L4 biomechanical/sensorimotor, L5 human constructs, Lε epistemic state. SCOPE-annotated guards **refuse to score** claims outside a layer's ontology rather than returning a number.

Applied to a study: before checking a claim's statistics, check its layer. A claim about energy systems that violates L1, or a claim about human performance that violates L4's biomechanics, fails before its p-values matter. The refusal to score out-of-scope is the tool working, not failing.

## 4. Assumed stabilities (upstream: research note, documented procedure)

From `chain-position-detectability`: a chain of reasoning that assumes a link stays stable (a supply, a platform, an instrument, a policy) carries **assumed stabilities**. The rule: **an unassessed factor is treated as unknown, not as stable** — and *unknown is not a finding of instability*; it is a finding of missing assessment. Applied to a study: list the background conditions the design and analysis assume hold, and mark each `ASSESSED`, `ASSUMED`, or `UNASSESSED`. An `UNASSESSED` entry changes how much you trust the result; it does not by itself refute anything.

Also carried over: same-model/same-instrument redundancy is not independent redundancy — shared architecture can mean shared failure modes (upstream notes this as a *possibility to check*, not an established fact).

## Limits

- This card's tools need inputs (blind-coded corpora, probe libraries, layer declarations) the publication alone will rarely supply.
- Every tool here returns `UNKNOWN_measurable` or `BLOCKED` rather than guessing; expect those returns and record them.
