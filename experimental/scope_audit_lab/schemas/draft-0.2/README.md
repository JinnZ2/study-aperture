# Scoped physics evidence extensions, draft 0.2

Status: Proposed additive schema draft, with authoring-only structural review. This is not baseline requirements specification 0.2 conformance, a runtime audit engine, an approved stable interface, or empirical validation.

Prototype 0.1 compatibility remains UNKNOWN and voice remains DEFERRED. Draft 0.1's schema and original five examples are preserved; their schema IDs and version numbers are not relabeled.

Evidence schema draft 0.1 and the uninspected Prototype 0.1 are different artifacts. Preserving the former does not establish compatibility with the latter.

## Design answer: reference laws with explicit scope gates

Use known physical laws as sourced reference constraints, not as unqualified verdicts. A reference formulation, its required conditions, a model's actual conditions, a numerical comparison, and the interpretation of that comparison must remain separate objects.

This draft adds six supporting record types in [extensions.schema.json](extensions.schema.json). It retains draft 0.1's five mathematical evidence types, including the separation between an observation, a calculation, and an assessment; the additive `calculation` type fills the previously documented calculation-record gap.

- **quantity_definition:** Declares quantity kind, structure, a seven-base dimension signature, unit role, and scope. A declaration is not a measurement or an automatically verified unit conversion.
- **calculation:** Records an explicit method, version/state-bound input references, prerequisites, execution status, result, units, uncertainty dependencies, and assessment references.
- **balance_specification:** Records a particular boundary, frame, storage/transfer inventory, sign convention, and scoped relation. Included, excluded, and unknown terms remain distinguishable.
- **approximation_specification:** Identifies reference and approximate expressions, target output, domain, error denominator, zero policy, tolerance, criterion version, and supporting bound evidence.
- **physics_anchor:** Stores a sourced reference formulation, conditions, formalism, exclusions, and application hazards. Editorial restrictions are marked separately from source-explicit requirements.
- **anchor_application:** Maps a specific subject to an exact anchor version, records condition-by-condition examination, and separates applicability from comparison results.

These are supporting records, not replacements for claim, model, source, artifact, verification, or interpretation registries. Those broader schemas and the corresponding runtime components remain unfinished.

## Starter reference anchors

The [example bundle](../../examples/schema-draft-0.2/records.json) contains three editable, source-backed reference formulations rather than a complete catalogue. Their titles and citations do not establish their applicability to any particular model or observation.

### Energy balance

