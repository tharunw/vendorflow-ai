# VendorFlow AI — Evaluation Report

- Benchmark cases: **30**
- Correct predictions: **30**
- Accuracy: **100.0%**
- Macro F1: **1.000**
- False approvals: **0**
- False rejections: **0**

## Per-class metrics

| Decision | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| APPROVED | 1.000 | 1.000 | 1.000 | 8 |
| PENDING | 1.000 | 1.000 | 1.000 | 20 |
| REJECTED | 1.000 | 1.000 | 1.000 | 2 |

## Confusion matrix

Rows = expected decision; columns = predicted decision.

| Expected vs Predicted | APPROVED | PENDING | REJECTED |
|---|---:|---:|---:|
| APPROVED | 8 | 0 | 0 |
| PENDING | 0 | 20 | 0 |
| REJECTED | 0 | 0 | 2 |

## Scenario-level accuracy

| Scenario | Correct | Total | Accuracy |
|---|---:|---:|---:|
| BAD_DOCUMENT | 2 | 2 | 100.0% |
| CLEAN | 8 | 8 | 100.0% |
| CONFIRMED_SYNTHETIC_FRAUD | 2 | 2 | 100.0% |
| CROSS_COUNTRY | 4 | 4 | 100.0% |
| EXISTING_BANK_CHANGE | 4 | 4 | 100.0% |
| INCOMPLETE | 5 | 5 | 100.0% |
| NAME_MISMATCH | 5 | 5 | 100.0% |

## Mismatches

No decision mismatches on this synthetic benchmark.

## Interpretation and limitations

These metrics measure agreement with the supplied synthetic labels only. They do not establish real-world fraud detection, legal compliance, or bank/tax verification.

The dataset is small and synthetic. Do not present these results as production model performance or evidence of real-world fraud detection.
The benchmark labels and rules are prototype-specific; external government and bank verification are not performed.
