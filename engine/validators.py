"""Deterministic validation rules for VendorFlow AI.

These checks validate structure, consistency and synthetic reference matches.
They do NOT query government, tax authority or banking systems.
"""
import re
from .models import ValidationResult

PAN_RE = re.compile(r"^[A-Z]{3}[ABCFGHJLPT][A-Z][0-9]{4}[A-Z]$")
GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
EIN_RE = re.compile(r"^[0-9]{2}-?[0-9]{7}$")
UK_VAT_RE = re.compile(r"^(?:GB)?[0-9]{9}(?:[0-9]{3})?$")
IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
US_ROUTING_RE = re.compile(r"^[0-9]{9}$")
UK_SORT_RE = re.compile(r"^[0-9]{2}-?[0-9]{2}-?[0-9]{2}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
FREE_MAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "icloud.com", "proton.me", "protonmail.com"
}
VALID_IN_STATE_CODES = {f"{i:02d}" for i in range(1, 39)} | {"97", "99"}
ALPHABET36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def result(rule_id, check, passed, severity, weight, reason, field=None, evidence=None):
    return ValidationResult(rule_id, check, passed, severity, weight, reason,
                            field, evidence or {})

def gstin_check_character(first14):
    """Widely used GSTIN base-36 Luhn-style check-character calculation."""
    value = first14.upper()
    if len(value) != 14 or any(ch not in ALPHABET36 for ch in value):
        raise ValueError("GSTIN checksum requires 14 base-36 characters")
    total = 0
    for index, char in enumerate(value):
        product = ALPHABET36.index(char) * (1 if index % 2 == 0 else 2)
        total += product // 36 + product % 36
    return ALPHABET36[(36 - (total % 36)) % 36]

def validate_gstin(value):
    value = (value or "").strip().upper()
    if not GSTIN_RE.fullmatch(value):
        return False, "GSTIN must have the expected 15-character structure."
    if value[:2] not in VALID_IN_STATE_CODES:
        return False, "GSTIN contains an unrecognized state/territory code."
    embedded_pan = value[2:12]
    if not PAN_RE.fullmatch(embedded_pan):
        return False, "The PAN embedded in the GSTIN has an invalid structure."
    if value[13] != "Z":
        return False, "GSTIN position 14 must be Z for this prototype's regular registration pattern."
    expected = gstin_check_character(value[:14])
    if value[-1] != expected:
        return False, f"GSTIN checksum mismatch: expected final character {expected}."
    return True, "GSTIN structure and checksum passed; active registration is not verified."

def validate_pan(value):
    value = (value or "").strip().upper()
    return bool(PAN_RE.fullmatch(value))

def validate_tax(country, tax_type, tax_id):
    country = (country or "").upper()
    tax_type = (tax_type or "").upper()
    value = (tax_id or "").strip().upper()

    if not value:
        return result("R004", "Tax identifier present", False, "MEDIUM", 10,
                      "Tax identifier is missing; vendor can provide it.", "tax.tax_id")
    if country == "IN":
        if tax_type == "GSTIN":
            ok, reason = validate_gstin(value)
            return result("R004", "GSTIN structure and checksum", ok,
                          "HIGH", 15 if not ok else 0, reason, "tax.tax_id")
        if tax_type == "PAN":
            ok = validate_pan(value)
            return result("R004", "PAN format", ok, "HIGH", 15 if not ok else 0,
                          "PAN format passed." if ok else "PAN format is invalid.",
                          "tax.tax_id")
        return result("R010", "Tax type matches country", False, "HIGH", 15,
                      "India requires GSTIN or PAN in this prototype.", "tax.tax_type")

    if country == "US":
        ok = tax_type == "EIN" and bool(EIN_RE.fullmatch(value))
        return result("R004", "US EIN format", ok, "HIGH", 15 if not ok else 0,
                      "EIN format passed; IRS registration is not verified." if ok
                      else "US tax identifier must be an EIN in NN-NNNNNNN format.",
                      "tax.tax_id")

    if country == "GB":
        ok = tax_type == "VAT" and bool(UK_VAT_RE.fullmatch(value))
        return result("R004", "UK VAT format", ok, "HIGH", 15 if not ok else 0,
                      "UK VAT format passed; HMRC registration and ownership are not verified." if ok
                      else "UK tax identifier must be a 9-digit VAT number (optionally with 3-digit branch suffix).",
                      "tax.tax_id")

    return result("R003", "Supported country", False, "HIGH", 15,
                  "Country is not supported by this prototype.", "vendor.country")

def validate_ifsc(value):
    return bool(IFSC_RE.fullmatch((value or "").strip().upper()))

def validate_bank_identifier(country, bank):
    if country == "IN":
        value = bank.get("ifsc")
        ok = validate_ifsc(value)
        reason = "IFSC structure passed; bank/account existence is not verified." if ok else "Indian bank details require an IFSC matching the expected format."
    elif country == "US":
        value = bank.get("routing_number", "")
        ok = bool(US_ROUTING_RE.fullmatch(str(value)))
        reason = "Routing number has nine digits; checksum/bank ownership not verified." if ok else "US routing number must contain nine digits."
    elif country == "GB":
        value = bank.get("sort_code", "")
        ok = bool(UK_SORT_RE.fullmatch(str(value)))
        reason = "UK sort code structure passed; account ownership not verified." if ok else "UK sort code must contain six digits."
    else:
        return result("R008", "Bank identifier format", False, "HIGH", 15,
                      "Bank country is not supported for bank identifier validation.",
                      "bank.bank_country")
    return result("R008", "Bank identifier format", ok, "HIGH", 15 if not ok else 0,
                  reason, "bank")

