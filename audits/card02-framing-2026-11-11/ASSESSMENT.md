Status: read-only assessment of Card 02 at repository commit `28db96f764f68d6ea0db0d575f74fd3a3c8e9735`. Core files were not edited. The multi-model framing probe has not been run; historical assessor disagreement and the proposed GPT rewrite were not supplied for verification.

# Card 02: preserve the relational rule, correct the physical claim, declare the audit layer

**Card 02 is useful as a declaration discipline, but its first frozen-state sentence is not defensible as an unrestricted statement of physics.** The enforceable rules implement a much narrower registration check. Your framing-dependent probe is a worthwhile experimental proposal, provided its reference record distinguishes physical correctness from whether reporting that issue belongs to the assigned task. The same sentence does not become physically correct when the assessor is told to audit code rather than prose. What changes is the scope of an appropriate response. [1] [2]

## The paragraph being assessed

Card 02, line 54, reads verbatim:

> An average is a state variable only where the system is at equilibrium: the average over time equals the average over the population. A literature, a workforce, a market or an ecosystem under selection is a flow. A mean taken from it is a snapshot of that flow. Used as a fixed model input, it freezes the flow into a constant, and the gradients (where the quantity varies, how fast it moves) drop out.

The card identifies this as a toolbox addition, not an upstream `register_map.py` rule. Its opening provenance statement also says it is a recording discipline and that “the vocabulary is the tool.” Those statements are relevant to its intended use, but they do not withdraw the explicit physical assertion in the quoted paragraph. [1]

## What the relational statement gets right

Your central relation survives the assessment: **when a context-specific average is carried into a model as a fixed value, the scope and justification for holding it fixed should be declared.** The average may depend on population composition, observation period, selection, instrument, or changing conditions. A model can conceal those dependencies by treating an estimated value as portable or timeless. Asking for population, window and an assessment of stability makes that transformation inspectable. This is the useful content of Card 02’s declaration fields and final sentence, “The check is that the freezing is declared.” [1]

There are two different transformations here. Reducing a distribution to one number changes the representation across units. Holding that number fixed changes the representation across time or conditions. Neither transformation is automatically inappropriate, and neither requires that the entire system be at equilibrium. For example, at a specified time, a sum is exactly recoverable from the contemporaneous mean and the number of units. Using that identity need not assume future stability. Whether a mean loses information relevant to the particular target is a separate question from whether the arithmetic is correct.

Similarly, a changing mean can be a component of a nonequilibrium description. Whether that component is sufficient to close the dynamics is another question. “State variable” cannot therefore be restricted to equilibrium merely because some uses of a time-independent average require additional justification.

## Where the physical wording fails

The opening sentence combines three claims that need to remain separate.

**Stationarity** concerns invariance under time shifts of specified statistical properties. Weak stationarity concerns the mean and covariance; strict stationarity concerns the joint distributions. Stable population membership or composition alone does not establish all of these properties. The card’s population-stability question is a useful scope question, not a complete general definition of stationarity. [1] [4]

**Mean ergodicity** concerns whether an appropriate long-time average recovers the corresponding ensemble expectation. It requires a specified process, observable, probability measure and limiting or observational regime. University time-series notes explicitly formulate time-average convergence under stationary and ergodic conditions with an existing expectation; they do not identify this with thermodynamic equilibrium or guarantee exact equality in a finite observation window. An empirical “population average” is not automatically the relevant ensemble expectation either. [4] [6]

**Thermodynamic equilibrium** is a property of a physical system under specified conditions, not a synonym for either of those statistical properties. In Seifert’s master-equation setting, equilibrium and nonequilibrium steady states both have stationary probabilities; detailed balance distinguishes them. The review also gives a driven-ring example with a stationary distribution and a nonzero steady current. A stationary distribution therefore does not establish equilibrium. This is a distinction within the stated physical model, not an arbitrary terminological preference. [5] (§2.2 and §6.1.2)

A particularly simple counterexample separates stationarity from mean ergodicity. Let `X(t) = Y` for every time, where `Y` is one nondegenerate random draw. Every shifted collection of observations has the same joint distribution, so the process is stationary. But one realization’s time average is its particular `Y`, not generally the ensemble expectation `E[Y]`. The probability handout presents this constant-random-path example directly. [4] (§31.1)

Consequently, the literal sentence deserves a **scope/interpretation flag in a prose-correctness audit**. The correct repair is not to reject the relational warning. It is to stop presenting equilibrium, statistical stationarity and time/ensemble interchange as one condition.

