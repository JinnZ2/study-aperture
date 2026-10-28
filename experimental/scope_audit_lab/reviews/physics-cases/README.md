# Physics-case review of mathematical evidence draft 0.1

Status: Authoring review with synthetic calculations, not implementation of a runtime validator. Prototype 0.1 compatibility remains UNKNOWN, voice remains DEFERRED, and the evidence schema remains unchanged.

## Assessment

Retain the five distinct record types and explicit missingness conventions. The draft is useful for recording a human assessment, but it is not a sufficiently structured input contract for automatic physical judgments: dimensions, units, mathematical types, boundary conditions, and uncertainty are currently descriptive text, while observations are scalar-numeric. See the [examined schema guide](../../schemas/draft-0.1/README.md) and [schema](../../schemas/draft-0.1/evidence.schema.json).

This is a distinction between expressibility and computability. A reviewer can already record the cases below in text and attach artifacts; the absence of machine-readable structure does not make the evidence unrecordable, but an automated checker must not fill that structure by guessing.

The recommendation is a staged extension proposal, not adoption of a new schema or closure of the [open design choices](../../docs/decision-checklist.md). Do not build a broad “physics correctness” validator from these examples.

## Review method and artifacts

- **Examined state:** [results.json](results.json) records hashes of the unchanged schema, original synthetic examples, baseline requirements, and the calculation script.
- **Calculations:** [compute_review.py](compute_review.py) performs only the disclosed synthetic arithmetic using Python's standard library. It does not parse or validate equations, resolve evidence references, inspect instruments, or select causes.
- **Structural boundary probes:** [probe_schema.py](probe_schema.py) and [schema-probes.json](schema-probes.json) distinguish structural acceptance from the unperformed mathematical checks. The probe script needs a separately authorized authoring-only JSON Schema reviewer, not a lab runtime dependency.
- **Reproduction:** Run `python3 compute_review.py` from this directory and inspect its JSON output. Floating-point values can vary with the Python/platform math implementation; the exact fraction comparisons do not carry that trigonometric limitation.

The reviewed physical references explain established concepts, not the empirical performance of this instrument. All numerical values below are authored synthetic fixtures; none is a measurement from those references.

The two JSON outputs are supplementary authoring formats, not five-type evidence-schema instances or a proposed exchange interface. Their local `UNAVAILABLE` calculation marker is not an addition to the draft schema's missing-value vocabulary.

### Execution record

The arithmetic output reproduced exactly on a second run in the same environment. Targeted authoring assertions checked dimension equality/inequality, missing-storage propagation, conditional residual signs, zero-denominator handling, inclusive threshold comparisons, distinct absolute/relative criteria, conditional uncertainty arithmetic, and the acceptance of both structural boundary probes.

The structural reviewer used `jsonschema` 4.26.0 and `rfc3339-validator` 0.1.4 from a temporary directory outside the repository, with active date-time format checking explicitly confirmed. No dependency was added to the project; repeat the structural probes only in a separately prepared authoring environment.

The existing parent toolkit's `assess.py selftest` and the selftests of the four vendored scripts each returned `SELFTEST OK`. Those five existing-toolkit checks are distinct from this review, not results for the unimplemented lab acceptance matrix; local Markdown targets and Git whitespace checks were also checked.

## Dimensional consistency is a limited property

### P-01: An incompatible equation and an undetermined coefficient

Declare \(E\) to have dimensions \(ML^2T^{-2}\), \(m\) to have dimensions \(M\), and \(v\) to have dimensions \(LT^{-1}\). Then \(E=mv\) has incompatible dimensions, whereas \(E=c\,mv^2\) is dimensionally consistent for every dimensionless \(c\); these statements follow directly from the declared exponent arithmetic.

An assessment of the first equation can establish a dimensional discrepancy under those declarations. An assessment of the second cannot determine the coefficient, establish an empirical law, or select a physical interpretation merely because the exponents match.

- **Current representation:** Record declarations in each symbol's dimensions/units/type fields, then retain the examiner's calculation as an artifact. Structural acceptance is not evidence that any exponent calculation occurred.
- **Proposed extension:** Optional structured dimension signatures with a declared basis/system, rational exponents, provenance, and explicit missing states. Preserve original source notation rather than replacing it with normalized notation.
- **Planned adversarial check:** A dimensionally consistent but otherwise unsupported equation must not acquire a “correct physics” verdict.

### P-02: Equal dimensions do not establish comparable quantities

