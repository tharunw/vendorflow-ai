# VendorFlow AI — Stage 4 Core Engine

## Run tests
From this folder:
```bash
python -m unittest discover -s tests -v
```

## Use the engine
```python
import json
from engine import evaluate_submission

with open("vendor_submissions.jsonl", encoding="utf-8") as f:
    submission = json.loads(next(f))

result = evaluate_submission(submission)
print(json.dumps(result.to_dict(), indent=2))
```

## Decision policy
- APPROVED: all implemented mandatory checks pass and no risk flags remain.
- PENDING: missing/correctable issues or review flags; lifecycle remains OPEN.
- REJECTED: only when explicit, trusted hard-rejection evidence is provided.

## Scope and limitations
- GSTIN: structure, embedded PAN structure and base-36 checksum.
- PAN: format only.
- EIN: format only, not IRS verification.
- UK VAT: 9-digit/12-digit format only, not HMRC verification.
- IFSC: format only, not bank existence or account ownership.
- US routing number: nine-digit structure only; checksum/bank verification not implemented.
- UK sort code: six-digit structure only.
- Name matching is a review signal, not identity proof.
- Cross-border banking is flagged for review, not automatically rejected.
- Synthetic reference data is not external verification.

GSTIN checksum design follows the widely used base-36 Luhn-style calculation. Official GST rules specify the GSTIN structure and presence of a checksum character, but passing the checksum does not prove active registration.


## Name similarity thresholds
- 97–100: strong match after legal-suffix normalization.
- 85–96.99: review band.
- Below 85: mismatch signal.
These are prototype thresholds calibrated against this small synthetic dataset, not universal identity-verification standards.
