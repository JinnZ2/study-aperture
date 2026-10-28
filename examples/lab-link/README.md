# Example: linking a lab integrity report to a claim

Status: synthetic demonstration of `assess.py labref`. The claim is a placeholder, not drawn from any publication.

```
experimental/scope_audit_lab/examples/schema-draft-0.2/records.json   (synthetic evidence bundle)
        │  integrity_checker.py --output
        ▼
integrity-report.json   status INTEGRITY_GAPS_RECORDED, sha256 bound into the record
        │  assess.py labref --id L1 --lab-report integrity-report.json --claim C1
        ▼
assessment.json  lab_refs[L1] → claims [C1]      claim C1 support: UNDETERMINED (unchanged)
        │  assess.py report
        ▼
report.md   gaps listed under Incompleteness; L1 rendered as bundle integrity only
```

What this shows:

- The link carries the checker's own status, finding counts, input hashes, and the SHA-256 of the report file. It never edits claim support or decisions; a clean lab report would not make C1 SUPPORTED either.
- `INTEGRITY_GAPS_RECORDED` appears in the report's Incompleteness section.
- If `integrity-report.json` is edited, `assess.py check` fails (the binding broke). If it is deleted, the record stays VALID and the missing file is listed as incompleteness.

Rebuild from the repository root:

```sh
E=examples/lab-link
python3 experimental/scope_audit_lab/integrity_checker.py \
  experimental/scope_audit_lab/examples/schema-draft-0.2/records.json --output $E/integrity-report.json   # exit 1: gaps recorded
python3 assess.py labref --file $E/assessment.json --id L1 --lab-report $E/integrity-report.json --claim C1
python3 assess.py report --file $E/assessment.json > $E/report.md
```

(`labref` refuses an existing id; to rebuild from scratch, rerun the full `init`/`claim`/`tool`/`labref` sequence in a new record.)