I would not describe this as proving a defect in relational reasoning or a defect in an entire cultural tradition. The inspected artifact is this particular wording. Its physical overreach is observable; the exact pre-English reasoning, who introduced each interpretation, and the unseen GPT rewrite are not independently established here.

## What the code actually enforces

The production implementation explicitly says it is a record validator, not a scientific-validity judge. Direct inspection and constructed, read-only probes support the following narrower findings. They are observations about this implementation, not evidence that a publication or physical model is sound. [2]

**Registered input averages require declaration slots.** Population and window must be present or explicitly sentinel-valued; stationarity must use the vocabulary. An `ASSESSED` entry requires a non-sentinel basis and stated population/window. Claim links and split references are checked. An average that the assessor never registers is not discovered by the validator; the `averages` collection is optional. [2] (lines 365–398)

**`FROZEN` does not force `IMPOSED`.** The card prescribes `IMPOSED` with a stated reason, but the executable condition only forbids the three `MEASURED_*` grades on linked claims. Constructed probes also accepted `UNDECLARED`, `UNMEASURED`, `UNDERPOWERED` and an omitted grade. The report’s `-> IMPOSED` text is a rendering, not an assignment to the record. This is a difference between a method prescription and the enforced subset, not permission to reinterpret one as the other. [1] (lines 72 and 86) [2] (lines 399–404 and 459–461)

**`DECLARED` does not certify stationarity or adequacy.** It is derived from declared population/window and the `ASSESSED` label. The checker requires a basis but does not evaluate that basis’s meaning. A constructed basis explicitly saying the population changes still passed the registration check and derived `DECLARED`. That is consistent with a declaration-checking instrument; it would be misleading to read the status as “confirmed stable” or “physically justified.” Fully stated `ASSUMED` and `UNASSESSED` entries remain `PARTIAL`, with incompleteness, rather than becoming invalid. [2] (lines 252–272 and 374–404)

**Range transfer is not a hard physical gate.** The card prescribes an `INCOMMENSURABLE(range)` treatment when an average is carried outside its population/window. These production paths do not compare a claim’s scope with the average’s population or test whether its time interval is contained in the declared window. An `estimated_from` string differing from `population` creates incompleteness; it does not execute a substantive bridge assessment. [1] (line 73) [2] (lines 471–475)

The general five-field layer declaration, discard-rule and imposed-reason prescriptions are also not mandatory claim fields in `assess.py`. The card does describe the upstream vocabulary as a recording discipline rather than code users must run. Accordingly, a rules audit should identify which layer supplies each requirement, not claim that all card prose is production-enforced. Upstream `register_map.py` was not inspected or executed in this assessment. [1] (lines 3 and 11–30) [2] (lines 300–316 and 677–686)

## What your four framings can establish

The useful hypothesis is that framing changes the assessor’s selected audit transformation. **Flag occurrence alone cannot establish that mechanism.** A changed flag rate could also reflect salience, response format, deference to the document, or general prompt compliance. The response needs to expose which claim was flagged, which layer was audited, and why the flag was or was not in scope.

With **bare text**, the audit task is unspecified. A physical objection may be justified, but absence of that objection is not automatically an assessor error. This is an underdetermined task-scope condition, not a known binary no-flag case.

With **“audit the prose for correctness,”** the equilibrium/time-average sentence is directly in scope. A good answer flags its overreach while preserving the declaration discipline. It should not replace “the prose conflates conditions” with “all uses of fixed means are invalid.”

With **“audit the enforceable rules,”** the primary answer concerns what the implementation checks. If only the paragraph is supplied, actual enforcement cannot be established from that paragraph: the assessor must say that code or an enforcement contract is unavailable. If code is supplied, it can distinguish registration status from physical certification and identify prescription/enforcement differences. A separate physical caveat can still be appropriate if explicitly labeled outside the main audit scope. It must not be scored as an enforcement defect merely because it fired.

With **full card context**, “the vocabulary is the tool” clarifies the recording layer, but does not prescribe “ignore literal prose correctness.” A good answer can report both the sound operational purpose and the overstrong physical sentence. Unless the task explicitly selects an exclusive layer, a no-flag answer is not uniquely correct.

These observations refine the proposal rather than negate it. The physical proposition’s truth is invariant across framings. **The task-relative obligation to investigate or report it can be framing-dependent.** A reference process that fails to keep those two axes separate can manufacture disagreement; a reference process that hard-codes four different truth labels can manufacture false agreement just as easily.

## The battery addition I would propose

