import unittest
from evaluation.evaluate import evaluate, load_inputs

class TestEvaluationHarness(unittest.TestCase):
    def test_benchmark_has_30_labelled_cases(self):
        submissions, truth = load_inputs()
        self.assertEqual(len(submissions), 30)
        self.assertEqual(len(truth), 30)

    def test_benchmark_decisions_match_ground_truth(self):
        result = evaluate()
        self.assertEqual(result["total_cases"], 30)
        self.assertEqual(result["incorrect_predictions"], 0)
        self.assertEqual(result["accuracy"], 1.0)

    def test_report_files_created(self):
        evaluate()
        from evaluation.evaluate import REPORT_DIR
        self.assertTrue((REPORT_DIR / "evaluation_report.md").exists())
        self.assertTrue((REPORT_DIR / "case_level_evaluation.csv").exists())
        self.assertTrue((REPORT_DIR / "evaluation_summary.json").exists())

if __name__ == "__main__":
    unittest.main()
