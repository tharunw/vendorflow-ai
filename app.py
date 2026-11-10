"""VendorFlow AI — redesigned Streamlit prototype UI.
Keeps the existing deterministic engine, SQLite workflow, correction links and audit trail.
"""
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

st.set_page_config(
    page_title="VendorFlow AI | Vendor Operations",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- Visual system -----------------------------
st.markdown(
    """
    <style>
    :root {
        --vf-bg: #0b1120;
        --vf-panel: #111c2f;
        --vf-panel-2: #16243a;
        --vf-border: #26364f;
        --vf-text: #e8eef8;
        --vf-muted: #91a2ba;
        --vf-blue: #5b9cff;
        --vf-green: #35c99a;
        --vf-amber: #f5b942;
        --vf-red: #ff6b78;
    }
    html, body, [data-testid="stAppViewContainer"] {
        background: var(--vf-bg);
        color: var(--vf-text);
    }
    [data-testid="stHeader"] { background: rgba(11,17,32,.92); }
    [data-testid="stToolbar"] { right: 1rem; }
    .block-container {
        max-width: 1500px;
        padding-top: 1.7rem;
        padding-bottom: 3rem;
    }
    [data-testid="stSidebar"] {
        background: #0e1829;
        border-right: 1px solid var(--vf-border);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: var(--vf-muted);
    }
    h1, h2, h3 { color: #f4f7fc !important; letter-spacing: -.025em; }
    h1 { font-size: 2.25rem !important; font-weight: 750 !important; }
    h2 { font-size: 1.45rem !important; font-weight: 700 !important; }
    h3 { font-size: 1.08rem !important; font-weight: 650 !important; }
    p, label, .stMarkdown { color: var(--vf-text); }
    .vf-brand {
        display:flex; align-items:center; gap:12px; margin: 0 0 1.7rem 0;
    }
    .vf-logo {
        width:42px; height:42px; border-radius:13px;
        display:flex; align-items:center; justify-content:center;
        background:linear-gradient(135deg,#2563eb,#38bdf8);
        color:white; font-size:21px; box-shadow:0 8px 24px #2563eb35;
    }
    .vf-brand-name { font-size:1.12rem; font-weight:800; color:#f4f7fc; }
    .vf-brand-sub { color:var(--vf-muted); font-size:.72rem; margin-top:2px; }
    .vf-eyebrow {
        text-transform:uppercase; letter-spacing:.13em; font-size:.7rem;
        font-weight:750; color:#75aaff; margin-bottom:.4rem;
    }
    .vf-hero {
        border:1px solid #29436a; border-radius:18px; padding:25px 28px;
        background: radial-gradient(circle at 88% 12%, #1d4772 0, transparent 34%),
                    linear-gradient(115deg,#14243b,#101b2d 65%,#13243a);
        margin-bottom:22px;
    }
    .vf-hero-title { font-size:1.8rem; line-height:1.2; font-weight:800; color:#f7faff; }
    .vf-hero-copy { color:#a9bad1; margin-top:8px; font-size:.94rem; }
    .vf-live {
        display:inline-flex; align-items:center; gap:7px; border:1px solid #246c59;
        color:#69e0b8; background:#12372f; border-radius:99px; padding:6px 11px;
        font-size:.7rem; font-weight:800; letter-spacing:.07em;
    }
    .vf-dot { width:7px; height:7px; border-radius:50%; background:#35d6a2; }
    .vf-metric {
        background:linear-gradient(145deg,#15243a,#111c2f);
        border:1px solid var(--vf-border); border-radius:15px;
        padding:17px 18px; min-height:124px;
    }
    .vf-metric-label { color:#9badc5; font-size:.8rem; font-weight:600; }
    .vf-metric-value { color:#f4f7fc; font-size:2rem; font-weight:800; margin-top:8px; line-height:1.1; }
    .vf-metric-foot { color:#8295af; font-size:.72rem; margin-top:7px; }
    .vf-section {
        display:flex; align-items:center; justify-content:space-between;
        margin: 1.4rem 0 .7rem 0;
    }
    .vf-section-title { color:#edf3fc; font-size:1.12rem; font-weight:750; }
    .vf-section-note { color:var(--vf-muted); font-size:.78rem; }
    .vf-panel {
        background:var(--vf-panel); border:1px solid var(--vf-border);
        border-radius:15px; padding:17px 18px;
    }
    .vf-status {
        display:inline-block; border-radius:99px; padding:4px 9px;
        font-size:.72rem; font-weight:750; letter-spacing:.02em;
    }
    .vf-approved { background:#123d35; color:#5ce0b6; }
    .vf-pending { background:#493719; color:#ffd078; }
    .vf-rejected { background:#4a202b; color:#ff8994; }
    div.stButton > button, div.stFormSubmitButton > button {
        border-radius:9px; border:1px solid #34547d; font-weight:650;
        min-height:2.55rem; transition:all .15s ease;
    }
    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"] {
        background:linear-gradient(110deg,#2563eb,#287fd8);
        border:0; color:white;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        border-color:#65a4ff; color:white; transform:translateY(-1px);
    }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background:#111d30; border-color:#30425e; color:#edf3fc; border-radius:8px;
    }
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        border:1px solid var(--vf-border); border-radius:10px; overflow:hidden;
    }
    [data-testid="stTabs"] button { color:#9fb0c7; font-weight:650; }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color:#78adff; border-bottom-color:#438cf4;
    }
    [data-testid="stAlert"] { border-radius:10px; }
    .vf-footer {
        border-top:1px solid var(--vf-border); margin-top:2.5rem;
        padding-top:14px; color:#71839d; font-size:.72rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def status_pill(value):
    styles = {
        "APPROVED": "vf-approved",
        "PENDING": "vf-pending",
        "REJECTED": "vf-rejected",
    }
    css = styles.get(str(value).upper(), "vf-pending")
    return f'<span class="vf-status {css}">{value}</span>'


def section_heading(title, note=""):
    st.markdown(
        f'<div class="vf-section"><div class="vf-section-title">{title}</div>'
        f'<div class="vf-section-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def metric_card(label, value, foot, icon):
    st.markdown(
        f"""
        <div class="vf-metric">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div class="vf-metric-label">{label}</div>
            <div style="font-size:1.15rem">{icon}</div>
          </div>
          <div class="vf-metric-value">{value}</div>
          <div class="vf-metric-foot">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    st.markdown(
        '<div class="vf-brand"><div class="vf-logo">🛡</div><div>'
        '<div class="vf-brand-name">VENDORFLOW AI</div>'
        '<div class="vf-brand-sub">Secure vendor correction portal</div></div></div>',
        unsafe_allow_html=True,
    )
    st.title("Update vendor information")
    st.caption("Secure self-service correction · Demo environment")
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
        st.markdown("### Business information")
        legal_name = st.text_input("Legal business name", payload.get("vendor", {}).get("legal_name", ""))
        email = st.text_input("Business email", payload.get("vendor", {}).get("business_email", ""))
        address = st.text_input("Business address", payload.get("vendor", {}).get("business_address", ""))
        st.markdown("### Tax information")
        tax_name = st.text_input("Tax registered name", payload.get("tax", {}).get("tax_registered_name", ""))
        tax_id = st.text_input("Tax ID", payload.get("tax", {}).get("tax_id", ""))
        st.markdown("### Bank information")
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
            ("bank", "bank_country", bank_country), ("bank", "account_number", account_number),
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
                st.write("Updated decision:", status_pill(outcome["case"]["assessment"]["decision"]), unsafe_allow_html=True)
                st.write("New version:", outcome["case"]["case"]["current_version"])
                st.markdown("### Changes recorded")
                st.dataframe(pd.DataFrame(outcome["diff"]), use_container_width=True, hide_index=True)
                st.caption("Your previous submission remains in the audit history.")
            except (ValueError, KeyError) as exc:
                st.error(str(exc))
    st.stop()


# Magic-link route is checked before the operator navigation.
query = st.query_params
if query.get("case_id") and query.get("token"):
    render_magic_link_page(str(query.get("case_id")), str(query.get("token")))

# ----------------------------- Sidebar -----------------------------
st.sidebar.markdown(
    """
    <div class="vf-brand">
      <div class="vf-logo">🛡</div>
      <div><div class="vf-brand-name">VENDORFLOW AI</div>
      <div class="vf-brand-sub">Vendor operations workspace</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)
page = st.sidebar.radio(
    "WORKSPACE",
    ["Dashboard", "New submission", "Case details", "About"],
    format_func=lambda x: {
        "Dashboard": "▦   Dashboard",
        "New submission": "＋   New submission",
        "Case details": "◈   Case details",
        "About": "ⓘ   About",
    }[x],
)
st.sidebar.markdown("---")
st.sidebar.markdown("**WORKFLOW STATUS**")
st.sidebar.markdown("🟢 Decision engine ready")
st.sidebar.markdown("🔒 Audit trail enabled")
st.sidebar.markdown("✉️ Email drafts only")
st.sidebar.markdown("---")
st.sidebar.caption("Prototype environment · Synthetic data only")
st.sidebar.caption("No real email or external tax/bank verification")

# ----------------------------- Page header -----------------------------
st.markdown(
    '<div class="vf-eyebrow">VENDOR OPERATIONS / WORKSPACE</div>',
    unsafe_allow_html=True,
)
st.title("VendorFlow AI")
st.caption("AI-assisted onboarding · Deterministic decisions · Traceable case management")

# ----------------------------- Dashboard -----------------------------
if page == "Dashboard":
    cases = manager.list_cases()
    st.markdown(
        """
        <div class="vf-hero">
          <div style="display:flex;justify-content:space-between;gap:20px;align-items:flex-start;flex-wrap:wrap">
            <div>
              <div class="vf-eyebrow">OPERATIONS OVERVIEW</div>
              <div class="vf-hero-title">Onboarding command centre</div>
              <div class="vf-hero-copy">A clear view of vendor submissions, decision outcomes and cases that need attention.</div>
            </div>
            <div class="vf-live"><span class="vf-dot"></span> ENGINE READY</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            metric_card("TOTAL SUBMISSIONS", total, "Cases in the register", "📁")
        with m2:
            metric_card("APPROVED", approved, f"{(approved / total * 100):.1f}% of submissions", "✓")
        with m3:
            metric_card("PENDING REVIEW", pending, "Require action or human review", "◷")
        with m4:
            metric_card("REJECTED", rejected, "Confirmed disqualifying evidence", "!")

        section_heading("Decision distribution", "Live case register")
        chart_col, summary_col = st.columns([1.55, 1])
        with chart_col:
            chart_data = pd.DataFrame(
                {"Cases": [approved, pending, rejected]},
                index=["Approved", "Pending", "Rejected"],
            )
            st.bar_chart(chart_data, use_container_width=True, height=260)
        with summary_col:
            st.markdown('<div class="vf-panel">', unsafe_allow_html=True)
            st.markdown("#### Pipeline summary")
            for label, count, color in [
                ("Approved", approved, "#35c99a"),
                ("Pending", pending, "#f5b942"),
                ("Rejected", rejected, "#ff6b78"),
            ]:
                pct = (count / total * 100) if total else 0
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;margin:15px 0 5px">'
                    f'<span style="color:#b7c5d8">{label}</span>'
                    f'<b style="color:#f4f7fc">{count} <small style="color:#8295af">({pct:.0f}%)</small></b></div>'
                    f'<div style="height:7px;background:#26364f;border-radius:10px;overflow:hidden">'
                    f'<div style="height:7px;width:{pct:.1f}%;background:{color};border-radius:10px"></div></div>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        section_heading("Recent vendor cases", "Latest records from the case manager")
        view = df.rename(columns={
            "case_id": "Case ID", "vendor_id": "Vendor ID",
            "business_decision": "Decision", "lifecycle_status": "Lifecycle",
            "current_version": "Version", "updated_at": "Last updated",
        })
        preferred = [c for c in ["Case ID", "Vendor ID", "Decision", "Lifecycle", "Version", "Last updated"] if c in view.columns]
        st.dataframe(view[preferred], use_container_width=True, hide_index=True)
        left, right = st.columns([1, 1])
        with left:
            st.download_button(
                "↓  Export case register (CSV)",
                df.to_csv(index=False).encode("utf-8"),
                file_name="vendorflow_case_register.csv",
                mime="text/csv",
            )
        with right:
            if st.button("↻  Load missing synthetic cases"):
                created, skipped = seed_demo_cases()
                st.success(f"Loaded {created} new cases; {skipped} already existed.")
                st.rerun()

# ----------------------------- New submission -----------------------------
elif page == "New submission":
    st.markdown(
        '<div class="vf-hero"><div class="vf-eyebrow">INTAKE WORKFLOW</div>'
        '<div class="vf-hero-title">Register a new vendor</div>'
        '<div class="vf-hero-copy">Capture business, tax and banking details. The deterministic Python engine evaluates the submission.</div></div>',
        unsafe_allow_html=True,
    )
    with st.form("new_vendor_form"):
        st.markdown("### 01 · Business information")
        left, right = st.columns(2)
        with left:
            case_id = st.text_input("Case ID", placeholder="CASE-DEMO-1001")
            vendor_id = st.text_input("Vendor ID", placeholder="VND-DEMO-1001")
            legal_name = st.text_input("Legal business name")
            country = st.selectbox("Business country", ["IN", "US", "GB", "AE", "SG"])
        with right:
            business_type = st.selectbox("Business type", ["PRIVATE_LIMITED", "LLP", "SOLE_PROPRIETORSHIP", "PARTNERSHIP"])
            email = st.text_input("Business email")
            address = st.text_input("Business address")
        st.markdown("### 02 · Tax information")
        tax_left, tax_right = st.columns(2)
        with tax_left:
            tax_type = st.selectbox("Tax ID type", ["GSTIN", "PAN", "EIN", "UK_VAT"])
            tax_id = st.text_input("Tax ID")
        with tax_right:
            tax_name = st.text_input("Tax registered name")
        st.markdown("### 03 · Banking information")
        bank_left, bank_right = st.columns(2)
        with bank_left:
            bank_country = st.selectbox("Bank country", ["IN", "US", "GB", "AE", "SG"])
            holder = st.text_input("Bank account holder name")
        with bank_right:
            account_number = st.text_input("Bank account number")
            ifsc = st.text_input("IFSC (India only; optional)")
        create = st.form_submit_button("Evaluate and create case", type="primary", use_container_width=True)

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
                             "synthetic_fixture": False},
            }
            try:
                created = manager.create_case(payload, actor="streamlit_user")
                result = created["assessment"]
                st.success(f"Case created: {case_id}")
                a, b, c = st.columns(3)
                a.metric("Decision", result["decision"])
                b.metric("Lifecycle", result["lifecycle_status"])
                c.metric("Risk score", result["risk_score"])
                st.write(result["summary"])
                if result.get("pending_reasons"):
                    st.markdown("### Items requiring attention")
                    for reason in result["pending_reasons"]:
                        st.warning(reason)
                with st.expander("View detailed validation output"):
                    st.json(result["validations"])
            except ValueError as exc:
                st.error(str(exc))

# ----------------------------- Case details -----------------------------
elif page == "Case details":
    st.markdown(
        '<div class="vf-hero"><div class="vf-eyebrow">CASE MANAGEMENT</div>'
        '<div class="vf-hero-title">Vendor case workspace</div>'
        '<div class="vf-hero-copy">Inspect decisions, review risk signals, request corrections and trace every event.</div></div>',
        unsafe_allow_html=True,
    )
    cases = manager.list_cases()
    if not cases:
        st.info("No cases available. Load demo cases from the Dashboard.")
    else:
        options = [x["case_id"] for x in cases]
        selected = st.selectbox("Select a case", options)
        data = manager.get_case(selected)
        case, result = data["case"], data["assessment"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Decision", case["business_decision"])
        c2.metric("Lifecycle", case["lifecycle_status"])
        c3.metric("Version", case["current_version"])
        c4.metric("Risk score", result["risk_score"])
        st.markdown("### Decision summary")
        st.write(result["summary"])
        t1, t2, t3, t4 = st.tabs(["Risk & validations", "Submission", "Corrections", "Audit timeline"])
        with t1:
            if result["risk_flags"]:
                st.markdown("#### Risk signals requiring attention")
                st.dataframe(pd.DataFrame(result["risk_flags"]), use_container_width=True, hide_index=True)
            else:
                st.success("No risk flags in the latest assessment.")
            st.markdown("#### Validation results")
            st.dataframe(pd.DataFrame(result["validations"]), use_container_width=True, hide_index=True)
        with t2:
            st.json(data["submission"])
        with t3:
            if case["lifecycle_status"] == "OPEN":
                st.markdown("#### Vendor follow-up")
                st.caption("Generate an email draft first, then create a one-time secure correction link.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✉  Generate correction email draft"):
                        draft = manager.create_correction_email(selected)
                        st.session_state["latest_draft"] = draft
                with col2:
                    if st.button("🔗  Generate one-time magic link"):
                        base_url = setting("VENDORFLOW_BASE_URL", "http://localhost:8501")
                        st.session_state["latest_link"] = manager.create_magic_link(selected, base_url=base_url)
                if st.session_state.get("latest_draft"):
                    draft = st.session_state["latest_draft"]
                    st.markdown("**Email draft (not sent)**")
                    st.text_input("Recipient", draft["recipient"])
                    st.text_input("Subject", draft["subject"])
                    st.text_area("Email body", draft["body"], height=220)
                if st.session_state.get("latest_link"):
                    st.markdown("**Secure correction link**")
                    st.code(st.session_state["latest_link"])
                    st.caption("Share this one-time link with the intended vendor contact. It expires and can only be used once.")
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
                st.dataframe(
                    audit[["audit_id", "event_type", "actor", "details_json", "created_at"]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No audit events found.")

# ----------------------------- About -----------------------------
else:
    st.markdown(
        '<div class="vf-hero"><div class="vf-eyebrow">PRODUCT OVERVIEW</div>'
        '<div class="vf-hero-title">Trustworthy vendor onboarding</div>'
        '<div class="vf-hero-copy">A transparent workflow that turns submissions into explainable decisions and traceable follow-ups.</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("### The problem")
    st.write("Vendor onboarding is slowed by incomplete submissions, mismatched records and repeated manual follow-ups.")
    st.markdown("### The solution")
    st.write("VendorFlow AI validates submitted information, applies deterministic rules, keeps correctable cases open, and records every submission version and decision.")
    st.markdown("### System architecture")
    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="vf-panel"><h3>⚙️ Decision engine</h3><p style="color:#9badc5">Python validation, risk scoring and deterministic decision policy.</p></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="vf-panel"><h3>🗄️ Case management</h3><p style="color:#9badc5">SQLite submissions, assessments, email drafts, magic-link hashes and audit trail.</p></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="vf-panel"><h3>🖥️ Operator workspace</h3><p style="color:#9badc5">Streamlit dashboard, intake form, correction portal and case review.</p></div>', unsafe_allow_html=True)
    st.markdown("### Important boundaries")
    st.warning(
        "This is a prototype policy, not legal or compliance approval. Tax and bank checks are format-level checks, "
        "not external verification. Email drafts are not sent. Demo magic links require HTTPS, authentication, "
        "rate limits and access controls in production. All bundled demo records are fictional."
    )

st.markdown(
    '<div class="vf-footer">VENDORFLOW AI · DEMO ENVIRONMENT · SYNTHETIC DATA ONLY · '
    'Deterministic decisions with explainable validation and an auditable case history</div>',
    unsafe_allow_html=True,
)
