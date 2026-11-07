"""Shared result structures for the VendorFlow deterministic engine."""
from dataclasses import asdict, dataclass, field as dc_field
from typing import Any, Dict, List, Optional

@dataclass
class ValidationResult:
    rule_id: str
    check: str
    passed: bool
    severity: str
    weight: int
    reason: str
    field: Optional[str] = None
    evidence: Dict[str, Any] = dc_field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

@dataclass
class NameMatchResult:
    left_label: str
    right_label: str
    left_value: str
    right_value: str
    score: float
    decision_hint: str

    def to_dict(self):
        return asdict(self)

@dataclass
class EngineResult:
    case_id: str
    vendor_id: str
    risk_score: int
    decision: str
    lifecycle_status: str
    validations: List[ValidationResult] = dc_field(default_factory=list)
    name_matches: List[NameMatchResult] = dc_field(default_factory=list)
    risk_flags: List[Dict[str, Any]] = dc_field(default_factory=list)
    hard_rejection_reasons: List[str] = dc_field(default_factory=list)
    pending_reasons: List[str] = dc_field(default_factory=list)
    summary: str = ""

    def to_dict(self):
        return {
            "case_id": self.case_id,
            "vendor_id": self.vendor_id,
            "risk_score": self.risk_score,
            "decision": self.decision,
            "lifecycle_status": self.lifecycle_status,
            "validations": [x.to_dict() for x in self.validations],
            "name_matches": [x.to_dict() for x in self.name_matches],
            "risk_flags": self.risk_flags,
            "hard_rejection_reasons": self.hard_rejection_reasons,
            "pending_reasons": self.pending_reasons,
            "summary": self.summary
        }
