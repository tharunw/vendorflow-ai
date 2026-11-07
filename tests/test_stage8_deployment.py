import json
import tempfile
import unittest
from pathlib import Path
from workflow import CaseManager

ROOT = Path(__file__).resolve().parents[1]

class TestDeploymentConfiguration(unittest.TestCase):
    def test_magic_link_uses_configured_public_base_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = CaseManager(str(Path(tmp) / "test.db"))
            payload = json.loads((ROOT / "vendor_submissions.jsonl").read_text(encoding="utf-8").splitlines()[0])
            manager.create_case(payload)
            link = manager.create_magic_link(payload["case_id"], base_url="https://vendorflow-demo.example")
            self.assertTrue(link.startswith("https://vendorflow-demo.example/?"))
            self.assertIn("case_id=CASE-0001", link)
            self.assertIn("token=", link)

if __name__ == "__main__":
    unittest.main()
