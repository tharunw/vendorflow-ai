import json
import unittest
from pathlib import Path

from engine import evaluate_submission
from engine.validators import gstin_check_character, validate_gstin

ROOT = Path(__file__).resolve().parents[1]

def make_valid_gstin():
    first14 = "29ABCCA1234F1Z"
    return first14 + gstin_check_character(first14)

def base_submission():
    gstin = make_valid_gstin()
    return {
        "case_id": "CASE-TEST-0001",
        "vendor_id": "VND-TEST-0001",
        "submission_version": 1,
        "vendor": {
            "legal_name": "ABC Technologies Private Limited",
            "country": "IN",
            "business_type": "PRIVATE_LIMITED",
            "business_email": "finance@abctech.example",
            "business_address": "Fictional Test Park, Hyderabad"
        },
        "tax": {
            "tax_type": "GSTIN",
            "tax_id": gstin,
            "tax_registered_name": "ABC Technologies Private Limited"
        },
        "bank": {
            "account_holder_name": "ABC Technologies Private Limited",
            "account_number": "TEST-0001",
            "bank_country": "IN",
            "ifsc": "TEST0001234"
        },
        "documents": [
            {"document_id": "DOC-1", "document_type": "BANK_PROOF",
             "file_name": "bank_proof.txt"}
        ],
        "metadata": {
            "submission_source": "WEB_FORM",
            "submitted_at": "2026-11-06T10:00:00Z",
            "is_existing_vendor": False
        }
    }

class TestVendorFlowEngine(unittest.TestCase):
    def test_gstin_checksum(self):
        value = make_valid_gstin()
        self.assertTrue(validate_gstin(value)[0])
        altered = value[:-1] + ("0" if value[-1] != "0" else "1")
        self.assertFalse(validate_gstin(altered)[0])

    def test_clean_happy_path_approved(self):
        result = evaluate_submission(base_submission())
        self.assertEqual(result.decision, "APPROVED")
        self.assertEqual(result.lifecycle_status, "CLOSED")

    def test_missing_tax_id_pending(self):
        sub = base_submission()
        sub["tax"]["tax_id"] = ""
        result = evaluate_submission(sub)
        self.assertEqual(result.decision, "PENDING")
        self.assertEqual(result.lifecycle_status, "OPEN")

    def test_bank_holder_mismatch_pending(self):
        sub = base_submission()
        sub["bank"]["account_holder_name"] = "ABC Technology Services Limited"
        result = evaluate_submission(sub)
        self.assertEqual(result.decision, "PENDING")
        self.assertTrue(any(m.score < 92 for m in result.name_matches))

    def test_cross_country_inconsistency_pending(self):
        sub = base_submission()
        sub["bank"]["bank_country"] = "AE"
        sub["bank"].pop("ifsc", None)
        sub["business_email"] = "not-used"
        sub["vendor"]["business_email"] = "vendor@gmail.com"
        result = evaluate_submission(sub)
        self.assertEqual(result.decision, "PENDING")
        self.assertTrue(any(v.rule_id == "R009" and not v.passed for v in result.validations))

    def test_existing_vendor_bank_change_pending(self):
        sub = base_submission()
        sub["metadata"]["is_existing_vendor"] = True
        sub["metadata"]["existing_bank_details_changed"] = True
        result = evaluate_submission(sub)
        self.assertEqual(result.decision, "PENDING")
        self.assertTrue(any(v.rule_id == "R012" and not v.passed for v in result.validations))

    def test_bad_document_does_not_hard_reject(self):
        sub = base_submission()
        sub["documents"][0]["quality"] = "UNREADABLE"
        result = evaluate_submission(sub)
        self.assertEqual(result.decision, "PENDING")
        self.assertEqual(result.lifecycle_status, "OPEN")
        self.assertFalse(result.hard_rejection_reasons)

    def test_confirmed_fraud_rejected(self):
        sub = base_submission()
        sub["metadata"]["confirmed_fraud"] = True
        result = evaluate_submission(sub)
        self.assertEqual(result.decision, "REJECTED")
        self.assertEqual(result.lifecycle_status, "CLOSED")

    def test_result_serializes(self):
        result = evaluate_submission(base_submission())
        serialized = json.dumps(result.to_dict())
        self.assertIn('"decision": "APPROVED"', serialized)

if __name__ == "__main__":
    unittest.main(verbosity=2)
