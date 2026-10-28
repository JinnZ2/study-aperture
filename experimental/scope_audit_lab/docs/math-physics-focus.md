# Scope Audit Lab: mathematics and physics focus

Status: Active scope direction approved by the project owner; procedures and implementation choices below remain proposals. No mathematical audit engine, symbolic prover, numerical backend, or validated physics assessor is implemented by this document.

## Recorded scope decision

- **Decision S-01 / APPROVED:** prioritize evidence and assessment concerning mathematics, equations, and physics analysis.
- **Decision maker:** project owner.
- **Approval reference:** the project-owner instruction in the study-aperture planning conversation: “Yes, let’s focus primarily upon evidence, assessment, concerning mathematical and equation and physics analysis and defer the voice part.”
- **Permitted work:** refocus planning and review on mathematical and physical claims, their assumptions, derivations, measurements, and verification limits. This does not select a storage backend, settle open design gates, establish compatibility with Prototype 0.1, or authorize arbitrary audited-code execution.
- **Decision S-02 / DEFERRED:** voice-event schemas, classification, collection, and live instrumentation are outside the current work scope.
- **Deferral reason:** explicit owner prioritization of mathematics/physics evidence and assessment.
- **Revisit trigger:** an explicit owner request to resume voice work, followed by the necessary capability, annotation, consent, and execution reviews; no automatic date or milestone reactivates it.
- **Affected plans:** W-01 through W-03 are deferred, and VOICE.01 through VOICE.07 remain NOT RUN and excluded from the current milestone. These requirements remain in the unchanged baseline; this scoped milestone cannot claim full specification 0.2 conformance.

This decision narrows current work without deleting the voice requirements or rewriting their history. The evidence, verification, numerical, and integration design choices remain open unless separately approved.

### Subsequent baseline decision

