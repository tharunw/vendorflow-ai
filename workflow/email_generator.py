"""Creates drafts only; this prototype does not send email."""
def build_correction_email(payload, result):
    reasons = result.get("pending_reasons") or []
    vendor = payload.get("vendor") or {}
    recipient = vendor.get("business_email") or ""
    lines = [
        f"Hello {(vendor.get('legal_name') or 'Vendor')},",
        "",
        "Thank you for submitting your vendor onboarding application.",
        "We have reviewed the information. The application is still open and needs the following clarification(s):",
    ]
    if reasons:
        lines.extend([f"- {reason}" for reason in reasons])
    else:
        lines.append("- Please review the highlighted fields with our onboarding team.")
    lines += ["", "Please use the secure correction link provided separately to update only the requested information.",
              "Your previous submission is retained in our audit history.",
              "", "Regards,", "Vendor Onboarding Team"]
    return {"recipient": recipient, "subject": f"Action required: vendor onboarding {payload.get('case_id','')}",
            "body": "\n".join(lines)}
