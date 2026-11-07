# VendorFlow AI — Stage 6 Streamlit UI

## Run locally (Windows PowerShell)
Open the terminal in the project root (the folder containing `app.py`, `engine`, `workflow`, `tests`):
```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Streamlit prints a local URL, normally `http://localhost:8501`.

## Pages
- Dashboard: KPI cards, decision distribution, recent cases, CSV export, load synthetic fixtures.
- New submission: enter vendor, tax and bank details, then run the deterministic engine.
- Case details: inspect risk flags, validation results, latest submission, correction email draft, magic link, and audit timeline.
- Magic-link correction: opening a generated localhost URL displays the vendor correction form. On submit, a new immutable submission version is created, a field-level diff is shown, and the engine runs again.

## First use
Open Dashboard and click **Load 30 synthetic demo cases**. The action is idempotent: existing case IDs are skipped. Then explore the Case details page.

## Notes
- The app stores its SQLite database at `vendorflow.db` in the project root.
- Demo email is not sent.
- The magic link is for local demonstration only. Production use requires HTTPS, real authentication/session controls, expiry policy, rate limiting, CSRF protection and email delivery integration.
- Do not use real personal, tax, bank or confidential vendor data in this prototype.
