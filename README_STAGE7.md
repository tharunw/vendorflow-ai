# VendorFlow AI — Stage 7 Evaluation Harness

## Run evaluation
From the project root:
```powershell
python -m evaluation.evaluate
```

The evaluator compares every deterministic engine decision against `ground_truth.json` using `vendor_submissions.jsonl`.

## Generated reports
The command creates a `reports/` directory containing:
- `evaluation_report.md`: readable summary, class metrics, confusion matrix and scenario accuracy.
- `evaluation_summary.json`: machine-readable metrics and mismatches.
- `case_level_evaluation.csv`: one row per test case, including expected/predicted decisions, risk score, flags and pending reasons.

## Metrics
- Accuracy: correct decisions / all labelled cases.
- Precision: of predictions for a class, the fraction matching that class.
- Recall: of true cases in a class, the fraction correctly identified.
- F1: harmonic mean of precision and recall.
- Macro F1: unweighted mean of the three class F1 scores.
- False approval: a case labelled PENDING or REJECTED by the benchmark but predicted APPROVED.
- False rejection: a case labelled APPROVED or PENDING by the benchmark but predicted REJECTED.
- Confusion matrix: rows are expected labels; columns are predicted labels.

## Important interpretation
The benchmark is a small, fictional, synthetic set of 30 labelled cases. Perfect agreement means the current rule engine matches these supplied labels; it does not establish generalisation to real vendor data, fraud-detection quality, regulatory compliance, or external bank/tax verification. Avoid describing the result as "100% real-world accuracy".
