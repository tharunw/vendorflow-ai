"""VendorFlow AI — Streamlit prototype UI (Stage 6)."""
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from workflow import CaseManager

ROOT = Path(__file__).resolve().parent

def setting(name, default=""):
    """Read a deployment setting from Streamlit secrets, then environment variables."""
    try:
        value = st.secrets.get(name, None)
        if value is not None and str(value).strip():
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, default)

DB_PATH = Path(setting("VENDORFLOW_DB_PATH", str(ROOT / "vendorflow.db")))
manager = CaseManager(str(DB_PATH))

st.set_page_config(page_title="VendorFlow AI", page_icon="🧾", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
.metric-card {border: 1px solid rgba(128,128,128,.25); border-radius: 12px; padding: 14px;}
.small-muted {color: #777; font-size: .88rem;}
</style>
""", unsafe_allow_html=True)

def status_pill(value):
    colors = {"APPROVED": "🟢", "PENDING": "🟠", "REJECTED": "🔴", "OPEN": "🟠", "CLOSED": "⚫"}
    return f"{colors.get(value, '⚪')} {value}"

def load_payloads():
    path = ROOT / "vendor_submissions.jsonl"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def seed_demo_cases():
    payloads = load_payloads()
    created, skipped = 0, 0
    for payload in payloads:
        try:
            manager.create_case(payload, actor="demo_seed")
            created += 1
        except ValueError:
            skipped += 1
    return created, skipped

def render_magic_link_page(case_id, token):
    st.title("VendorFlow AI — Secure correction")
    st.caption("Vendor self-service correction page · Demo environment")
    data = manager.get_case(case_id)
    if not data:
        st.error("We could not find this case.")
        st.stop()
    if data["case"]["lifecycle_status"] != "OPEN":
        st.success("This case is already closed. No further correction is required.")
        st.stop()
    payload = data["submission"]
    st.info(f"Case {case_id} is open. Update only the information that needs correction.")
    with st.form("vendor_correction_form"):
        st.subheader("Business information")
        legal_name = st.text_input("Legal business name", payload.get("vendor", {}).get("legal_name", ""))
        email = st.text_input("Business email", payload.get("vendor", {}).get("business_email", ""))
        address = st.text_input("Business address", payload.get("vendor", {}).get("business_address", ""))
        st.subheader("Tax information")
        tax_name = st.text_input("Tax registered name", payload.get("tax", {}).get("tax_registered_name", ""))
        tax_id = st.text_input("Tax ID", payload.get("tax", {}).get("tax_id", ""))
        st.subheader("Bank information")
        holder = st.text_input("Bank account holder name", payload.get("bank", {}).get("account_holder_name", ""))
        bank_country = st.text_input("Bank country (ISO code)", payload.get("bank", {}).get("bank_country", ""))
        account_number = st.text_input("Bank account number", payload.get("bank", {}).get("account_number", ""))
        submitted = st.form_submit_button("Submit corrections", type="primary")
    if submitted:
        updates = {}
        for section, key, value in [
            ("vendor", "legal_name", legal_name), ("vendor", "business_email", email),
            ("vendor", "business_address", address), ("tax", "tax_registered_name", tax_name),
            ("tax", "tax_id", tax_id), ("bank", "account_holder_name", holder),
            ("bank", "bank_country", bank_country), ("bank", "account_number", account_number)
        ]:
            old = (payload.get(section) or {}).get(key, "")
            if value != old:
                updates.setdefault(section, {})[key] = value
        if not updates:
            st.warning("No changes detected. Please update at least one field.")
        else:
            try:
                outcome = manager.resubmit(case_id, token, updates, actor="vendor_magic_link")
                st.success("Your corrections were submitted and the application was re-evaluated.")
                st.write("Updated decision:", status_pill(outcome["case"]["assessment"]["decision"]))
                st.write("New version:", outcome["case"]["case"]["current_version"])
                st.subheader("Changes recorded")
                st.dataframe(pd.DataFrame(outcome["diff"]), use_container_width=True, hide_index=True)
                st.caption("Your previous submission remains in the audit history.")
            except (ValueError, KeyError) as exc:
                st.error(str(exc))
    st.stop()

# If the user arrives through a demo magic link, render the vendor correction experience.
query = st.query_params
if query.get("case_id") and query.get("token"):
    render_magic_link_page(str(query.get("case_id")), str(query.get("token")))

st.title("VendorFlow AI")
st.caption("AI-assisted vendor onboarding · Deterministic decisions · Traceable case management")
st.sidebar.title("VendorFlow AI")
page = st.sidebar.radio("Navigation", ["Dashboard", "New submission", "Case details", "About"])
st.sidebar.caption("Prototype · Synthetic data · No real email or external verification")

if page == "Dashboard":
    st.header("Onboarding dashboard")
    cases = manager.list_cases()
    if not cases:
        st.info("No cases yet. Load the synthetic demo cases or create a new submission.")
        if st.button("Load 30 synthetic demo cases", type="primary"):
            created, skipped = seed_demo_cases()
            st.success(f"Loaded {created} cases. Skipped {skipped} existing cases.")
            st.rerun()
    else:
        df = pd.DataFrame(cases)
        total = len(df)
        approved = int((df["business_decision"] == "APPROVED").sum())
        pending = int((df["business_decision"] == "PENDING").sum())
        rejected = int((df["business_decision"] == "REJECTED").sum())
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total cases", total)
        c2.metric("Approved", approved)
        c3.metric("Pending", pending)
        c4.metric("Rejected", rejected)
        st.subheader("Case pipeline")
        pipeline = pd.DataFrame({"Status": ["Approved", "Pending", "Rejected"],
                                 "Cases": [approved, pending, rejected]})
        st.bar_chart(pipeline.set_index("Status"))
        st.subheader("Recent cases")
        view = df.rename(columns={"case_id":"Case ID","vendor_id":"Vendor ID",
                                  "business_decision":"Decision","lifecycle_status":"Lifecycle",
                                  "current_version":"Version","updated_at":"Last updated"})
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.download_button("Download case register (CSV)", df.to_csv(index=False).encode("utf-8"),
                           file_name="vendorflow_case_register.csv", mime="text/csv")
        if st.button("Load any missing synthetic cases"):
            created, skipped = seed_demo_cases()
            st.success(f"Loaded {created} new cases; {skipped} already existed.")
            st.rerun()

elif page == "New submission":
    st.header("New vendor submission")
    st.write("Enter a vendor's information. The deterministic Python engine evaluates the submission.")
    with st.form("new_vendor_form"):
        left, right = st.columns(2)
        with left:
            case_id = st.text_input("Case ID", placeholder="CASE-DEMO-1001")
            vendor_id = st.text_input("Vendor ID", placeholder="VND-DEMO-1001")
            legal_name = st.text_input("Legal business name")
            country = st.selectbox("Business country", ["IN", "US", "GB", "AE", "SG"])
            business_type = st.selectbox("Business type", ["PRIVATE_LIMITED", "LLP", "SOLE_PROPRIETORSHIP", "PARTNERSHIP"])
            email = st.text_input("Business email")
            address = st.text_input("Business address")
        with right:
            tax_type = st.selectbox("Tax ID type", ["GSTIN", "PAN", "EIN", "UK_VAT"])
            tax_id = st.text_input("Tax ID")
            tax_name = st.text_input("Tax registered name")
            bank_country = st.selectbox("Bank country", ["IN", "US", "GB", "AE", "SG"])
            holder = st.text_input("Bank account holder name")
            account_number = st.text_input("Bank account number")
            ifsc = st.text_input("IFSC (India only; optional)")
        create = st.form_submit_button("Evaluate and create case", type="primary")
    if create:
        if not case_id.strip() or not vendor_id.strip():
            st.error("Case ID and Vendor ID are required.")
        else:
            payload = {
                "case_id": case_id.strip(), "vendor_id": vendor_id.strip(), "submission_version": 1,
                "vendor": {"legal_name": legal_name, "country": country, "business_type": business_type,
                           "business_email": email, "business_address": address},
                "tax": {"tax_type": tax_type, "tax_id": tax_id, "tax_registered_name": tax_name},
                "bank": {"account_holder_name": holder, "account_number": account_number,
                         "bank_country": bank_country, "ifsc": ifsc},
                "documents": [],
                "metadata": {"submission_source": "STREAMLIT_FORM", "is_existing_vendor": False,
                             "synthetic_fixture": False}
            }
            try:
                created = manager.create_case(payload, actor="streamlit_user")
                result = created["assessment"]
                st.success(f"Case created: {case_id}")
                a,b,c = st.columns(3)
                a.metric("Decision", result["decision"])
                b.metric("Lifecycle", result["lifecycle_status"])
                c.metric("Risk score", result["risk_score"])
                st.write(result["summary"])
                if result.get("pending_reasons"):
                    st.subheader("Items requiring attention")
                    for reason in result["pending_reasons"]:
                        st.warning(reason)
                st.json(result["validations"])
            except ValueError as exc:
                st.error(str(exc))

elif page == "Case details":
    st.header("Case details")
    cases = manager.list_cases()
    if not cases:
        st.info("No cases available. Load demo cases from the Dashboard.")
    else:
        options = [x["case_id"] for x in cases]
        selected = st.selectbox("Select a case", options)
        data = manager.get_case(selected)
        case, result = data["case"], data["assessment"]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Decision", case["business_decision"])
        c2.metric("Lifecycle", case["lifecycle_status"])
        c3.metric("Version", case["current_version"])
        c4.metric("Risk score", result["risk_score"])
        st.subheader("Decision summary")
        st.write(result["summary"])
        t1,t2,t3,t4 = st.tabs(["Risk & validations", "Submission", "Corrections", "Audit timeline"])
        with t1:
            if result["risk_flags"]:
                st.dataframe(pd.DataFrame(result["risk_flags"]), use_container_width=True, hide_index=True)
            else:
                st.success("No risk flags in the latest assessment.")
            st.dataframe(pd.DataFrame(result["validations"]), use_container_width=True, hide_index=True)
        with t2:
            st.json(data["submission"])
        with t3:
            if case["lifecycle_status"] == "OPEN":
                col1,col2 = st.columns(2)
                with col1:
                    if st.button("Generate correction email draft"):
                        draft = manager.create_correction_email(selected)
                        st.session_state["latest_draft"] = draft
                with col2:
                    if st.button("Generate one-time magic link"):
                        base_url = setting("VENDORFLOW_BASE_URL", "http://localhost:8501")
                        st.session_state["latest_link"] = manager.create_magic_link(selected, base_url=base_url)
                if st.session_state.get("latest_draft"):
                    draft = st.session_state["latest_draft"]
                    st.markdown("**Email draft (not sent)**")
                    st.text_input("Recipient", draft["recipient"])
                    st.text_area("Subject", draft["subject"])
                    st.text_area("Email body", draft["body"], height=220)
                if st.session_state.get("latest_link"):
                    st.markdown("**Demo correction link**")
                    st.code(st.session_state["latest_link"])
                    st.caption("Local demo link only. A deployed version must use HTTPS and authenticated access.")
            else:
                st.info("This case is closed. Corrections are disabled.")
            if data["email_drafts"]:
                st.markdown("**Saved email drafts**")
                for draft in data["email_drafts"]:
                    with st.expander(f"Draft #{draft['draft_id']} · {draft['subject']}"):
                        st.write(draft["body"])
        with t4:
            if data["audit_log"]:
                audit = pd.DataFrame(data["audit_log"])
                st.dataframe(audit[["audit_id","event_type","actor","details_json","created_at"]],
                             use_container_width=True, hide_index=True)
            else:
                st.info("No audit events found.")

else:
    st.header("About VendorFlow AI")
    st.markdown("""
    **Problem:** Vendor onboarding is slowed by incomplete submissions, mismatched records and repeated email follow-ups.

    **Solution:** VendorFlow AI extracts and validates submitted information, applies deterministic rules, keeps correctable cases open, and records every submission version and decision.

    **Architecture**
    - Streamlit: operator and vendor-facing prototype UI
    - Python engine: deterministic validation, risk scoring and decision policy
    - SQLite: cases, submissions, assessments, email drafts, magic-link hashes and audit trail
    - Synthetic JSONL records: repeatable demonstration dataset

    **Important boundaries**
    - The decision engine is a prototype policy, not legal or compliance approval.
    - Tax and bank identifier checks are format-level checks, not external verification.
    - Email drafts are not sent.
    - Demo magic links are local-only; production needs HTTPS, authentication, rate limits and access controls.
    - Synthetic records and documents are fictional.
    """)