The fixed-control-volume reference separates stored-energy change, heat/work transfer, and energy carried by incoming and outgoing mass, following the [MIT energy-conversion lecture](https://ocw.mit.edu/courses/2-60j-fundamentals-of-advanced-energy-conversion-spring-2020/54a791b898a31befeea178f796efcd9c_MIT2_60s20_lec2.pdf). Its sign convention is heat into the volume positive and work out positive; flow enthalpy already incorporates flow-work accounting in that formulation ([MIT lecture](https://ocw.mit.edu/courses/2-60j-fundamentals-of-advanced-energy-conversion-spring-2020/54a791b898a31befeea178f796efcd9c_MIT2_60s20_lec2.pdf)).

This starter deliberately restricts its expression to a fixed boundary, classical continuum accounting, and the displayed uniform-\(g\) potential specialization. Other formulations are not declared incorrect; they require another explicitly sourced reference or a justified transformation.

### Linear momentum balance

The material-system reference is \(d\mathbf P/dt=\sum\mathbf F_{\rm external}\) in an inertial frame, using [MIT's material-volume formulation](https://web.mit.edu/2.25/www/pdf/fundamental_laws.pdf). The familiar \(\mathbf F=m\mathbf a\) form is a constant-mass specialization, as distinguished in [NASA's momentum explanation](https://www.grc.nasa.gov/WWW/K-12/BGP/newton2.html).

The application must identify which matter belongs to the system, which interactions are external, and what frame is used. A rocket subsystem with changing membership is not silently treated as the same material system; a control-volume momentum balance would be a different explicitly scoped anchor.

### Entropy balance

The reference separates entropy transfer by heat and mass from internal entropy generation, using the [MIT control-volume entropy balance](https://ocw.mit.edu/courses/2-60j-fundamentals-of-advanced-energy-conversion-spring-2020/54a791b898a31befeea178f796efcd9c_MIT2_60s20_lec2.pdf). Nonnegative entropy generation is the second-law reference constraint, not a blanket requirement that every subsystem's entropy increase ([MIT thermodynamics lecture](https://ocw.mit.edu/courses/22-081j-introduction-to-sustainable-energy-fall-2010/411beca04e9b15f5ca2caed33b4a801d_MIT22_081JF10_lec09a.pdf)).

The starter requires a declared classical thermodynamic entropy description and relevant boundary temperatures. Do not apply it automatically to a different entropy definition, an unspecified subsystem, or a missing transfer inventory.

### Dimensional and mathematical constraints

Dimension signatures use an explicitly ordered seven-base convention corresponding to the SI/ISQ base quantities listed by [NIST](https://www.nist.gov/pml/special-publication-330/sp-330-section-2). This is one declared representation choice, not a new assertion that dimensions prove physical laws.

Quantity kind is separate from dimension: energy and moment of force are an example of different kinds with the same dimension in the [BIPM metrology vocabulary](https://jcgm.bipm.org/vim/en/1.2.html). Fields for quantity kind, tensor/vector structure, and frame cannot be discarded after a dimension match.

## Suggested assessment workflow

- **Register the subject:** Preserve the original equation, exact wording, source location, transcription uncertainties, declared purpose, and model version.
- **Choose a candidate anchor:** Record its formulation/version and why it is relevant. A source citation is a reference, not evidence that the studied system satisfies its conditions.
- **Examine applicability:** Map symbols, system identity, boundary, frame, domain, initial/boundary conditions, included interactions, and omitted terms to the anchor's requirements. Mark unknowns; retain out-of-scope results without classifying the model as false.
- **Examine mathematical eligibility:** Check definedness, quantity kinds, dimensions, numerical representation, and input availability under a specified method. A missing denominator or storage term blocks the affected calculation, not the entire evidence record.
- **Record the calculation:** Link exact input records and examined versions/states. Record what ran and its output separately from what an examiner inspected.
- **Assess one property at a time:** Report applicability, a particular law-consistency criterion, approximation adequacy, and empirical support separately. A declared complete term inventory is still a declaration needing evidence.
- **Preserve interpretations:** Keep implementation defects, measurement problems, omitted transfers/interactions, assumption mismatch, regime mismatch, and other explanations available. Neither a discrepancy nor an exact fit selects a root cause.

“Consistent with the selected balance under the recorded assumptions” is a permissible scoped finding when supported. “Physics verified,” “law disproved,” and “new physics established” are not automatic outputs of this workflow.

An unknown or out-of-scope application blocks a definitive law-comparison verdict, not the recording of observations or arithmetic differences. Preserve those in their own records even when the chosen anchor cannot yet interpret them.

## Structural safeguards and remaining semantic limits

The proposed schema structurally forbids a present calculation result when execution is `NOT_EXECUTED`, requires assessment references for definitive applicability/comparison labels, and prevents a law-consistency verdict when applicability is unknown or outside the selected scope. Explicit zero-denominator extensions require a present extension definition rather than an empty placeholder.

Those guards do not authenticate evidence. A reference can be broken, point to an unrelated assessment, or claim a resolution status that no resolver established; an author can also omit an anchor condition, assert a term inventory is complete, or supply contradictory declarations while satisfying record shape.

Until a semantic procedure resolves those dependencies, present such fields as recorded assertions, not established findings. An application record's confident status, even with a referenced assessment, cannot itself be used as proof of applicability or law consistency.

The authoring review deliberately probes these limitations in [review-results.json](../../reviews/draft-0.2/review-results.json). No semantic resolver, equation parser, dimension algebra engine, proof checker, physical applicability classifier, numerical backend, or uncertainty estimator is supplied.

## Offline review and mixed versions

The new schema has ID `urn:scope-audit-lab:schema:math-physics-extensions:0.2`. It references shared definitions from the frozen `urn:scope-audit-lab:schema:math-evidence:0.1`, whose local path is `../draft-0.1/evidence.schema.json`.

Register both schema documents explicitly in a local review registry. A reviewer must fail closed on an unregistered reference; a URN is not a network-fetch instruction, and no remote `$schema` download is required.

The [fixture generator](../../reviews/draft-0.2/build_examples.py) uses only Python's standard library and writes illustrative JSON to stdout. The optional [structural reviewer](../../reviews/draft-0.2/review_schema.py) uses separately installed authoring dependencies outside the project; it is not a stdlib runtime component or a claim of lab implementation.

The fixture bundle mixes unchanged-version observation/assessment record types with new supporting records. This does not establish compatibility with an uninspected prototype, require automatic migration, or change existing toolkit behavior.

## Source and evidence limits

References were read through fetched text or extracted equations; original PDF renderings were not visually inspected in this pass. Publication/course versions are identified only where present, source records remain explicitly unresolved, and no downloaded source artifact or empirical reproduction is asserted.

The [Sonin text extraction](https://web.mit.edu/2.25/www/pdf/fundamental_laws.pdf) also presented an apparent tension between an entropy inequality and explanatory prose. That is retained as an extraction/source-inspection question, not silently corrected or used to define this draft's entropy restriction; the entropy anchor instead cites the separately inspected MIT thermodynamics materials above.

Examples are synthetic and their applicability/criterion checks remain unevaluated. Their presence, structural review, and parent-toolkit selftests are not execution of the lab acceptance matrix, evidence of empirical validity, approval of the open design decisions, or full requirements-specification 0.2 conformance.