def validate_submission(submission):
    """Return field, tax, bank, email, cross-field and document validation results."""
    vendor = submission.get("vendor") or {}
    tax = submission.get("tax") or {}
    bank = submission.get("bank") or {}
    metadata = submission.get("metadata") or {}
    docs = submission.get("documents") or []
    results = []

    required = [
        ("vendor.legal_name", vendor.get("legal_name")),
        ("vendor.country", vendor.get("country")),
        ("vendor.business_email", vendor.get("business_email")),
        ("vendor.business_address", vendor.get("business_address")),
        ("tax.tax_type", tax.get("tax_type")),
        ("tax.tax_id", tax.get("tax_id")),
        ("bank.account_holder_name", bank.get("account_holder_name")),
        ("bank.account_number", bank.get("account_number")),
        ("bank.bank_country", bank.get("bank_country"))
    ]
    missing = [path for path, value in required if value is None or str(value).strip() == ""]
    results.append(result("R001", "Mandatory business fields", not missing,
                          "MEDIUM", 10 if missing else 0,
                          "Missing fields: " + ", ".join(missing) if missing else
                          "All mandatory business fields are present.",
                          "submission", {"missing_fields": missing}))

    country = (vendor.get("country") or "").upper()
    email = (vendor.get("business_email") or "").strip().lower()
    email_ok = bool(EMAIL_RE.fullmatch(email))
    results.append(result("R002", "Business email syntax", email_ok, "MEDIUM",
                          5 if not email_ok else 0,
                          "Business email syntax passed." if email_ok else
                          "Business email is missing or has invalid syntax.",
                          "vendor.business_email"))

    domain = email.rsplit("@", 1)[-1] if "@" in email else ""
    free_mail = domain in FREE_MAIL_DOMAINS
    results.append(result("R011", "Business email domain", not free_mail, "LOW",
                          3 if free_mail else 0,
                          "Free-mail provider detected; this is a contextual signal, not proof of fraud."
                          if free_mail else "No known free-mail domain flag.",
                          "vendor.business_email", {"domain": domain}))

    tax_result = validate_tax(country, tax.get("tax_type"), tax.get("tax_id"))
    results.append(tax_result)

    tax_country_match = (
        (country == "IN" and tax.get("tax_type") in {"GSTIN", "PAN"}) or
        (country == "US" and tax.get("tax_type") == "EIN") or
        (country == "GB" and tax.get("tax_type") == "VAT")
    )
    results.append(result("R010", "Tax type-country consistency", tax_country_match,
                          "HIGH", 15 if not tax_country_match else 0,
                          "Tax identifier type does not match the declared country."
                          if not tax_country_match else "Tax type is consistent with declared country.",
                          "tax.tax_type"))

    bank_country = (bank.get("bank_country") or "").upper()
    country_match = bank_country == country
    results.append(result("R009", "Business-bank country consistency", country_match,
                          "MEDIUM", 10 if not country_match else 0,
                          "Bank country differs from business country; cross-border banking may be legitimate but requires review."
                          if not country_match else "Business and bank country match.",
                          "bank.bank_country"))

    results.append(validate_bank_identifier(bank_country, bank))

    # Tax record name is supplied by the synthetic reference/extraction layer.
    tax_name = tax.get("tax_registered_name") or ""
    legal_name = vendor.get("legal_name") or ""
    tax_name_present = bool(tax_name.strip())
    results.append(result("R006", "Tax registration name present", tax_name_present,
                          "MEDIUM", 0 if tax_name_present else 10,
                          "Tax registered name is available for comparison." if tax_name_present
                          else "Tax registered name is missing; obtain a registration record.",
                          "tax.tax_registered_name"))

    # Documents are evaluated independently. Wrong/unreadable docs are pending
    # replacement; they do not trigger case-level hard rejection by themselves.
    required_doc_types = {"BANK_PROOF"}
    supplied_types = {d.get("document_type") for d in docs}
    missing_docs = sorted(required_doc_types - supplied_types)
    results.append(result("R013", "Required bank proof present", not missing_docs,
                          "MEDIUM", 10 if missing_docs else 0,
                          "Missing required documents: " + ", ".join(missing_docs)
                          if missing_docs else "Required bank proof is present.",
                          "documents", {"missing_document_types": missing_docs}))

    # Synthetic benchmark metadata can mark a document as unreadable or wrong.
    bad_docs = [d for d in docs if d.get("quality") in {"UNREADABLE", "WRONG_TYPE"}]
    results.append(result("R014", "Document quality and type", not bad_docs,
                          "MEDIUM", 10 if bad_docs else 0,
                          "One or more documents need replacement; other case data is retained."
                          if bad_docs else "No document-quality issue was supplied to the engine.",
                          "documents", {"affected_document_ids": [d.get("document_id") for d in bad_docs]}))

    # Existing vendor bank changes are a hold for independent verification.
    changed = bool(metadata.get("existing_bank_details_changed"))
    results.append(result("R012", "Existing vendor bank detail change", not changed,
                          "HIGH", 25 if changed else 0,
                          "Existing vendor bank details changed; independent confirmation is required."
                          if changed else "No existing-vendor bank change was declared.",
                          "bank.account_number"))

    return results
