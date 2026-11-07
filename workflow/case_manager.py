"""Open-case lifecycle, resubmission, re-evaluation and audit trail."""
import copy, json, secrets, hashlib
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone
from pathlib import Path

from engine import evaluate_submission
from .database import Database
from .email_generator import build_correction_email

def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _flatten(value, prefix=""):
    out = {}
    if isinstance(value, dict):
        for k, v in value.items():
            out.update(_flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(value, list):
        out[prefix] = value
    else:
        out[prefix] = value
    return out

def payload_diff(old, new):
    a, b = _flatten(old), _flatten(new)
    return [{"field": k, "before": a.get(k), "after": b.get(k)}
            for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k) and k != "submission_version"]

class CaseManager:
    def __init__(self, db_path="vendorflow.db"):
        self.db = Database(db_path)

    def _audit(self, con, case_id, event, actor, details):
        con.execute("INSERT INTO audit_logs(case_id,event_type,actor,details_json,created_at) VALUES(?,?,?,?,?)",
                    (case_id, event, actor, json.dumps(details, ensure_ascii=False), utcnow()))

    def create_case(self, payload, actor="system"):
        payload = copy.deepcopy(payload)
        case_id, vendor_id = payload["case_id"], payload["vendor_id"]
        now = utcnow()
        result = evaluate_submission(payload).to_dict()
        with self.db.connect() as con:
            if con.execute("SELECT 1 FROM cases WHERE case_id=?", (case_id,)).fetchone():
                raise ValueError(f"Case already exists: {case_id}")
            con.execute("INSERT INTO cases VALUES(?,?,?,?,?,?,?)",
                        (case_id, vendor_id, result["decision"], result["lifecycle_status"], 1, now, now))
            con.execute("INSERT INTO submissions(case_id,version,payload_json,created_at) VALUES(?,?,?,?)",
                        (case_id, 1, json.dumps(payload), now))
            con.execute("INSERT INTO assessments(case_id,version,result_json,created_at) VALUES(?,?,?,?)",
                        (case_id, 1, json.dumps(result), now))
            self._audit(con, case_id, "CASE_CREATED", actor, {"version": 1})
            self._audit(con, case_id, "ASSESSMENT_COMPLETED", "decision_engine",
                        {"decision": result["decision"], "risk_score": result["risk_score"]})
        return self.get_case(case_id)

    def get_case(self, case_id):
        with self.db.connect() as con:
            case = con.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
            if not case: return None
            submission = con.execute("SELECT * FROM submissions WHERE case_id=? ORDER BY version DESC LIMIT 1", (case_id,)).fetchone()
            assessment = con.execute("SELECT * FROM assessments WHERE case_id=? ORDER BY version DESC LIMIT 1", (case_id,)).fetchone()
            audits = con.execute("SELECT * FROM audit_logs WHERE case_id=? ORDER BY audit_id", (case_id,)).fetchall()
            drafts = con.execute("SELECT * FROM email_drafts WHERE case_id=? ORDER BY draft_id DESC", (case_id,)).fetchall()
        return {"case": dict(case), "submission": json.loads(submission["payload_json"]),
                "assessment": json.loads(assessment["result_json"]),
                "audit_log": [dict(x) for x in audits], "email_drafts": [dict(x) for x in drafts]}

    def list_cases(self):
        with self.db.connect() as con:
            rows = con.execute("SELECT case_id,vendor_id,business_decision,lifecycle_status,current_version,updated_at FROM cases ORDER BY updated_at DESC").fetchall()
        return [dict(x) for x in rows]

    def create_correction_email(self, case_id):
        data = self.get_case(case_id)
        if not data: raise KeyError(case_id)
        if data["case"]["lifecycle_status"] != "OPEN":
            raise ValueError("Only open cases can receive correction requests.")
        result, payload = data["assessment"], data["submission"]
        draft = build_correction_email(payload, result)
        now = utcnow()
        with self.db.connect() as con:
            con.execute("INSERT INTO email_drafts(case_id,version,recipient,subject,body,created_at) VALUES(?,?,?,?,?,?)",
                        (case_id, data["case"]["current_version"], draft["recipient"], draft["subject"], draft["body"], now))
            self._audit(con, case_id, "CORRECTION_EMAIL_DRAFTED", "system", {"subject": draft["subject"]})
        return draft

    def create_magic_link(self, case_id, ttl_hours=48, base_url="http://localhost:8501"):
        data = self.get_case(case_id)
        if not data: raise KeyError(case_id)
        if data["case"]["lifecycle_status"] != "OPEN":
            raise ValueError("Magic links are available only for open cases.")
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        expiry = (now + timedelta(hours=ttl_hours)).isoformat(timespec="seconds")
        with self.db.connect() as con:
            con.execute("INSERT INTO magic_links(case_id,token_hash,expires_at,created_at) VALUES(?,?,?,?)",
                        (case_id, token_hash, expiry, now.isoformat(timespec="seconds")))
            self._audit(con, case_id, "MAGIC_LINK_CREATED", "system", {"expires_at": expiry, "ttl_hours": ttl_hours})
        # Configure VENDORFLOW_BASE_URL to the deployed HTTPS Streamlit URL.
        # The token is returned once; only its hash is stored in SQLite.
        query = urlencode({"case_id": case_id, "token": token})
        return f"{base_url.rstrip('/')}/?{query}"

    def resubmit(self, case_id, token, updates, actor="vendor"):
        """Apply targeted updates to the latest payload. Previous versions remain immutable."""
        now = datetime.now(timezone.utc)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with self.db.connect() as con:
            case = con.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
            if not case: raise KeyError(case_id)
            if case["lifecycle_status"] != "OPEN": raise ValueError("This case is closed.")
            link = con.execute("SELECT * FROM magic_links WHERE case_id=? AND token_hash=?",
                               (case_id, token_hash)).fetchone()
            if not link: raise ValueError("Invalid magic link.")
            if link["used_at"]: raise ValueError("This magic link has already been used.")
            if datetime.fromisoformat(link["expires_at"]) < now: raise ValueError("Magic link has expired.")
            previous = con.execute("SELECT payload_json FROM submissions WHERE case_id=? ORDER BY version DESC LIMIT 1",
                                   (case_id,)).fetchone()
            old_payload = json.loads(previous["payload_json"])
            new_payload = copy.deepcopy(old_payload)
            self._deep_update(new_payload, updates)
            version = case["current_version"] + 1
            new_payload["submission_version"] = version
            result = evaluate_submission(new_payload).to_dict()
            diff = payload_diff(old_payload, new_payload)
            stamp = now.isoformat(timespec="seconds")
            con.execute("UPDATE magic_links SET used_at=? WHERE link_id=?", (stamp, link["link_id"]))
            con.execute("INSERT INTO submissions(case_id,version,payload_json,created_at) VALUES(?,?,?,?)",
                        (case_id, version, json.dumps(new_payload), stamp))
            con.execute("INSERT INTO assessments(case_id,version,result_json,created_at) VALUES(?,?,?,?)",
                        (case_id, version, json.dumps(result), stamp))
            con.execute("UPDATE cases SET business_decision=?,lifecycle_status=?,current_version=?,updated_at=? WHERE case_id=?",
                        (result["decision"], result["lifecycle_status"], version, stamp, case_id))
            self._audit(con, case_id, "VENDOR_RESUBMITTED", actor, {"version": version, "changed_fields": diff})
            self._audit(con, case_id, "ASSESSMENT_COMPLETED", "decision_engine",
                        {"version": version, "decision": result["decision"], "risk_score": result["risk_score"]})
        return {"case": self.get_case(case_id), "diff": diff}

    @staticmethod
    def _deep_update(target, updates):
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                CaseManager._deep_update(target[key], value)
            else:
                target[key] = value
