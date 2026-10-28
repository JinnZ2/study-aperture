# Scoped assessment: neutrino oscillations in the Tolman VI spacetime

This is a first worked study run of Study Aperture's mathematical/physics evidence workflow, with a draft criterion-to-conclusion mapping contract and bounded offline calculations. It finds a candidate internal sign discrepancy in selected phase expressions, while preserving passing algebraic/numerical checks and unresolved scientific questions separately; it does not pronounce the whole paper correct or incorrect.

## Study identity and what “today” means

The selected paper is Daniele Gregoris, “Neutrino oscillations inside ultrarelativistic matter: on the role of the Tolman VI spacetime,” The European Physical Journal C 86, article 1238, explicitly published October 27, 2026 ([publisher article](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). “Today” here means October 27 in America/Chicago; acquisition and execution timestamps can fall on October 28 UTC.

This is a journal-publication date, not a claim that the work first became public that day; the publisher also identifies a preprint, which was not inspected in this pass ([publisher record](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). The article is classified as theoretical physics and declares no associated new data or software, so this run must not be presented as an empirical neutrino experiment ([article classification and availability statements](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)).

An initially promising SQUID candidate was not used: its news story says the research was published “today,” but the journal record says October 26, 2026 ([October 27 news story](https://phys.org/news/2026-10-quantum-sensor-loop-magnetic-medicine.html), [journal publication record](https://doi.org/10.1103/wc1k-wxtc)). That discrepancy is a source/date distinction, not evidence against the SQUID research.

## Materials, execution, and limits

The inspection covered the publisher's HTML text, publication metadata, selected original HTML TeX, stated assumptions, unit/coordinate notes, and availability statements; a subsequent visual inspection examined the original PDF's pages 4–5, but not the full derivations or cited background literature ([inspected article and linked PDF](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). The original TeX for equations 1, 2, 7, 8, 11, 12, 13, and 14 is retained without formula repair in `source-extract.json`; its PDF-uninspected limit is historical to that capture stage, while `pdf-inspection.json` records the later examination and exact PDF digest.

The fixed local program uses only Python's standard library, exact `Fraction` arithmetic for coefficient identities, and composite Simpson quadrature for selected integrals. It executes locally authored comparison functions, not code supplied by the paper, and needs no network when rerun against the captured extract.

The general offline integrity checker remains at version 0.2.0 and still performs no mathematical or empirical validation. Mathematical/numerical examination below comes from this case-specific authoring procedure; the proposed general criterion mappings remain `DRAFT_NOT_EXECUTABLE`.

## Separate assessment lanes

| Property examined | Criterion outcome | Scoped finding | Not established |
|---|---|---|---|
| Equation 2 coefficient identities at \(a=7/4\) | MET | Exact rational coefficients give isotropic pressure, \(p=\rho/3\), and zero trace coefficient | Einstein-tensor derivation, existence of an astrophysical realization, or empirical radiation-fluid identification |
| Literal equation 8 difference versus equation 12 | NOT_MET at all three selected trials | Opposite signs at admissible small-parameter inputs; candidate internal sign discrepancy | Its root cause, a global repair, or the effect on every later physical conclusion |
| Equation 12 quadrature versus equation 13 endpoint expression | MET at the three selected trials | Agreement within the declared absolute tolerance \(10^{-10}\) | A universal symbolic identity or correctness of the preceding approximation step |
| Complete dimensional/quantity review | INDETERMINATE | Coordinate and unit normalization was not fully restored | Either a dimensional pass or a dimensional failure |
| Empirical support for the proposed neutrino signature | NOT_EVALUATED | No new physical measurement was performed in this audit | Either empirical confirmation or empirical contradiction |

These are separate attributed assessment results, not votes to be averaged. In particular, agreement between equations 12 and 13 does not repair an inconsistency between equations 8 and 12.

### Exact mathematical subcheck

The paper gives \(\rho=(a-1)/(ar^2)\), \(p_r=(2-a)/(ar^2)\), and \(p_t=1/(4ar^2)\), and identifies \(a=7/4\) as the isotropic, tracefree specialization ([equation 2 and discussion](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). Removing the defined common factor \(1/(ar^2)\) for this positive \(a\) and \(r>0\), the locally checked exact coefficients are \(3/4,1/4,1/4\); hence \(p_r=p_t=\rho/3\) and \(-3/4+1/4+2(1/4)=0\).

This establishes an algebraic identity within the supplied expressions. It does not independently derive those expressions from the metric or establish their empirical applicability.

### Candidate sign discrepancy

The paper defines \(\Phi_{kj}=\Phi_k-\Phi_j\) and \(\Delta m^n=m_k^n-m_j^n\), and writes the equation 8 phase as a massive square root minus the common massless square root ([equations 7, 8, and definitions following equation 13](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). Define \(q(r)=E^2/r-L^2/r^2\), with \(q>\max(m_k^2,m_j^2)\).

Taking the literal difference of equation 8 for species \(k\) and \(j\) cancels the massless term, leaving

\[
\Phi_{kj}^{(8)}
=\sqrt a\int_{r_A}^{r_B}
\left[\sqrt{q-m_k^2}-\sqrt{q-m_j^2}\right]\,dr.
\]

At positive \(\Delta m^2\), this integrand is negative. A direct Taylor expansion gives the conditional comparison

\[
\sqrt a\left[
-\frac{\Delta m^2}{2\sqrt q}
-\frac{\Delta m^4}{8q^{3/2}}
+O\!\left(\frac{m_k^6+m_j^6}{q^{5/2}}\right)
\right].
\]

The publisher's equation 12 instead has a positive quadratic term and a negative quartic term under the stated mass ordering ([published equation 12](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). Both signs were checked against original publisher HTML TeX and visually against the PDF's page 5, with the phase ordering checked on page 4; no difference in these selected signs was observed between HTML and PDF.

No source expression was silently changed. The negative-leading Taylor expression is separately labeled as this review's conditional comparison, not an author-approved correction.

A global phase reversal would reverse both the quadratic and quartic terms, whereas the literal discrepancy here is not the reversal of both. A consistent convention review therefore needs to trace the expansion rather than automatically changing an overall sign.

## Recorded numerical results

The first local trial uses \(a=7/4\), \(E=10\), \(L=1\), \(m_k=0.2\), \(m_j=0.1\), and \(r\in[1,2]\). These are model-coordinate test numbers, not measured neutrino parameters or asserted SI values.

| Locally executed quantity | Recorded value |
|---|---:|
| Equation 8 flavor-phase difference, 1024 Simpson subintervals | \(-0.002427511648255096\) |
| Published equation 12 expansion, same interval | \(+0.002426578278248313\) |
| Equation 12 minus equation 8 | \(+0.004854089926503409\) |
| Equation 13 endpoint result | \(+0.002426578278248316\) |
| Absolute equation 13 versus equation 12 difference | \(3.47\times10^{-18}\) |
| Maximum local expansion parameter \(m^2/q\) | \(8.0402\times10^{-4}\) |
| Equation 8 quadrature change, 512 to 1024 subintervals | Approximately \(4.51\times10^{-17}\) |

Two additional trials, including a radial \(L=0\) case, retain the opposite-sign finding and equation 12/13 sampled agreement. All three maximum \(m^2/q\) values are below \(10^{-3}\), and the computations stay away from the singular center and square-root turning points.

For cancellation resistance, equation 8's difference is evaluated using

\[
\sqrt{q-m_k^2}-\sqrt{q-m_j^2}
=\frac{m_j^2-m_k^2}{\sqrt{q-m_k^2}+\sqrt{q-m_j^2}}.
\]

The run also records a conditional Taylor remainder bound on each selected interval. That analytical truncation bound is not a complete floating-point or quadrature error certificate, and convergence across three step counts is a diagnostic rather than a rigorous interval proof.

## Physics scope and unresolved explanations

The article assumes a static spherically symmetric metric, uses an eikonal/WKB treatment, adopts natural-unit conventions, and notes a rescaling of the time coordinate ([model, approximation discussion, and notes 2–3](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). A careless unrescaled SI-unit check would therefore not justify declaring its metric dimensionally wrong.

The paper explicitly treats coherence and a short-wavelength approximation and discusses a curvature singularity at \(r=0\) ([approximation and singularity discussion](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). Whether those approximations remain controlled in the region relevant to the proposed singularity signature requires a wider review; this run does not answer that question by extrapolating its nonsingular test inputs.

Candidate explanations for the equation discrepancy remain unresolved: a printed sign error, a phase-order/convention mismatch, an authoring transcription or implementation mistake, or a substantive derivation problem. The selected PDF signs agree with HTML; the next discriminating checks are a preprint comparison, an independent derivation with the same phase ordering, and tracing any corrected convention through the spinoptics terms and probabilities, and no author contact was made.

An overall sign change can leave some squared-probability expressions unchanged, but that observation would not by itself settle interference with other terms. The present run does not claim that the identified discrepancy necessarily invalidates the observational proposal.

No existing classical energy/momentum/entropy anchor was forced onto this relativistic model. The case includes no registered general-relativity anchor application, so zero anchor-coverage rows must not be misread as successful physics-law coverage.

## Evidence integrity, corrections, and verification

The final evidence bundle contains 16 records: eight source equations, three numerical-run observations, and five property-specific assessments. Authoring-only JSON Schema review accepted their shapes; that is separate from the runtime checker's result and does not validate their scientific contents.

The runtime integrity report records zero ERROR findings and 19 UNKNOWN findings: unresolved source references and unresolved trial records remain explicit. The broader source, artifact, experiment, and verification registries are not implemented; the sidecar provenance/hash manifest is not a replacement for authenticated registry records.

The first generated bundle had six reference-format errors because three trial references were incorrectly encoded as text values. Its artifacts are retained under `attempt-01-invalid-trial-references/`; `correction-record.json` links them to the corrected bundle, whose three properly formed but unresolved trial references increase the UNKNOWN count rather than fabricating successful provenance.

The initial corrected HTML-only run is retained separately under `attempt-02-html-only/`. The final case-review-2 records add the PDF inspection and updated limitations without changing calculated values or silently rewriting the earlier evidence stage.

All 19 bounded case tests, the existing 100 checker tests, and five existing toolkit self-tests passed in the recorded environment. These are tests authored alongside the implementation, not independent verification; the case also remains explicitly unresolved in the original Study Aperture record/report.

The offline procedure, source extract, draft mappings, numerical outputs, machine-readable assessments, toolkit record, correction history, and hashes are supplied together. Prototype 0.1 compatibility remains UNKNOWN, voice is DEFERRED, and neither full requirements conformance nor a whole-paper scientific verdict is established.

## Scoped outcome

This study run demonstrates that the toolbox can preserve a useful mixed result: a valid algebraic subcheck, a candidate internal discrepancy, an independently coded sampled agreement, and unperformed or indeterminate examinations. The justified next step is to investigate the specific sign/ordering issue and approximation domain, not to label the entire publication “verified” or “debunked.”
