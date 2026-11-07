"""Explainable fuzzy name matching using stdlib only."""
import re
from difflib import SequenceMatcher
from .models import NameMatchResult

LEGAL_SUFFIXES = {
    "PRIVATE", "LIMITED", "LTD", "PVT", "LLP", "LLC", "INC",
    "INCORPORATED", "CORPORATION", "CORP", "PLC", "COMPANY", "CO"
}

def normalize_name(value):
    value = (value or "").upper()
    value = re.sub(r"[^A-Z0-9 ]", " ", value)
    tokens = [t for t in value.split() if t not in LEGAL_SUFFIXES]
    return " ".join(tokens)

def similarity(a, b):
    """Return a 0-100 normalized similarity score."""
    left, right = normalize_name(a), normalize_name(b)
    if not left or not right:
        return 0.0
    return round(100 * SequenceMatcher(None, left, right).ratio(), 2)

def compare_names(label_a, value_a, label_b, value_b):
    score = similarity(value_a, value_b)
    if score >= 97:
        hint = "STRONG_MATCH"
    elif score >= 85:
        hint = "REVIEW"
    else:
        hint = "MISMATCH"
    return NameMatchResult(
        left_label=label_a, right_label=label_b,
        left_value=value_a or "", right_value=value_b or "",
        score=score, decision_hint=hint
    )