Add an **experimental, framing-conditioned audit stratum**, not a new mandatory core card. Preserve the verbatim paragraph and its hash. Record the exact framing separately. Keep the underlying physical observation distinct from the task-scope comparison record. For each response, adjudicators should record the assigned layer, the layer actually audited, flag presence, the exact claim targeted, the justification, whether it belongs to that task, and unresolved scope ambiguity.

For this case, the origin/transformation/justification axis is especially useful:

- **Origin:** the hash-bound paragraph, contextual material and code actually supplied; separately disclosed retrieved or prior information.
- **Transformation:** literal physical proposition audit, metaphor-to-operational-rule interpretation, implementation audit, or a declared combination.
- **Justification:** the source passage and argument supporting the physical objection, or the code locations supporting an enforcement finding, plus the reason the observation is relevant to the assigned task.

The proposed four framings change both task instruction and available context. In particular, supplying the full card reveals information absent from the bare paragraph. That makes the four-way comparison useful descriptively, but not a clean isolation of wording alone. A stronger follow-up crosses **instruction framing** with **material availability**: paragraph-only, full card, and full card plus enforcement code. This separates attention selection from the effect of receiving additional evidence.

Use fresh independent contexts, matched source bytes and material packages within each comparison, fixed declared tools/settings, randomized execution order, and repeated runs. Record exact exposed model/version identifiers; family names alone are not versions. Report per-model/per-framing flag counts over completed responses, with attempted, invalid, missing and unscorable denominators separately. Preserve layer-specific adjudication and within-model repetition rather than pooling everything into one agreement score. Reviewers may be blinded to model identity, but they must know the assigned audit task to assess task-relative appropriateness.

`N`, model selection and repetition count remain design decisions here. No live assessor executions were performed. Therefore “models disagreed about transformation rather than physics” remains a hypothesis to test, not an established finding or a Card 07 result.

## A minimal prose repair, without changing the relational content

The following is a **proposed replacement**, not a repository edit or a new validation rule:

> An average compresses a distribution or a time-varying process. When a value estimated for a particular population and window is held fixed in a model, declare what it represents, what variation is not represented by that value, and why holding it fixed is adequate for the intended use. This is a declaration check, not a rule against averages or a certification that the system is at equilibrium. If the reasoning replaces a time average with an ensemble or population average, declare the sampling measure and the assumptions that justify that replacement. Stationarity, observable-specific ergodicity and thermodynamic equilibrium are distinct where they apply; none is established merely by declaring another.

I would also narrow “carries no information about mechanism” to **“matching one freely fitted scalar, by itself, does not independently identify a mechanism.”** The latter keeps the warning against using fit as independent confirmation without asserting that a fitted statistic can never be informative alongside other constraints. [1] (line 75)

The addendum already provides a place conceptually for recording translation losses rather than silently patching them. A proposed entry could retain the original relational form, the English wording introduced, the technical interpretation, the counterexample, and what the correction preserves. But the ledger should not assert that a particular cultural or model transformation caused the wording unless its origin is documented. The same equilibrium phrase is also repeated in ADDENDUM B6; correcting only the card would leave conflicting explanatory text. No addendum item or core card was changed in this assessment. [3] (§A and B6)

**Assessment:** retain Card 02’s declaration discipline; correct its physical overstatement; make prescription versus enforcement explicit; and test framing-conditioned task appropriateness without allowing the reference process to turn an unspecified audit layer into a false answer key.

## References

[1]: https://github.com/JinnZ2/study-aperture/blob/28db96f764f68d6ea0db0d575f74fd3a3c8e9735/cards/02_PREMISES.md "Card 02 at the assessed repository commit"
[2]: https://github.com/JinnZ2/study-aperture/blob/28db96f764f68d6ea0db0d575f74fd3a3c8e9735/assess.py "Study Aperture production validator and report implementation"
[3]: https://github.com/JinnZ2/study-aperture/blob/28db96f764f68d6ea0db0d575f74fd3a3c8e9735/ADDENDUM.md "Study Aperture translation-loss work list and frozen-average entry"
[4]: https://bookdown.org/kevin_davisross/stat350-handouts/stationary.html "STAT 350: stationary stochastic processes and mean ergodicity"
[5]: https://terpconnect.umd.edu/~cjarzyns/CHEM-CHPH-PHYS_703_Spr_20/resources/Rep%20Prog%20Phys%202012%20Seifert.pdf "Udo Seifert: stochastic thermodynamics, fluctuation theorems and molecular machines"
[6]: https://faculty.washington.edu/ezivot/econ582/econ582stationarytimeseriesslides.pdf "University of Washington: stationary time series and the ergodic theorem"
