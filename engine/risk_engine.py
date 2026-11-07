"""Weighted risk scoring. Only failed validations contribute weight."""
def calculate_risk(validations):
    score = min(100, sum(v.weight for v in validations if not v.passed))
    flags = []
    for v in validations:
        if not v.passed:
            flags.append({
                "rule_id": v.rule_id,
                "check": v.check,
                "severity": v.severity,
                "weight": v.weight,
                "reason": v.reason,
                "field": v.field
            })
    return score, flags
