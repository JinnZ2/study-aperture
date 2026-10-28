# Offline evidence-integrity report

Status: INTEGRITY_GAPS_RECORDED. This is not mathematical or empirical validation.
Structural JSON Schema validation was not performed; all condition outcomes remain recorded assertions.

## Snapshot

| Input | SHA-256 |
|---|---|
| experimental/scope_audit_lab/examples/schema-draft-0.2/records.json | 00f09d8add5d159924f6dd02c577af7c61492d13c9e392d5be6dbccb1980394a |

## Reference resolution

| Reference | Expected type | Snapshot result | Location |
|---|---|---|---|
| physics-draft:source-mit-energy-2020 | source | UNRESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/0/source_refs/0&quot;} |
| physics-draft:source-mit-energy-2020 | source | UNRESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/0/payload/source_citations/0/source_record&quot;} |
| physics-draft:source-mit-sonin | source | UNRESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/1/source_refs/0&quot;} |
| physics-draft:source-nasa-newton | source | UNRESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/1/source_refs/1&quot;} |
| physics-draft:source-mit-sonin | source | UNRESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/1/payload/source_citations/0/source_record&quot;} |
| physics-draft:source-nasa-newton | source | UNRESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/1/payload/source_citations/1/source_record&quot;} |
| physics-draft:source-mit-energy-2020 | source | UNRESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/2/source_refs/0&quot;} |
| physics-draft:source-mit-entropy-2010 | source | UNRESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/2/source_refs/1&quot;} |
| physics-draft:source-mit-energy-2020 | source | UNRESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/2/payload/source_citations/0/source_record&quot;} |
| physics-draft:source-mit-entropy-2010 | source | UNRESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/2/payload/source_citations/1/source_record&quot;} |
| physics-draft:power | quantity_definition | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/9/payload/result_quantity&quot;} |
| physics-draft:balance | balance_specification | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/9/payload/dependency_refs/0&quot;} |
| physics-draft:storage-rate | observation | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/9/payload/inputs/0/input&quot;} |
| physics-draft:power | quantity_definition | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/9/payload/inputs/0/quantity_definition&quot;} |
| physics-draft:power-in | observation | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/9/payload/inputs/1/input&quot;} |
| physics-draft:power | quantity_definition | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/9/payload/inputs/1/quantity_definition&quot;} |
| physics-draft:power-out | observation | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/9/payload/inputs/2/input&quot;} |
| physics-draft:power | quantity_definition | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/9/payload/inputs/2/quantity_definition&quot;} |
| physics-draft:energy-anchor | physics_anchor | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/10/payload/anchor&quot;} |
| physics-draft:power | quantity_definition | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/10/payload/balanced_quantity&quot;} |
| physics-draft:power | quantity_definition | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/10/payload/terms/0/quantity_definition&quot;} |
| physics-draft:storage-rate | observation | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/10/payload/terms/0/input_refs/0&quot;} |
| physics-draft:power | quantity_definition | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/10/payload/terms/1/quantity_definition&quot;} |
| physics-draft:power-in | observation | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/10/payload/terms/1/input_refs/0&quot;} |
| physics-draft:power | quantity_definition | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/10/payload/terms/2/quantity_definition&quot;} |
| physics-draft:power-out | observation | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/10/payload/terms/2/input_refs/0&quot;} |
| physics-draft:angle | quantity_definition | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/11/payload/inputs/0/quantity_definition&quot;} |
| physics-draft:dimension-one | quantity_definition | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/11/payload/error/quantity_definition&quot;} |
| physics-draft:dimension-one | quantity_definition | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/11/payload/criterion/threshold_quantity&quot;} |
| physics-draft:energy-anchor | physics_anchor | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/12/payload/anchor&quot;} |
| physics-draft:balance | balance_specification | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/12/payload/subjects/0/subject&quot;} |
| physics-draft:storage-rate | observation | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/12/payload/symbol_mappings/0/subject&quot;} |
| physics-draft:power | quantity_definition | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/12/payload/symbol_mappings/0/quantity_definition&quot;} |
| physics-draft:storage-rate | observation | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/13/payload/dependency_refs/0&quot;} |
| physics-draft:residual | calculation | RESOLVED | {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/13/payload/subjects/0/subject&quot;} |

