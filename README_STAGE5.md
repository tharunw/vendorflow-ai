# VendorFlow AI — Stage 5: Open-Case Workflow

Stage 5 adds persistent case management to the Stage 4 decision engine:
- SQLite storage for cases, immutable submission versions, assessments, audit events, email drafts and magic links.
- `PENDING` cases remain `OPEN`; `APPROVED` and `REJECTED` cases are closed.
- Correction email drafts are generated but **not sent**.
- Magic links use cryptographically random tokens. Only SHA-256 token hashes are stored; links expire and are single-use.
- Vendor resubmissions create a new immutable version, produce a field-level diff, and re-run the Stage 4 deterministic engine.
- Existing records are not overwritten.

## 1. Install / setup
Python 3.10+ recommended. Open a terminal in this project folder:
```powershell
python -m unittest discover -s .\tests -p "test_*.py" -v
```
No new third-party package is required for Stage 5; SQLite, token generation and hashing use Python's standard library.

## 2. Run the demo
```powershell
python workflow\demo_stage5.py
```
The demo creates `vendorflow_stage5_demo.db`, prints the current case decision, creates an email draft, and prints a local demo magic link. It does not send email.

## 3. Use from Python
```python
from workflow import CaseManager
import json

manager = CaseManager("vendorflow.db")
with open("vendor_submissions.jsonl", encoding="utf-8") as f:
    payload = json.loads(next(f))

case = manager.create_case(payload)
print(case["case"])
print(case["assessment"])

draft = manager.create_correction_email(payload["case_id"])
print(draft["body"])  # draft only

url = manager.create_magic_link(payload["case_id"])
print(url)  # demo URL; token is returned once to the caller

# In a real form, parse the token from the secure URL and pass only changed fields:
token = url.split("token=", 1)[1]
result = manager.resubmit(payload["case_id"], token, {
    "vendor": {"business_email": "accounts@example.org"}
})
print(result["diff"])
print(result["case"]["assessment"])
```

## 4. Database tables
- `cases`: current decision, lifecycle, current version.
- `submissions`: immutable JSON snapshot for every version.
- `assessments`: engine output per version.
- `audit_logs`: append-only event history.
- `email_drafts`: generated email content.
- `magic_links`: token hash, expiry, used timestamp.

## 5. Security / production limitations
This is a local case-study prototype, not a production identity or payment verification system.
- Email is not sent; the draft is shown for demonstration.
- The demo URL uses localhost. A deployed app must use HTTPS, secure session handling, rate limits, access controls and a real mail provider.
- Raw magic tokens are returned once; only their SHA-256 hashes are stored.
- The sample workflow accepts targeted JSON updates. A production form must whitelist editable fields and validate uploaded files, file size/type, malware and document provenance.
- Existing-vendor bank-change protection in Stage 4 is still a synthetic metadata signal. Before production, compare new bank details against a trusted, separately stored vendor master record and require human verification for changes.
- Sample documents and identifiers are fictional. Format/checksum checks are not government or bank verification.
- The engine's decision is only a prototype policy outcome, not legal/compliance approval.

## 6. Tests
Six Stage 5 workflow tests are added. Total suite should show 15 tests passing (9 Stage 4 + 6 Stage 5).
