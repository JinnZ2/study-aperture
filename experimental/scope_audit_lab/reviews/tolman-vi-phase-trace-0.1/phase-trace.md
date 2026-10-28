# Tolman VI follow-up: from phase convention to survival probability

This follow-up distinguishes a harmless complete phase reversal from a change to the relative eikonal/spin contributions. Under the paper's stated two-flavor formula, the former is invariant and the latter generally is not; the sign discrepancy cannot be dismissed as automatically harmless without a consistent rederivation of both contributions.

It also finds that full phase averaging alone gives \(1-\tfrac12\sin^2(2\theta)\), not a universal survival probability of one-half. These are restricted mathematical implications, not an established correction to the paper's physical prediction, a measured effect, or a whole-publication verdict.

## Source lineage and what was inspected

The study is Daniele Gregoris, “Neutrino oscillations inside ultrarelativistic matter: on the role of the Tolman VI spacetime,” published in The European Physical Journal C on October 27, 2026 ([publisher article](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). Its preprint is arXiv:2610.11319v1, submitted October 8, 2026, so October 27 is the journal-publication date rather than first public disclosure ([arXiv version history](https://arxiv.org/abs/2610.11319)).

The selected preprint formulas preserve the same phase ordering, equation 8 square-root ordering, equation 12 sign pattern, boost phase, and survival probability as the journal HTML ([versioned preprint](https://arxiv.org/html/2610.11319v1), [journal article](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). This is a selected-equation comparison, not a whole-paper semantic diff, and the two versions are not independent scientific confirmations.

Original journal PDF pages 9–10 were rendered and visually inspected for equation 35, the direction-reversal footnote, and the phase-averaging passage ([publisher's article and linked PDF](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). The PDF and HTML share the relevant mixing-angle factor and averaging claim; the exact visual-inspection event time was not instrumented and remains MISSING rather than reconstructed.

The earlier review, code, tests, and artifacts are retained unchanged. This follow-up has its own namespace, procedure version, selected-source capture, source lock, computed outputs, assessments, and verification manifest.

## Trace of the published definitions

The paper defines the relative phase as \(\Phi_{kj}=\Phi_k-\Phi_j\), introduces the sum of eikonal and spin contributions, gives the logarithmic boost phase, and uses that sum in the two-flavor survival probability ([equations 7, 22, 32, and 35](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). The relevant chain is:

| Source object | Role in this trace |
|---|---|
| Equations 7–8 | Relative-phase ordering and literal eikonal integral |
| Equations 12–13 | Published mass expansion and its integrated expression |
| Equation 22 | Addition of eikonal and spin phases |
| Equations 29–32 | Spin expectation-value difference and boost phase |
| Equation 35 | Conversion of total relative phase into survival probability |

For compactness, write \(F=\Phi_{kj}^{\mathrm{eik}}\), \(S=\Phi_{kj}^{\mathrm{boost}}\), and \(M=\sin^2(2\theta)\). Then equation 35 is

\[
P(F,S)=1-M\sin^2\!\left(\frac{F+S}{2}\right).
\]

The manuscript switches between \(ij\) in the boost numerator and \(kj\) on the phase label ([equations 29–32](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). For the sample implementation we explicitly identify \(i=k\), and also retain the reversed spin orientation as a sensitivity branch; that does not claim the author endorses both alignments or resolve spin transport from first principles.

### Derivation from amplitudes

Within a coherent, unitary, real two-state mixing model, let the same-flavor amplitude be

\[
\mathcal A_{\alpha\alpha}
=\cos^2\theta\,e^{i\phi_k}
+\sin^2\theta\,e^{i\phi_j}.
\]

Taking its squared modulus gives

\[
|\mathcal A_{\alpha\alpha}|^2
=\cos^4\theta+\sin^4\theta
+2\cos^2\theta\sin^2\theta\cos(\phi_k-\phi_j)
=1-\sin^2(2\theta)\sin^2\!\left(\frac{\phi_k-\phi_j}{2}\right).
\]

This derives the dependency being tested rather than presuming that any sign discrepancy must affect an observable. A separate complex-amplitude implementation agrees with the compact expression at the recorded test inputs.

For this unitary two-flavor model, transition probability is \(1-P\), so a survival-probability change corresponds to an equal-magnitude, opposite-sign transition-probability change. Absorption, three-flavor evolution, matter-dependent transport, and detector response are outside this derivation.

## Which sign changes cancel?

A common phase applied to both mass states cancels from \(\phi_k-\phi_j\). Reversing the entire relative phase also leaves this two-flavor probability unchanged:

\[
P(-F,-S)=P(F,S).
\]

This is consistent with the paper's simultaneous phase reversal for path-direction reversal, rather than a challenge to that symmetry ([footnote 14 and equation 35](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). Relabeling both species consistently similarly reverses all relevant differences.

Reversing only \(F\), while retaining \(S\), is different. Direct use of the trigonometric identities gives

\[
\boxed{P(-F,S)-P(F,S)=M\sin F\,\sin S.}
\]

That expression is not generally zero. It vanishes in special cases, including zero mixing amplitude or suitable zeroes of the phase sines, but no such cancellation may be silently assumed.

As an algebraic example only, \(\theta=\pi/4\) and \(F=S=\pi/2\) give \(P(F,S)=0\) and \(P(-F,S)=1\). This demonstrates dependence of the formula; it does not establish that these phase values are realized by the paper's metric or any physical instrument.

### Why the quartic term matters even without spin

At the admissible trial inputs, write the positive quadratic contribution as \(F_2\) and the positive magnitude of the quartic contribution as \(F_4\). The published expansion has \(F_{\rm pub}=F_2-F_4\), whereas the literal equation 8 difference expands as \(F_{\rm lit}=-F_2-F_4\) under the stated mass ordering ([equations 7–13](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)).

Consequently, the two expressions are not exact global negatives at retained quartic order. With spin omitted, the conditional quartic comparison gives

\[
P(-F_2-F_4,0)-P(F_2-F_4,0)
=-M\sin F_2\,\sin F_4.
\]

At leading quadratic order alone, with spin also omitted, the sign does cancel. That restricted cancellation cannot establish equivalence of the complete expressions.

## Fixed numerical branch comparison

The three original nonsingular trials were reused with explicitly chosen \(\theta=\pi/6\). These are model-coordinate numbers, not calibrated SI neutrino parameters; the computation does not reproduce the paper's figures or assert measurement sensitivity.

For the first trial, \(a=7/4\), \(E=10\), \(L=1\), \(m_k=0.2\), \(m_j=0.1\), and \(r\in[1,2]\). With the illustrative identification \(\Delta m_{ij}=m_k-m_j\), the retained quantities are:

| Formal model quantity | Local result |
|---|---:|
| Published equation 13 eikonal phase \(F\) | \(+0.002426578278248316\) |
| Literal equation 8 relative phase | \(-0.002427511648255096\) |
| Published equation 32 boost phase \(S\) | \(+0.0003742642983116734\) |
| \(P(F,S)\) | \(0.9999985291161231\) |
| \(P(-F,-S)\), complete convention reversal | \(0.9999985291161231\) |
| \(P(F_{\rm Eq8},S)\), conditional eikonal substitution | \(0.9999992095331502\) |
| Conditional substitution minus published value | \(+6.80417\times10^{-7}\) |
| Eikonal-only literal/source probability difference | Approximately \(-8.4950\times10^{-10}\) |

Keeping the opposite spin orientation changes the conditional probability difference to approximately \(-6.82116\times10^{-7}\). Neither sensitivity branch is automatically designated as the corrected physical prediction.

The small differences in these particular examples do not establish that the discrepancy is experimentally negligible or detectable. Such a judgment needs physical normalization, valid propagation conditions, instrument response, uncertainty, and a specified observation model.

## Phase averaging does not generically imply equal flavor probability

The paper replaces the oscillatory sine-squared factor by its rapid-phase average, then states equal probability of measuring any flavor; its inspected passage does not set \(\theta=\pi/4\) ([section 5, equation 35, and footnote 17](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)). Retaining the equation's mixing factor yields instead

\[
\boxed{\langle P\rangle
=1-\frac12\sin^2(2\theta).}
\]

This equals one-half at maximal mixing, but not for arbitrary fixed \(\theta\). The local analytical and quadrature checks give:

| Mixing angle | Fully phase-averaged survival |
|---|---:|
| \(0\) | \(1\) |
| \(\pi/12\) | \(0.875\) |
| \(\pi/8\) | \(0.75\) |
| \(\pi/6\) | \(0.625\) |
| \(\pi/4\) | \(0.5\) |

Dephasing alone preserves the mass-state populations \(\cos^2\theta,\sin^2\theta\), leaving survival \(\cos^4\theta+\sin^4\theta\). It does not automatically produce a maximally mixed state or establish population equilibration.

An additional maximal-mixing assumption, specified population-changing dynamics, or another independently justified mechanism could change this inference. None is silently supplied by this review, and the result is not an empirical disproof of flavor equilibration in all physical environments.

## A divergent phase is not an averaging prescription

For a specified normalized averaging weight, the more general expression is

\[
\langle P\rangle
=1-\frac M2+\frac M2\operatorname{Re}\langle e^{i\Phi}\rangle.
\]

Full phase averaging requires the last characteristic factor to vanish. A divergent pointwise phase does not itself specify a response kernel or guarantee that condition, and the unaveraged oscillatory probability need not have a pointwise limit.

For example, averaging uniformly over a phase window of width \(W\) centered at \(\Phi_0\) gives

\[
\langle P\rangle_W
=1-\frac M2+\frac M2
\frac{\sin(W/2)}{W/2}\cos\Phi_0,
\]

with the continuous zero-width limit retained. Uniform weighting over a full \(2\pi\) phase period gives the complete average, whereas a narrow window generally retains phase dependence.

### Explicit response-kernel counterexample

As an ideal mathematical counterexample, take \(\Phi(r)=C\ln(r/r_A)\) and average uniformly in radius over \(0<r<\epsilon\). Direct integration gives

\[
\langle e^{i\Phi}\rangle
=\frac{(\epsilon/r_A)^{iC}}{1+iC},
\qquad
\left|\langle e^{i\Phi}\rangle\right|
=\frac{1}{\sqrt{1+C^2}}.
\]

For fixed nonzero \(C\), that magnitude does not go to zero as \(\epsilon\to0\), despite the divergent phase. At \(C=1\) and \(\theta=\pi/6\), the two shrinking-window subsequences \(\log(\epsilon/r_A)=-2\pi n\) and \(-(2n+1)\pi\) give averages \(0.8125\) and \(0.4375\), respectively, rather than convergence to \(0.625\).

The kernel is not a claimed detector model, and this is not an extrapolation of the validated numerical trials to a physical curvature singularity. It shows why “the phase diverges, therefore every measurement is fully averaged” requires an explicit additional measurement/ensemble argument.

## What follows, what remains open

The sign issue cannot automatically be dismissed as a global convention: the relative spin/eikonal sign and retained higher-order terms can affect the formal two-flavor probability. But this follow-up has not determined whether equation 8, the later expansion, spin transport, or a convention definition should be revised.

The equal-probability claim also needs an explicit additional premise beyond phase averaging in equation 35. Maximum mixing or an independently established population-equilibration process would be materially different from averaging a phase at arbitrary fixed mixing.

No measured probability, observable exclusion, detector resolution threshold, formal proof of the entire paper, or empirical singularity signature was established. WKB/coherence control near the singularity, physical normalization, and a finite response model remain unresolved.

## Execution and evidence integrity

The standard-library offline runner records the original and conditional branches without editing source equations or automatically selecting a correction. The final phase-trace-0.1.1 procedure creates 21 typed records: ten source equations, three original local derivations, three numerical-run observations, and five restricted assessments.

The runtime integrity checker reports zero ERROR findings and 24 UNKNOWN findings, preserving missing source/trial registry links. It still performs no mathematical/empirical validation, invokes no generic mapping executor, and contains no registered general-relativity anchor application in this case.

The initial package's three analytical criteria lacked evidence links and failed the separate schema review despite its narrow-integrity and test results; that stage is retained under `attempt-01-missing-derivation-links/`. The correction adds actual step-by-step derivation records, rather than padding the criteria with unrelated references, and preserves the original shape review and verification history.

All 27 new trace tests, the unchanged 19 original case tests, the 100 checker tests, and five existing toolkit self-test commands pass in the final recorded environment. A fresh isolated offline rerun reproduces the deterministic computed/evidence/report artifacts; this is same-process authoring verification, not independent scientific reproduction.

Source/execution hashes, selected preprint/journal expressions, mathematical counterexamples, conditionally computed values, limitations, and test logs are retained together. Prototype 0.1 compatibility remains UNKNOWN, voice remains DEFERRED, and full baseline conformance remains unestablished.