## Anchor-condition coverage

| Application | Available-condition identity coverage | Coverage for bound version |
|---|---|---|
| physics-draft:energy-application | COMPLETE | COMPLETE |

Complete coverage means every condition has one matching check, not that the conditions are met.

### Recorded condition outcomes

| Application / condition | Recorded outcome | Evidence-link resolutions |
|---|---|---|
| physics-draft:energy-application / E-boundary | NOT_EVALUATED | [] |
| physics-draft:energy-application / E-signs | NOT_EVALUATED | [] |
| physics-draft:energy-application / E-stored | NOT_EVALUATED | [] |
| physics-draft:energy-application / E-formalism | NOT_EVALUATED | [] |
| physics-draft:energy-application / E-inventory | NOT_EVALUATED | [] |

## Version bindings

| Location | Examined version | Target version | Binding |
|---|---|---|---|
| {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/9/payload/inputs/0&quot;} | {&quot;status&quot;: &quot;PRESENT&quot;, &quot;value&quot;: &quot;fixture-0.2-1&quot;} | {&quot;status&quot;: &quot;PRESENT&quot;, &quot;value&quot;: &quot;fixture-0.2-1&quot;} | SAME_DECLARED_VERSION |
| {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/9/payload/inputs/1&quot;} | {&quot;status&quot;: &quot;PRESENT&quot;, &quot;value&quot;: &quot;fixture-0.2-1&quot;} | {&quot;status&quot;: &quot;PRESENT&quot;, &quot;value&quot;: &quot;fixture-0.2-1&quot;} | SAME_DECLARED_VERSION |
| {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/9/payload/inputs/2&quot;} | {&quot;status&quot;: &quot;PRESENT&quot;, &quot;value&quot;: &quot;fixture-0.2-1&quot;} | {&quot;status&quot;: &quot;PRESENT&quot;, &quot;value&quot;: &quot;fixture-0.2-1&quot;} | SAME_DECLARED_VERSION |
| {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/11/payload/inputs/0&quot;} | {&quot;status&quot;: &quot;MISSING&quot;, &quot;reason&quot;: &quot;No input version.&quot;} | null | BLOCKED_REFERENCE |
| {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/12/payload/subjects/0&quot;} | {&quot;status&quot;: &quot;PRESENT&quot;, &quot;value&quot;: &quot;fixture-0.2-1&quot;} | {&quot;status&quot;: &quot;PRESENT&quot;, &quot;value&quot;: &quot;fixture-0.2-1&quot;} | SAME_DECLARED_VERSION |
| {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/13/payload/subjects/0&quot;} | {&quot;status&quot;: &quot;PRESENT&quot;, &quot;value&quot;: &quot;fixture-0.2-1&quot;} | {&quot;status&quot;: &quot;PRESENT&quot;, &quot;value&quot;: &quot;fixture-0.2-1&quot;} | SAME_DECLARED_VERSION |
| {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/12/payload/anchor&quot;} | {&quot;status&quot;: &quot;PRESENT&quot;, &quot;value&quot;: &quot;fixture-0.2-1&quot;} | {&quot;status&quot;: &quot;PRESENT&quot;, &quot;value&quot;: &quot;fixture-0.2-1&quot;} | SAME_DECLARED_VERSION |

## Integrity findings

