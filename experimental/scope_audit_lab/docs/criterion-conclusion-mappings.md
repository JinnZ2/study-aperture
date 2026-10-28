# Criterion-to-conclusion mappings, draft 0.1

Status: Proposed mapping contract, not a stable schema, adopted inference engine, or extension of the runtime checker's scientific authority. The project owner authorized drafting explicit mappings and a worked study assessment; this does not establish full requirements conformance.

The purpose is to prevent a recorded criterion result from silently changing the property under discussion. A dimension check cannot become a proof, a simulation fit cannot become an empirical measurement, and an assessment of applicability cannot become a claim that a physical law has been confirmed.

## Mapping objects

Each mapping declares the following information before its outcome is interpreted. Missing information blocks the affected implication, not the preservation of observations or calculations.

- **Identity:** A unique mapping ID, explicit draft-contract version, mapping version, author, and status.
- **Subject binding:** Exact record ID, type, version, field/step selector, and available state/artifact hashes. Matching version labels alone do not prove equal content.
- **Target property:** A named lane/property ID and exact, narrowly worded conclusion, together with domain, hypotheses, exclusions, and quantifier.
- **Criterion binding:** Assessment ID/version, criterion ID/version, exact rule, procedure version, expected result, tolerances or proof obligations, and examined evidence.
- **Evidence obligations:** What must be directly inspected, calculated, measured, version-bound, scope-compatible, or independently reproduced. Source-reported results remain source-reported.
- **Outcome implications:** Separate, explicit implications for `MET`, `NOT_MET`, `INDETERMINATE`, and `NOT_EVALUATED`; neither absence nor failed execution defaults to `NOT_MET`.
- **Defeaters and limits:** Known conflicts, provenance gaps, scope violations, uncertainty limits, and alternative explanations that prevent the proposed implication.
- **Authorization:** Who proposed or reviewed the mapping, and what remains unapproved. Authorship is not an independent validation.

An example machine-readable declaration is supplied in the [worked study's mappings](../reviews/tolman-vi-2026-10-27/mappings.json). It is a sidecar draft, not a supported new record type; the 0.2.0 runtime checker does not execute these mappings or establish property alignment.

## Independent property lanes

| Lane | Required evidence before a qualified conclusion | Permissible narrow wording | Forbidden promotion |
|---|---|---|---|
| Mathematical validity | Exact statement/domain; justified transformations; defined operations; stated quantifier; inspected proof or restricted calculation | “These coefficient identities hold exactly under the stated assumptions,” or “this checked step disagrees at the recorded admissible inputs” | Finite numerical samples become a universal proof; inability to verify becomes a contradiction |
| Dimensional and quantity compatibility | Declared unit/coordinate conventions, symbol meanings, dimension signatures, quantity kinds, scalar/vector/tensor structure, and inspected operations | “The inspected terms have compatible declared dimensions and quantity structure” | Dimension compatibility establishes coefficients, dynamics, or empirical truth |
| Numerical agreement | Same target quantity/state, compatible representations, explicit inputs, validity domain, tolerances, method and convergence/sensitivity evidence | “The two implemented expressions agree within the declared tolerance at these inputs” | Agreement proves an identity, validates the solver globally, or measures nature |
| Empirical support | Actual observations, population/system and conditions, instrumentation/calibration, uncertainty and selection information, compatible predictions, and comparison procedure | “These observations support this specified prediction within the recorded conditions and uncertainty model” | A theoretical paper, literature quotation, or synthetic run becomes an independent physical experiment |

Applicability is a separate gate for interpreting a result physically, not an extra vote for a model. Evidence for one lane does not satisfy another lane's obligations unless a separately declared, justified bridge is examined.

## Outcome semantics

- **MET:** The recorded procedure met its exact rule. Only the declared, scoped implication is eligible for review, and only if the evidence obligations and defeater checks are satisfied.
- **NOT_MET:** That rule was not met under the recorded inputs/procedure. This does not automatically falsify the subject, locate a root cause, or refute an entire publication.
- **INDETERMINATE:** The attempted procedure could not establish that rule's status. Preserve the reason, partial results, and unresolved alternatives.
- **NOT_EVALUATED:** No qualifying procedure was performed. Do not infer either success or failure.

A missing prerequisite, missing artifact, unresolved version, or nonfinite result must not be replaced with a default value. An unsupported mapping remains a proposal even when all referenced IDs resolve.

For a discrepancy, retain the original expression, the independently stated comparison, the exact inputs, and the size/direction of the difference. If an alternative sign convention or transcription repair would change the result, register it as a separate candidate rather than silently correcting the source.

## Review gates and reporting

A future executor must check mapping identity and uniqueness, subject/criterion versions, exact selectors, property-lane identity, procedure execution, artifact inspection, evidence scope, declared tolerances, and conflicts. A version mismatch or undeclared cross-lane implication blocks the mapping, while conflicting results remain side by side.

Reports must distinguish the proposed conclusion, criterion outcome, mapping eligibility, attributed reviewer assessment, and scientific support status. They must not combine independent properties into a numerical score or a final “physics verified” label.

Required adversarial cases include a dimensional pass offered as empirical support, a numerical match offered as proof, an uninspected source assertion, a stale criterion, a wrong-field assessment, a zero/undefined denominator, a noisy near-threshold result, and two conflicting examinations of the same property. Drafting these cases does not claim their full implementation.

## First worked application

The [October 27, 2026 study assessment](../reviews/tolman-vi-2026-10-27/study-assessment.pplx.md) separates exact rational coefficient checks, numerical comparison of two published expressions, unresolved coordinate-unit conventions, and absent new empirical measurements. Its computed values are local numerical results, not new neutrino observations or an audit of every derivation in the paper.

The paper is Daniele Gregoris, “Neutrino oscillations inside ultrarelativistic matter: on the role of the Tolman VI spacetime,” published October 27, 2026 in The European Physical Journal C ([publisher article](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). The paper's applicability conditions, source equations, and theoretical status are preserved separately from the authoring checks.

Prototype 0.1 compatibility remains UNKNOWN, voice is DEFERRED, and these mappings do not establish baseline requirements specification 0.2 conformance. Existing schemas and historical verification artifacts remain unchanged.
