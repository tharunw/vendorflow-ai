import json, tempfile, unittest
from pathlib import Path
from workflow import CaseManager

ROOT = Path(__file__).resolve().parents[1]
class TestOpenCaseWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.manager = CaseManager(str(Path(self.tmp.name) / "test.db"))
        lines = (ROOT / "vendor_submissions.jsonl").read_text(encoding="utf-8").splitlines()
        self.clean = json.loads(next(line for line in lines if json.loads(line)["case_id"] == "CASE-0006"))
        self.pending = json.loads(next(line for line in lines if json.loads(line)["case_id"] == "CASE-0009"))
    def tearDown(self): self.tmp.cleanup()
    def test_create_and_version_one(self):
        data = self.manager.create_case(self.clean)
        self.assertEqual(data["case"]["current_version"], 1)
        self.assertEqual(data["submission"]["case_id"], self.clean["case_id"])
    def test_email_draft_for_pending_case(self):
        self.manager.create_case(self.pending)
        draft = self.manager.create_correction_email(self.pending["case_id"])
        self.assertIn("Action required", draft["subject"])
        self.assertTrue(draft["body"])
    def test_magic_link_and_resubmission(self):
        self.manager.create_case(self.pending)
        url = self.manager.create_magic_link(self.pending["case_id"])
        token = url.split("token=", 1)[1]
        outcome = self.manager.resubmit(self.pending["case_id"], token,
                                        {"vendor": {"business_email": "accounts@example.org"}})
        self.assertEqual(outcome["case"]["case"]["current_version"], 2)
        self.assertEqual(outcome["diff"][0]["field"], "vendor.business_email")
    def test_magic_link_one_time(self):
        self.manager.create_case(self.pending)
        url = self.manager.create_magic_link(self.pending["case_id"])
        token = url.split("token=", 1)[1]
        self.manager.resubmit(self.pending["case_id"], token, {"vendor": {"business_email": "a@b.org"}})
        with self.assertRaises(ValueError):
            self.manager.resubmit(self.pending["case_id"], token, {"vendor": {"business_email": "c@d.org"}})
    def test_invalid_token_rejected(self):
        self.manager.create_case(self.pending)
        with self.assertRaises(ValueError):
            self.manager.resubmit(self.pending["case_id"], "wrong-token", {"vendor": {"business_email": "x@y.org"}})
    def test_closed_case_cannot_be_resubmitted(self):
        self.manager.create_case(self.clean)
        with self.assertRaises(ValueError):
            self.manager.create_magic_link(self.clean["case_id"])
if __name__ == "__main__": unittest.main()
