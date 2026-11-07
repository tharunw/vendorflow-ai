#!/usr/bin/env python3
"""
VendorFlow AI - Stage 3 synthetic dataset generator.

Generates 30 fictional vendor onboarding submissions, sample text documents,
ground-truth labels, JSONL, CSV, and a dataset summary.

No third-party packages are required.
Run: python generate_dataset.py
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import csv
import json
import random

SEED = 42
NAMES = [
    ("Aarav", "Mehta"), ("Isha", "Reddy"), ("Kabir", "Shah"),
    ("Mira", "Nair"), ("Dev", "Kapoor"), ("Anaya", "Rao"),
    ("Neil", "Patel"), ("Tara", "Iyer"), ("Rohan", "Das"),
    ("Sana", "Khan"), ("Arjun", "Pillai"), ("Diya", "Joshi"),
    ("Vivaan", "Menon"), ("Kiara", "Singh"), ("Aditya", "Gupta"),
    ("Myra", "Bose"), ("Reyansh", "Kulkarni"), ("Aisha", "Thomas"),
    ("Ishaan", "Verma"), ("Sara", "Mishra"), ("Ayaan", "Sharma"),
    ("Nisha", "Raman"), ("Krish", "Sethi"), ("Riya", "Chawla"),
    ("Om", "Bhat"), ("Zoya", "Ali"), ("Manav", "Desai"),
    ("Aditi", "Sen"), ("Yash", "Kumar"), ("Leela", "Fernandes")
]

def make_vendor_name(first, last, i):
    stem = f"{first} {last}"
    suffixes = ["Technologies Private Limited", "Trading Solutions LLP",
                "Industrial Services Private Limited", "Digital Systems LLC",
                "Consulting Limited"]
    return f"{stem} {suffixes[i % len(suffixes)]}"

def make_tax_id(country, i):
    # Deliberately synthetic identifiers. These are test fixtures, not real
    # registrations and are not guaranteed to pass official checksum/API checks.
    if country == "IN":
        pan = f"ABCCA{(i+1):04d}F"
        first14 = f"29{pan}1Z"
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        total = 0
        for pos, ch in enumerate(first14):
            product = alphabet.index(ch) * (1 if pos % 2 == 0 else 2)
            total += product // 36 + product % 36
        check = alphabet[(36 - (total % 36)) % 36]
        return "GSTIN", first14 + check
    if country == "US":
        return "EIN", f"{20 + (i % 70):02d}-{1000000 + i:07d}"
    return "VAT", f"GB{100000000 + i:09d}"

def write_document(doc_dir, doc_id, doc_type, vendor_name, content, suffix=".txt"):
    filename = f"{doc_id.lower()}_{doc_type.lower()}{suffix}"
    path = doc_dir / filename
    path.write_text(content, encoding="utf-8")
    return {
        "document_id": doc_id,
        "document_type": doc_type,
        "file_name": filename,
        "relative_path": f"documents/{filename}"
    }

def build_dataset(output_dir="."):
    out = Path(output_dir)
    docs = out / "documents"
    docs.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    now = datetime(2026, 11, 6, 10, 0, tzinfo=timezone.utc)

    scenarios = (
        ["CLEAN"] * 8 +
        ["INCOMPLETE"] * 5 +
        ["NAME_MISMATCH"] * 5 +
        ["CROSS_COUNTRY"] * 4 +
        ["EXISTING_BANK_CHANGE"] * 4 +
        ["CONFIRMED_SYNTHETIC_FRAUD"] * 2 +
        ["BAD_DOCUMENT"] * 2
    )
    rng.shuffle(scenarios)

    submissions, truth = [], []
    for i, scenario in enumerate(scenarios, start=1):
        first, last = NAMES[i-1]
        country = ["IN", "US", "GB"][i % 3]
        legal_name = make_vendor_name(first, last, i)
        tax_type, tax_id = make_tax_id(country, i)
        email_domain = {"IN": "example.in", "US": "example.com",
                        "GB": "example.co.uk"}[country]
        email = f"finance.vendor{i:02d}@{email_domain}"
        bank_country = country
        bank_holder = legal_name
        account_number = f"TEST-{i:04d}-{1000+i:04d}"
        bank_identifier = {}
        if country == "IN":
            bank_identifier["ifsc"] = f"TEST000{i:04d}"
        elif country == "US":
            bank_identifier["routing_number"] = f"{100000000 + i:09d}"
        else:
            bank_identifier["sort_code"] = f"{10+i:02d}-{20+i:02d}-{30+i:02d}"

        is_existing = scenario == "EXISTING_BANK_CHANGE"
        if is_existing:
            # Existing vendor's new account is deliberately different from
            # the synthetic baseline stored in metadata.
            account_number = f"NEW-{i:04d}-{7000+i:04d}"
        if scenario == "NAME_MISMATCH":
            bank_holder = legal_name.replace("Limited", "Ltd").replace(
                "Technologies", "Technology Services")
        if scenario == "CROSS_COUNTRY":
            # An Indian tax identity with a UAE bank is a deliberate cross-field
            # inconsistency. The free-mail domain is an additional signal.
            country = "IN"
            tax_type, tax_id = make_tax_id("IN", i)
            bank_country = "AE"
            email = f"vendor{i:02d}@gmail.com"
            bank_identifier = {"iban": f"AE00TEST{i:016d}"}
        if scenario == "CONFIRMED_SYNTHETIC_FRAUD":
            # Explicit labelled fixture: the benchmark says this document is
            # fabricated. This is not an inference from a format mismatch.
            legal_name = f"Fictional Shell Entity {i}"
        submitted_at = (now + timedelta(minutes=i * 7)).isoformat().replace("+00:00", "Z")

        documents = []
        gst_or_tax_type = {
            "IN": "GST_CERTIFICATE", "US": "EIN_DOCUMENT", "GB": "VAT_CERTIFICATE"
        }.get(country, "BUSINESS_REGISTRATION")
        d1 = f"DOC-{i:04d}-01"
        doc_content = (
            f"SYNTHETIC TEST DOCUMENT\nDocument type: {gst_or_tax_type}\n"
            f"Registered entity: {legal_name}\nTax identifier: {tax_id}\n"
            "NOTICE: Fictional test fixture; not an official certificate.\n"
        )
        if scenario == "CONFIRMED_SYNTHETIC_FRAUD":
            doc_content += "BENCHMARK_LABEL: CONFIRMED_FABRICATED_DOCUMENT\n"
        documents.append(write_document(
            docs, d1, gst_or_tax_type, legal_name, doc_content
        ))
        d2 = f"DOC-{i:04d}-02"
        bank_doc = (
            f"SYNTHETIC BANK PROOF\nAccount holder: {bank_holder}\n"
            f"Account reference: {account_number}\nBank country: {bank_country}\n"
            "NOTICE: Fictional test fixture; not a real bank statement.\n"
        )
        documents.append(write_document(docs, d2, "BANK_PROOF", legal_name, bank_doc))

        vendor = {
            "legal_name": legal_name,
            "country": country,
            "business_type": "PRIVATE_LIMITED",
            "business_email": email,
            "business_address": f"Test Business Park, Unit {i}, Fictional City"
        }
        tax = {
            "tax_type": tax_type,
            "tax_id": tax_id,
            "tax_registered_name": legal_name
        }
        bank = {
            "account_holder_name": bank_holder,
            "account_number": account_number,
            "bank_country": bank_country,
            **bank_identifier
        }
        expected_decision = "APPROVED"
        expected_flags = []
        expected_document_status = "ACCEPTED"
        expected_reason = "All synthetic benchmark checks are expected to pass."

        if scenario == "INCOMPLETE":
            # Keep structure intact but remove a business value so the case
            # enters business validation and becomes PENDING, not schema-rejected.
            if i % 2:
                vendor["business_address"] = ""
                expected_flags.append("MISSING_BUSINESS_ADDRESS")
            else:
                tax["tax_id"] = ""
                expected_flags.append("MISSING_TAX_ID")
            expected_decision = "PENDING"
            expected_reason = "Required information is missing and can be supplied by the vendor."

        elif scenario == "NAME_MISMATCH":
            expected_decision = "PENDING"
            expected_flags = ["BANK_HOLDER_NAME_MISMATCH"]
            expected_reason = "Bank account holder differs from the submitted legal entity name; request evidence or review."

        elif scenario == "CROSS_COUNTRY":
            expected_decision = "PENDING"
            expected_flags = ["BANK_COUNTRY_MISMATCH", "FREE_MAIL_DOMAIN"]
            expected_reason = "Country, tax registration, bank country and email domain are inconsistent; request clarification."

        elif scenario == "EXISTING_BANK_CHANGE":
            expected_decision = "PENDING"
            expected_flags = ["EXISTING_VENDOR_BANK_CHANGE", "INDEPENDENT_CONFIRMATION_REQUIRED"]
            expected_reason = "Existing vendor payment details changed; hold for independent verification."

        elif scenario == "CONFIRMED_SYNTHETIC_FRAUD":
            expected_decision = "REJECTED"
            expected_flags = ["CONFIRMED_FABRICATED_DOCUMENT"]
            expected_reason = "Ground-truth fixture explicitly labels the submitted document as fabricated."

        elif scenario == "BAD_DOCUMENT":
            expected_decision = "PENDING"
            expected_document_status = "REJECTED"
            expected_flags = ["DOCUMENT_UNREADABLE_OR_WRONG_TYPE"]
            expected_reason = "One document is unusable; request replacement while keeping the case open."
            # Replace the bank proof with a clearly low-quality placeholder.
            bad_name = f"doc-{i:04d}-02_bad_document.txt"
            (docs / documents[1]["file_name"]).unlink()
            (docs / bad_name).write_text(
                "LOW QUALITY SCAN: unreadable placeholder; no extractable account holder or bank details.\n",
                encoding="utf-8"
            )
            documents[1]["file_name"] = bad_name
            documents[1]["relative_path"] = f"documents/{bad_name}"

        metadata = {
            "submission_source": "WEB_FORM",
            "submitted_at": submitted_at,
            "is_existing_vendor": is_existing,
            "synthetic_fixture": True
        }
        if is_existing:
            metadata["previous_bank_account_masked"] = f"****{1000+i:04d}"
            metadata["independent_confirmation_required"] = True

        submission = {
            "case_id": f"CASE-{i:04d}",
            "vendor_id": f"VND-{i:04d}",
            "submission_version": 1,
            "vendor": vendor,
            "tax": tax,
            "bank": bank,
            "documents": documents,
            "metadata": metadata
        }
        submissions.append(submission)
        truth.append({
            "case_id": submission["case_id"],
            "vendor_id": submission["vendor_id"],
            "scenario": scenario,
            "expected_decision": expected_decision,
            "expected_flags": expected_flags,
            "expected_document_status": expected_document_status,
            "expected_reason": expected_reason,
            "is_touchless_eligible": scenario == "CLEAN"
        })

    with (out / "vendor_submissions.jsonl").open("w", encoding="utf-8") as f:
        for row in submissions:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    flat_rows = []
    truth_by_case = {x["case_id"]: x for x in truth}
    for row in submissions:
        label = truth_by_case[row["case_id"]]
        flat_rows.append({
            "case_id": row["case_id"],
            "vendor_id": row["vendor_id"],
            "scenario": label["scenario"],
            "expected_decision": label["expected_decision"],
            "country": row["vendor"]["country"],
            "legal_name": row["vendor"]["legal_name"],
            "business_email": row["vendor"]["business_email"],
            "tax_type": row["tax"]["tax_type"],
            "tax_id": row["tax"]["tax_id"],
            "tax_registered_name": row["tax"]["tax_registered_name"],
            "bank_holder_name": row["bank"]["account_holder_name"],
            "bank_country": row["bank"]["bank_country"],
            "is_existing_vendor": row["metadata"]["is_existing_vendor"],
            "expected_document_status": label["expected_document_status"],
            "expected_flags": "|".join(label["expected_flags"])
        })
    with (out / "vendor_submissions.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(flat_rows[0].keys()))
        writer.writeheader()
        writer.writerows(flat_rows)

    with (out / "ground_truth.json").open("w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2, ensure_ascii=False)

    counts = {}
    decisions = {}
    for item in truth:
        counts[item["scenario"]] = counts.get(item["scenario"], 0) + 1
        decisions[item["expected_decision"]] = decisions.get(item["expected_decision"], 0) + 1
    summary = {
        "dataset_name": "VendorFlow AI synthetic onboarding benchmark",
        "seed": SEED,
        "total_cases": len(submissions),
        "scenario_counts": counts,
        "expected_decision_counts": decisions,
        "documents_generated": sum(len(x["documents"]) for x in submissions),
        "synthetic_only": True,
        "warning": "Fictional test fixtures; not real businesses, bank records, tax registrations, or official verification."
    }
    with (out / "dataset_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    print(f"Generated files in: {out.resolve()}")

if __name__ == "__main__":
    build_dataset(Path(__file__).resolve().parent)