- **UNKNOWN / REFERENCE_UNRESOLVED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/0/source_refs/0&quot;}: Snapshot identity/type resolution is UNRESOLVED; content truth is not evaluated.
- **UNKNOWN / REFERENCE_UNRESOLVED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/0/payload/source_citations/0/source_record&quot;}: Snapshot identity/type resolution is UNRESOLVED; content truth is not evaluated.
- **UNKNOWN / REFERENCE_UNRESOLVED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/1/source_refs/0&quot;}: Snapshot identity/type resolution is UNRESOLVED; content truth is not evaluated.
- **UNKNOWN / REFERENCE_UNRESOLVED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/1/source_refs/1&quot;}: Snapshot identity/type resolution is UNRESOLVED; content truth is not evaluated.
- **UNKNOWN / REFERENCE_UNRESOLVED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/1/payload/source_citations/0/source_record&quot;}: Snapshot identity/type resolution is UNRESOLVED; content truth is not evaluated.
- **UNKNOWN / REFERENCE_UNRESOLVED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/1/payload/source_citations/1/source_record&quot;}: Snapshot identity/type resolution is UNRESOLVED; content truth is not evaluated.
- **UNKNOWN / REFERENCE_UNRESOLVED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/2/source_refs/0&quot;}: Snapshot identity/type resolution is UNRESOLVED; content truth is not evaluated.
- **UNKNOWN / REFERENCE_UNRESOLVED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/2/source_refs/1&quot;}: Snapshot identity/type resolution is UNRESOLVED; content truth is not evaluated.
- **UNKNOWN / REFERENCE_UNRESOLVED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/2/payload/source_citations/0/source_record&quot;}: Snapshot identity/type resolution is UNRESOLVED; content truth is not evaluated.
- **UNKNOWN / REFERENCE_UNRESOLVED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/2/payload/source_citations/1/source_record&quot;}: Snapshot identity/type resolution is UNRESOLVED; content truth is not evaluated.
- **UNKNOWN / BINDING_BLOCKED_REFERENCE**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/11/payload/inputs/0&quot;}: Exact declared-version binding is BLOCKED_REFERENCE; chronology, relevance of changes, and physical validity are not inferred.
- **UNKNOWN / CONDITION_NOT_EVALUATED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/12/payload/condition_checks/0&quot;}: Recorded condition outcome remains NOT_EVALUATED. {&quot;condition_id&quot;: &quot;E-boundary&quot;}
- **UNKNOWN / CONDITION_NOT_EVALUATED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/12/payload/condition_checks/1&quot;}: Recorded condition outcome remains NOT_EVALUATED. {&quot;condition_id&quot;: &quot;E-signs&quot;}
- **UNKNOWN / CONDITION_NOT_EVALUATED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/12/payload/condition_checks/2&quot;}: Recorded condition outcome remains NOT_EVALUATED. {&quot;condition_id&quot;: &quot;E-stored&quot;}
- **UNKNOWN / CONDITION_NOT_EVALUATED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/12/payload/condition_checks/3&quot;}: Recorded condition outcome remains NOT_EVALUATED. {&quot;condition_id&quot;: &quot;E-formalism&quot;}
- **UNKNOWN / CONDITION_NOT_EVALUATED**: {&quot;input&quot;: &quot;experimental/scope_audit_lab/examples/schema-draft-0.2/records.json&quot;, &quot;pointer&quot;: &quot;/records/12/payload/condition_checks/4&quot;}: Recorded condition outcome remains NOT_EVALUATED. {&quot;condition_id&quot;: &quot;E-inventory&quot;}

## Verification limits

- Resolution establishes only supplied-snapshot identity and declared type, not authenticated content.
- Same declared version does not prove equal content, complete dependencies, or empirical freshness.
- Condition coverage and recorded outcomes do not establish physical applicability or evidence relevance.
- No URLs/artifact paths are opened, no submitted code is executed, and inputs are not modified.
- Unsupported contracts remain opaque. Missing targets do not establish falsehood.
- No full JSON Schema validation, temporal ordering, proof checking, or scientific verdict.
