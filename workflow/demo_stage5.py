"""Small command-line demonstration of Stage 5."""
import json
from pathlib import Path
from workflow import CaseManager

ROOT = Path(__file__).resolve().parent
manager = CaseManager("vendorflow_stage5_demo.db")
with open(ROOT / "vendor_submissions.jsonl", encoding="utf-8") as f:
    payload = json.loads(next(f))
case = manager.create_case(payload)
print("Created:", case["case"]["case_id"], case["case"]["business_decision"], case["case"]["lifecycle_status"])
if case["case"]["lifecycle_status"] == "OPEN":
    draft = manager.create_correction_email(payload["case_id"])
    link = manager.create_magic_link(payload["case_id"])
    print("\nEMAIL DRAFT (not sent)\n", draft["subject"], "\n", draft["body"])
    print("\nDEMO MAGIC LINK:\n", link)
print("\nAudit events:", len(manager.get_case(payload["case_id"])["audit_log"]))
