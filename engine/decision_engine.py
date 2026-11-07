"""Final deterministic decision policy."""
HARD_REJECTION_KEYS = {
    "CONFIRMED_FABRICATED_DOCUMENT",
    "CONFIRMED_FABRICATED_IDENTITY"
}

def decide(validations, risk_score, hard_rejection_reasons=None):
    hard_rejection_reasons = hard_rejection_reasons or []
    if hard_rejection_reasons:
        return "REJECTED", "CLOSED", hard_rejection_reasons, []

    failed = [v for v in validations if not v.passed]
    pending = [v.reason for v in failed]
    if failed:
        # Even high risk remains pending unless confirmed disqualifying evidence
        # is independently established and explicitly supplied as a hard rule.
        return "PENDING", "OPEN", [], pending

    if risk_score >= 20:
        return "PENDING", "OPEN", [], ["Risk threshold requires human review."]
    return "APPROVED", "CLOSED", [], []

def run_decision_engine(submission, validations, risk_score):
    """Apply trusted benchmark evidence, not an LLM inference, for hard rejects."""
    metadata = submission.get("metadata") or {}
    hard = []
    if metadata.get("confirmed_fraud") is True:
        hard.append("Confirmed fabricated evidence explicitly recorded in benchmark metadata.")
    decision, lifecycle, rejection_reasons, pending_reasons = decide(
        validations, risk_score, hard
    )
    return decision, lifecycle, rejection_reasons, pending_reasons