Moment of force and energy conventionally have the same dimension but are not the same kind of quantity, as explicitly distinguished by the [BIPM vocabulary of metrology](https://jcgm.bipm.org/vim/en/1.2.html). Consequently, matching dimension vectors is insufficient grounds for treating a torque record as an energy observation.

- **Current representation:** The draft keeps mathematical type, quantity, dimensions, units, and conventions separate, but as free-form declarations.
- **Proposed extension:** Quantity-kind and representation declarations, including scalar/vector/tensor shape and frame where relevant, separately from dimension and unit declarations.
- **Planned adversarial check:** Preserve incompatible or ambiguous quantity kinds even when their dimensions agree. A missing kind is an unknown, not permission to coerce.

## Conservation assessment depends on the system boundary

### P-03: Apparent excess output with unmeasured storage

A control-volume energy balance must account for energy transfer, including that carried by mass crossing the boundary; MIT's [control-volume treatment](https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node19.html) explicitly separates these contributions. For this synthetic case, stipulate that \(P_{\rm in}\) and \(P_{\rm out}\) already include all relevant incoming and outgoing energy transfers for a declared fixed boundary.

Define the tested relation and residual as:

\[
\frac{dE}{dt}=P_{\rm in}-P_{\rm out},
\qquad
r=\frac{dE}{dt}-(P_{\rm in}-P_{\rm out}).
\]

Set the synthetic incoming rate to \(100\,\mathrm W\) and outgoing rate to \(120\,\mathrm W\). The storage rate required for zero residual is \(-20\,\mathrm W\), but the storage rate has not been measured in this fixture; the actual residual is therefore unavailable.

If one separately supplies a hypothetical storage rate of \(-20\,\mathrm W\), the conditional residual is zero. If instead one supplies zero storage rate, it is \(+20\,\mathrm W\); neither hypothetical value may replace missing evidence.

- **Current representation:** Boundary, scope, conditions, assumptions, and scalar values can be recorded, but there is no structured inventory of balance terms.
- **Proposed extension:** A balance specification with system/boundary identity, frame, time interval, storage/transfer terms, sign conventions, included/excluded contributions, units, and input references.
- **Planned adversarial check:** Missing storage is not zero storage. Neither excess output nor a zero residual automatically establishes a new source of energy, exhaustive accounting, or a cause.

### P-04: An equation cannot silently migrate between boundaries

The control-volume formulation and steady-state simplifications depend on the selected system and assumptions, as described in [MIT's conservation-law notes](https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node19.html). Changing the boundary or included transfers therefore requires a new scoped examination rather than automatic reuse of an earlier result.

- **Current representation:** Scope and version/state bindings can identify the change, but there is no term-level dependency checker.
- **Proposed extension:** Bind a balance assessment to the exact boundary definition, included-term inventory, and assumption states. Reassessment is required when a relevant dependency changes; age alone does not establish staleness.
- **Planned adversarial check:** An earlier passing balance cannot validate a later open-system equation merely because both records use the same equation label.

## Approximation boundaries require a specified error measure

### P-05: Small-angle pendulum approximation

The simple-pendulum treatment uses \(\sin\theta\approx\theta\) to obtain the linearized equation and its approximate period, with the angle expressed in radians; this dependency is described in [OpenStax's pendulum derivation](https://openstax.org/books/university-physics-volume-1/pages/15-4-pendulums). The review deliberately assesses only the replacement of sine, not the error in the resulting period or the adequacy of every pendulum assumption.

Define the illustrative metric:

\[
e(\theta)=\frac{|\theta-\sin\theta|}{|\sin\theta|}.
\]

The local calculation gives approximately \(0.5095\%\) at \(10^\circ\), \(1.1515\%\) at \(15^\circ\), and \(4.7198\%\) at \(30^\circ\). At zero, the absolute difference is zero but this relative metric is undefined because its denominator is zero; no continuous extension is silently substituted.

For a user-chosen inclusive rule \(e\leq 1\%\), the \(10^\circ\) case meets the rule and the \(15^\circ\) case does not. These are statuses of this metric and tolerance, not observations of a phase transition or universal model failure.

- **Current representation:** `APPROXIMATES`, scope, and criterion text can document the intended comparison, but do not define a computable error contract.
- **Proposed extension:** Identify reference expression, approximate expression, expansion variable, domain, angle convention, error formula, denominator, tolerance, inclusive/exclusive comparison, and applicable output quantity.
- **Executed authoring check:** Separate exact fraction comparisons cover below, at, and above an inclusive threshold in error space. They do not establish an exactly represented angular crossing, a period-error bound, or numerical solver accuracy.

The inspected [OpenStax text](https://openstax.org/books/university-physics-volume-1/pages/15-4-pendulums) also associates angles below \(15^\circ\) with a less-than-\(1\%\) comparison between sine and angle, without specifying the relative-error denominator in that statement. Preserve that as a source-reported quantitative statement rather than inheriting it as a verified tolerance guarantee: the synthetic \(14.5^\circ\) calculation exceeds \(1\%\) under the denominator explicitly defined here.

The source was directly inspected, and a bounded mathematical comparison was performed; no pendulum experiment or empirical replication occurred. The ambiguity in the source's error definition and its possible pedagogical rounding remain investigation notes, not automatically selected explanations.

### P-06: Absolute and relative criteria can disagree

Use the synthetic mathematical function \(F(\epsilon)=1/(1-\epsilon)\) and approximation \(A(\epsilon)=1+\epsilon\). For real \(\epsilon\neq1\), direct subtraction gives:

\[
F(\epsilon)-A(\epsilon)=\frac{\epsilon^2}{1-\epsilon}.
\]

On the declared interval \(|\epsilon|\leq0.1\), the absolute error is at most \(1/90\), while the relative error with denominator \(|F|\) is \(\epsilon^2\leq1/100\). At \(\epsilon=0.1\), an absolute tolerance of \(0.01\) is not met, while an inclusive relative tolerance of \(1\%\) is met.

- **Current representation:** Multiple criteria can coexist; a single undifferentiated approximation status would discard the distinction.
- **Proposed extension:** Store each error calculation and criterion separately with exact input references, method, denominator, units where applicable, and domain. If asymptotic-order notation is supplied, do not turn it into a numerical bound without additional evidence.
- **Planned adversarial check:** An approximation meeting one output's relative tolerance must not automatically meet an absolute tolerance or validate a different output.

## Derivations and uncertainty must preserve dependencies

### P-07: An absent initial condition cannot become a chosen solution

For the synthetic equation \(dy/dt=0\) on a connected interval, \(y=C\) describes the constant solutions. Selecting \(y=0\) requires an additional condition such as \(y(t_0)=0\); no missing initial condition licenses that selection.

- **Current representation:** Initial-condition scope, assumption references, and derivation steps can retain the requirement, but no checker propagates or discharges it.
- **Proposed extension:** Step-local domains, introduced assumptions, and explicit discharge/dependency rules. Adopt only a declared, limited proof or transformation system before implementing logical judgments.
- **Planned adversarial check:** A conditional derivation cannot become an unconditional theorem through omission of an assumption reference or a step marked `EQUIVALENT`.

### P-08: Missing covariance cannot become independence

For scalar random quantities with finite second moments, expanding the variance of \(Y-P\) gives \(\operatorname{Var}(Y-P)=\operatorname{Var}(Y)+\operatorname{Var}(P)-2\operatorname{Cov}(Y,P)\). This algebraic identity does not estimate the covariance or establish that the recorded uncertainties are standard deviations of the relevant distributions.

In the synthetic illustration, standard uncertainties of \(3\,U\) and \(4\,U\) yield \(5\,U\) for the residual only under an explicit zero-covariance assumption. A covariance of \(12\,U^2\) instead yields \(1\,U\); with covariance neither supplied nor justified, this chosen combined-uncertainty calculation remains unavailable.

- **Current representation:** Uncertainty is descriptive text and there is no structured covariance or shared-calibration model.
- **Proposed extension:** Uncertainty type, coverage information when relevant, input definitions, covariance/correlation dependencies, units, provenance, and calculation eligibility. Distinguish unknown from inapplicable rather than forcing either to zero.
- **Planned adversarial check:** No normalized residual is produced from an unknown or zero uncertainty denominator without an explicit, mathematically valid rule. A large residual does not select its cause.

## Recommended next schema work

Keep draft 0.1 and its example bytes intact. Proposed additions should be reviewed as a new draft; its version must not be confused with baseline requirements specification 0.2.

- **First priority, quantity and calculation contracts:** Structured dimensions/quantity kinds and a distinct calculation record, with methods, exact input references, missingness, units, and numerical limitations.
- **First priority, scoped physics checks:** A balance-term specification and approximation/error contract covering the cases above. These are narrower and more inspectable than an automatic verdict about physical validity.
- **Next priority, dependence:** Assumption propagation, boundary/state changes, and structured uncertainty inputs. Preserve the option to report an unsupported calculation rather than implementing speculative arithmetic.
- **Later support, richer observations:** Vectors, tensors, fields, and time series with temporal/spatial support and frame information. Until supported, retain original artifacts rather than manufacturing scalar measurements.

Use three reporting layers: structural eligibility, an explicitly named mathematical or numerical property, and physical adequacy relative to purpose/evidence. A finding in one layer cannot silently promote another; empirical adequacy can remain unresolved even when every implemented structural and arithmetic check passes.

## What was and was not established

The attached arithmetic was executed locally and its output retained. The separate structural probes were also executed in an authoring-only reviewer environment; their scoped results are documented in [schema-probes.json](schema-probes.json).

No Scope Audit Lab acceptance-matrix tests were implemented or executed. No physics experiment, symbolic proof system, uncertainty estimator, unit conversion engine, general semantic validator, prototype compatibility test, or voice instrument was implemented or validated.
