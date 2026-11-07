"""Evaluate VendorFlow AI decisions against the labelled synthetic benchmark.

Run from the project root:
    python -m evaluation.evaluate
Only standard-library modules are used.
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from engine import evaluate_submission

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "vendor_submissions.jsonl"
LABEL_PATH = ROOT / "ground_truth.json"
REPORT_DIR = ROOT / "reports"
LABELS = ["APPROVED", "PENDING", "REJECTED"]


def load_inputs():
    submissions = [json.loads(line) for line in DATA_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    labels = json.loads(LABEL_PATH.read_text(encoding="utf-8"))
    truth = {row["case_id"]: row for row in labels}
    if len(truth) != len(labels):
        raise ValueError("Ground-truth file contains duplicate case IDs.")
    if set(x["case_id"] for x in submissions) != set(truth):
        raise ValueError("Submission case IDs and ground-truth case IDs do not match.")
    return submissions, truth


def safe_div(num, den):
    return num / den if den else 0.0


def evaluate():
    submissions, truth = load_inputs()
    rows = []
    confusion = {actual: {pred: 0 for pred in LABELS} for actual in LABELS}
    scenario_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    class_counts = {}
    for submission in submissions:
        case_id = submission["case_id"]
        expected = truth[case_id]["expected_decision"]
        result = evaluate_submission(submission).to_dict()
        predicted = result["decision"]
        if expected not in LABELS or predicted not in LABELS:
            raise ValueError(f"Unexpected decision label for {case_id}: {expected}/{predicted}")
        correct = expected == predicted
        confusion[expected][predicted] += 1
        scenario = truth[case_id].get("scenario", "UNKNOWN")
        scenario_stats[scenario]["total"] += 1
        scenario_stats[scenario]["correct"] += int(correct)
        rows.append({
            "case_id": case_id,
            "scenario": scenario,
            "expected_decision": expected,
            "predicted_decision": predicted,
            "correct": correct,
            "risk_score": result["risk_score"],
            "lifecycle_status": result["lifecycle_status"],
            "risk_flags": "; ".join(str(x.get("rule_id", x)) for x in result.get("risk_flags", [])),
            "pending_reasons": " | ".join(result.get("pending_reasons", [])),
        })

    total = len(rows)
    correct_n = sum(r["correct"] for r in rows)
    metrics = {}
    f1s = []
    for label in LABELS:
        tp = confusion[label][label]
        fp = sum(confusion[a][label] for a in LABELS if a != label)
        fn = sum(confusion[label][p] for p in LABELS if p != label)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2 * precision * recall, precision + recall)
        support = sum(confusion[label].values())
        metrics[label] = {"precision": precision, "recall": recall, "f1": f1, "support": support}
        f1s.append(f1)

    false_approvals = sum(1 for r in rows if r["predicted_decision"] == "APPROVED" and r["expected_decision"] != "APPROVED")
    false_rejections = sum(1 for r in rows if r["predicted_decision"] == "REJECTED" and r["expected_decision"] != "REJECTED")
    scenario_report = {
        name: {"correct": values["correct"], "total": values["total"],
               "accuracy": safe_div(values["correct"], values["total"])}
        for name, values in sorted(scenario_stats.items())
    }
    mismatches = [r for r in rows if not r["correct"]]
    summary = {
        "benchmark": "VendorFlow AI synthetic labelled benchmark",
        "total_cases": total,
        "correct_predictions": correct_n,
        "incorrect_predictions": total - correct_n,
        "accuracy": safe_div(correct_n, total),
        "macro_f1": safe_div(sum(f1s), len(f1s)),
        "false_approvals": false_approvals,
        "false_rejections": false_rejections,
        "class_metrics": metrics,
        "confusion_matrix": confusion,
        "scenario_metrics": scenario_report,
        "mismatches": mismatches,
        "interpretation": (
            "These metrics measure agreement with the supplied synthetic labels only. "
            "They do not establish real-world fraud detection, legal compliance, or bank/tax verification."
        )
    }

    REPORT_DIR.mkdir(exist_ok=True)
    with (REPORT_DIR / "case_level_evaluation.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    (REPORT_DIR / "evaluation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# VendorFlow AI — Evaluation Report", "",
        f"- Benchmark cases: **{total}**",
        f"- Correct predictions: **{correct_n}**",
        f"- Accuracy: **{summary['accuracy']:.1%}**",
        f"- Macro F1: **{summary['macro_f1']:.3f}**",
        f"- False approvals: **{false_approvals}**",
        f"- False rejections: **{false_rejections}**", "",
        "## Per-class metrics", "",
        "| Decision | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|"
    ]
    for label, m in metrics.items():
        lines.append(f"| {label} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {m['support']} |")
    lines += ["", "## Confusion matrix", "",
              "Rows = expected decision; columns = predicted decision.", "",
              "| Expected vs Predicted | APPROVED | PENDING | REJECTED |",
              "|---|---:|---:|---:|"]
    for actual in LABELS:
        lines.append("| " + actual + " | " + " | ".join(str(confusion[actual][p]) for p in LABELS) + " |")
    lines += ["", "## Scenario-level accuracy", "",
              "| Scenario | Correct | Total | Accuracy |", "|---|---:|---:|---:|"]
    for scenario, m in scenario_report.items():
        lines.append(f"| {scenario} | {m['correct']} | {m['total']} | {m['accuracy']:.1%} |")
    lines += ["", "## Mismatches", ""]
    if mismatches:
        lines += ["| Case | Scenario | Expected | Predicted |", "|---|---|---|---|"]
        for r in mismatches:
            lines.append(f"| {r['case_id']} | {r['scenario']} | {r['expected_decision']} | {r['predicted_decision']} |")
    else:
        lines.append("No decision mismatches on this synthetic benchmark.")
    lines += ["", "## Interpretation and limitations", "", summary["interpretation"], "",
              "The dataset is small and synthetic. Do not present these results as production model performance or evidence of real-world fraud detection.",
              "The benchmark labels and rules are prototype-specific; external government and bank verification are not performed.", ""]
    (REPORT_DIR / "evaluation_report.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = evaluate()
    print("VENDORFLOW AI EVALUATION")
    print(f"Cases: {result['total_cases']}")
    print(f"Accuracy: {result['accuracy']:.1%}")
    print(f"Macro F1: {result['macro_f1']:.3f}")
    print(f"False approvals: {result['false_approvals']}")
    print(f"False rejections: {result['false_rejections']}")
    print("Confusion matrix (rows=expected, columns=predicted):")
    print("                 APPROVED  PENDING  REJECTED")
    for label in LABELS:
        print(f"{label:12s} {result['confusion_matrix'][label]['APPROVED']:8d} "
              f"{result['confusion_matrix'][label]['PENDING']:8d} "
              f"{result['confusion_matrix'][label]['REJECTED']:9d}")
    print(f"Reports saved to: {REPORT_DIR}")