The owner subsequently approved [E-01](decision-checklist.md#e-01-approval-record): “Proceed independently; mark Prototype 0.1 compatibility unknown”. Prototype inspection is no longer a prerequisite for independent work; compatibility remains UNKNOWN, and no prototype modules, interfaces, or validation results are assumed inherited.

## Proposed assessment unit

Make the unit of assessment an exact mathematical or physical claim under declared conditions, not an entire paper labeled correct or incorrect. A single publication may contain a valid derivation, a numerically fragile implementation, and an empirically unresolved application; retain those findings separately.

For each assessed claim, propose recording:

| Declaration | Evidence to retain |
|---|---|
| Exact claim and representation | Original equation/text, source location, transcription provenance, notation mapping, and representation version |
| Kind of statement | Definition, identity, theorem, approximation, constitutive relation, conservation statement, empirical fit, simulation output, or proposed interpretation; do not infer its kind solely from notation |
| Domain and scope | Variable domains, admissible inputs, spatial/time scales, operating regime, boundary/initial conditions, and excluded interactions |
| Mathematical structure | Scalar/vector/tensor types, index/coordinate conventions, operators, function regularity, and prerequisites where relevant |
| Physical quantities | Quantity identity, dimensions, units, sign/reference conventions, and measurement procedure where empirical |
| Assumptions and dependencies | Explicit hypotheses, closure relations, parameter estimates, independence assumptions, and upstream derivation/input references |
| Procedure and result | What property was examined, by which method, on which state, with which outcome and limitations |
| Open questions | Missing derivation, unmeasured parameter, unresolved interaction, alternative explanation, or unavailable capability |

These are proposed assessment declarations, not implemented schema fields or a demand that every claim contain every kind of evidence. A purely mathematical claim need not invent an empirical measurement, and a measurement report need not invent a proof.

## Proposed reasoning sequence

### Capture the claim and its domain

Preserve the original expression alongside any machine-oriented transcription. Record ambiguous symbols, missing parentheses, uncertain units, and inaccessible supplementary material before analysis; a transcription error must not become an attributed error in the publication.

Distinguish a universal quantifier from a finite collection of examples. State the intended property and the domain on which a proof, counterexample, or numerical probe would bear.

### Check prerequisites and transformations

Assess whether each reviewed step preserves the declared claim, and name any additional assumption introduced. Checks may concern nonzero divisors, invertibility, positivity, regularity, interchange of limits/integrals, operator domains, boundary terms, and branch choices, where applicable.

Separate an inspected derivation from a formal proof verified by an implemented proof system. Numerical sampling or exact checks at particular inputs do not establish a general identity; inability to verify a step is not a demonstrated contradiction.

### Check physical structure within the declared regime

Propose dimensional and quantity compatibility, scalar/vector/tensor compatibility, sign/reference conventions, boundary/initial-condition compatibility, limiting cases, and conservation or balance checks when the governing model and system boundary justify them.

Passing dimensional checks does not select a coefficient, establish an equation's empirical adequacy, or resolve omitted interactions. A balance residual cannot be called a conservation-law violation before declared boundary fluxes, sources/sinks, storage, measurement uncertainty, and relevant model assumptions have been examined.

Record these as property-specific assessments with evidence and limits. Do not assume that every model shares the same invariances, equilibrium conditions, closure rules, or conserved quantities.

### Separate analytical, numerical, and empirical examinations

- **Analytical examination:** reviewed logic and derivation under explicit hypotheses; distinguish a proof sketch, a checked finite calculation, and a complete formal result.
- **Numerical examination:** executable/state references, inputs, precision, tolerances, step sizes, and sensitivity or convergence probes; no such probe alone proves analytical correctness.
- **Empirical examination:** predictions linked to actual observations with compatible quantities, calibration information, uncertainty models, and operating conditions; synthetic fixtures must not be reported as measurements of nature.
- **Assessment:** attributed implications of the above results, including unresolved alternatives; not an automatic upgrade of a criterion result into universal model validity.

Implementation error, numerical error, uncertain inputs, measurement error, omitted interactions, and scope mismatch remain candidate explanations rather than a forced taxonomy or automatically selected cause.

### Report a scoped conclusion

State the exact property established or not established, examined domain/state, evidence, remaining gaps, and what could discriminate among explanations. Keep “criterion met,” “criterion not met,” “indeterminate,” and “not evaluated” distinct from claim support and decisions.

## Proposed initial synthetic demonstrations

These are manually specified planning fixtures, not run results, benchmarks, physical experiments, or a claim that their checks are automated.

| Proposed fixture | Intended distinction | Expected evidence obligation |
|---|---|---|
| Cancel a factor in `x²/x = x` | The cancellation requires `x != 0`; it does not define the original expression at zero | Preserve the original domain and the additional condition; report zero as undefined for the original expression |
| Infer a universal identity from finitely many matching samples | Agreement at sampled inputs is not a universal proof | Retain sample/domain references and an explicitly limited numerical finding; construct a separate counterexample where applicable |
| Inspect two dimensionally compatible expressions with different coefficients | Dimensional compatibility alone cannot determine the coefficient | Record the dimensional result separately from absent derivation or empirical evidence |
| Compute a residual with missing covariance | Residual availability and uncertainty availability can differ | Retain an ordinary residual when valid; leave combined uncertainty unavailable unless its assumptions are supplied |
| Compare a model and measurement with mismatched units or quantities | A numerical difference is not meaningful until compatibility is established | Block the unsupported calculation and retain original input declarations |
| Reuse a passing calculation after an unreviewed equation/configuration change | Previous verification is bound to its examined state | Preserve the old result and mark current applicability unknown, rather than silently passing the new state |
| Observe a discrepancy in an incompletely specified open-system balance | Missing flux/storage information is not automatically a violation or proof of an omitted cause | Preserve missing terms and competing explanations |

Any synthetic expected outcome must be justified independently of the code under test. A generated expected answer and generated implementation agreeing is not independent evidence of correctness.

## Proposed implementation boundary

Start with evidence capture, scope declarations, reviewed mathematical steps, property-specific assessments, and synthetic fixtures. The Python-standard-library constraint remains in place; do not silently install a symbolic algebra package or imply support for arbitrary equation parsing and proof.

A first bounded implementation could support structured/manual declarations and a small set of explicit, tested arithmetic and dimensional operations after the relevant design gates are settled. General symbolic simplification, theorem proving, arbitrary differential-equation solving, and live physical measurement integration remain unestablished capabilities, not promises made by this scope decision.

Proceed under the approved independent start; this permission does not establish baseline compatibility. The next active review is E-02 through E-04 and V-01 through V-03, with N-01 and N-02 prioritized as prerequisites for any numerical calculations; N-03 is needed before transition probing, and integration choices remain explicit.
