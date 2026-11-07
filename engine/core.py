"""Public entry point for the VendorFlow AI deterministic engine."""
from .validators import validate_submission
from .name_matcher import compare_names
from .risk_engine import calculate_risk
from .decision_engine import run_decision_engine
from .models import EngineResult

def evaluate_submission(submission):
    validations = validate_submission(submission)
    vendor = submission.get("vendor") or {}
    tax = submission.get("tax") or {}
    bank = submission.get("bank") or {}

    name_matches = [
        compare_names("Legal name", vendor.get("legal_name", ""),
                      "Tax record name", tax.get("tax_registered_name", "")),
        compare_names("Legal name", vendor.get("legal_name", ""),
                      "Bank holder name", bank.get("account_holder_name", ""))
    ]

    # Name mismatch thresholds are risk signals; they are not identity proof.
    for idx, match in enumerate(name_matches):
        if match.score < 97:
            from .models import ValidationResult
            validations.append(ValidationResult(
                rule_id="R007" if idx == 1 else "R006",
                check=f"{match.left_label} vs {match.right_label}",
                passed=False,
                severity="MEDIUM" if match.score >= 80 else "HIGH",
                weight=15 if idx == 1 else 10,
                reason=f"Name similarity is {match.score:.2f}%; verify supporting evidence.",
                field="bank.account_holder_name" if idx == 1 else "tax.tax_registered_name",
                evidence={"similarity_score": match.score}
            ))

    risk_score, flags = calculate_risk(validations)
    decision, lifecycle, hard_reasons, pending_reasons = run_decision_engine(
        submission, validations, risk_score
    )

    case_id = submission.get("case_id") or "CASE-UNASSIGNED"
    vendor_id = submission.get("vendor_id") or "VND-UNASSIGNED"
    if decision == "APPROVED":
        summary = "All implemented checks passed. Eligible for approval under the prototype policy."
    elif decision == "REJECTED":
        summary = "Rejected because confirmed disqualifying evidence was explicitly supplied."
    else:
        summary = "Case remains open. Resolve the listed exceptions or complete human review."

    return EngineResult(
        case_id=case_id, vendor_id=vendor_id, risk_score=risk_score,
        decision=decision, lifecycle_status=lifecycle,
        validations=validations, name_matches=name_matches,
        risk_flags=flags, hard_rejection_reasons=hard_reasons,
        pending_reasons=pending_reasons, summary=summary
    )
