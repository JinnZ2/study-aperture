Status: user-supplied assessment-output specimens preserved as data with a separate, bounded source review. This is not a new source-authentication implementation, a model benchmark, a scientific-validity verdict, or proof of execution through `assess.py`.

# Gemini assessment records, 2026-11-11

This collection preserves two user-reported Gemini attempts: the first contains
three publication records; the second contains one record about a different
publication, supplied after an attempted correction. The exact prompts,
correction instructions, model version, generation settings, original model
session, tool access, and any repository execution logs were not supplied.
Attribution to Gemini and the ordering come from the user's report, not an
independently inspected model session.

## Files and capture boundary

| File | Role |
|---|---|
| `data/attempt-01.txt` | First supplied structured payload, three records, unchanged after capture |
| `data/attempt-02.txt` | Second supplied structured payload, one record, unchanged after capture |
| `manifest.json` | Explicit capture conditions, attempt relationship, byte counts, and SHA-256 hashes |
| `REVIEW.md` | Reviewer findings, source locations, uncertainty, and what this does not establish |

The capture starts at `PUBLICATION:` and ends at the final `INCOMPLETENESS:`
line of each supplied payload. Conversational prefaces are outside the capture.
Text is UTF-8 with LF line endings and a final newline; the first capture
preserves the nonbreaking space and trailing spaces present in the supplied
payload. No spelling, quotation, citation, diagnostic state, decision,
mathematical notation, or failure classification has been repaired in either
specimen. These are captures of user-supplied text, not authenticated byte
exports from Gemini.

Path-specific `.gitattributes` rules disable automatic text conversion and
whitespace-error treatment for these two raw captures only. They preserve
original trailing whitespace rather than treating cleanup as a correction.

The original conversational provenance is the
[user-authorized session](https://www.perplexity.ai/computer/tasks/30f3ec2c-6611-4cfa-9c5f-fd39d0f968dc).
Private local paths, user identifiers, and the surrounding conversation are
not included in the published specimens.

## How to use this data

- **Read the originals first:** preserve what was actually supplied before
  evaluating its content. A reviewer correction is a separate record.
- **Keep the comparison bounded:** attempt 02 concerns a different paper,
  not a corrected version of any of attempt 01's three records. Do not compute
  an improvement rate or general model reliability from these four records.
- **Separate the failure axes:** publication identity, quotation fidelity,
  source access, diagnostic authorization, scope, and physical adequacy are
  different questions. Do not collapse them into `MODEL_FAILED`.
- **Do not silently promote:** stored text, a hash match, and a passing
  repository test do not make a specimen a valid assessment or a claim
  empirically supported.
- **Retain uncertainty:** an unlocated basis is not proof that the relevant
  check never occurred. A different source containing a claim does not
  retroactively repair its original attribution.

Future corrections belong in a new review or specimen, linked to their
predecessor and with their own provenance. Do not edit these captures to make
the original model output more correct.

## Verification

From the repository root:

```sh
python3 -m unittest discover -s tests -p 'test_assessment_specimens.py' -v
./run_checks.sh
```

The offline tests pin the captured bytes, check manifest coverage, retain the
three-plus-one record boundaries and independent-review status, and confirm
that source locations remain recorded. They do not fetch publications,
authenticate a model session, reproduce the studies, or run these specimens
through `assess.py`. The existing `run_checks.sh` already discovers this suite.
