# VendorFlow AI — Stage 8: Deployment Preparation

## Deployment target
This project is prepared for Streamlit Community Cloud. The application entry point is `app.py`.

## Local verification
From the project root (the folder containing `app.py`):
```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## GitHub repository preparation
1. Create a new GitHub repository, for example `vendorflow-ai`.
2. Keep the repository private while preparing it, if preferred.
3. Upload the **contents** of this project folder (not the outer ZIP folder).
4. Confirm `app.py`, `requirements.txt`, `engine/`, `workflow/`, `evaluation/`, `tests/`, and the synthetic data files appear at the repository root.
5. Do not upload `vendorflow.db`, real vendor data, credentials, tokens, or `.streamlit/secrets.toml`.
6. The `.gitignore` file excludes local databases, Python caches and Streamlit secrets.

## Streamlit Community Cloud
1. Sign in to Streamlit Community Cloud using GitHub.
2. Choose **Create app** and select the `vendorflow-ai` repository.
3. Select the branch and set the main file path to `app.py`.
4. Deploy and wait for the build to finish.
5. Open the generated HTTPS app URL and test the Dashboard, New submission and Case details pages.

## Public magic-link configuration
The app supports a deployment setting named `VENDORFLOW_BASE_URL`.
For local development it defaults to `http://localhost:8501`.
For a deployed app, set the Streamlit secret:
```toml
VENDORFLOW_BASE_URL = "https://YOUR-APP-NAME.streamlit.app"
```
Then use the app's **Generate one-time magic link** action. The generated URL will point to the configured public app URL instead of localhost.

The app also supports `VENDORFLOW_DB_PATH` to choose a database file path. Do not assume a local SQLite file on a hosted free service is durable across restarts/redeployments. Streamlit Community Cloud's local filesystem should be treated as ephemeral for this prototype.

## Critical prototype limitations
- The SQLite database may be reset or lost when the hosted app restarts, rebuilds or moves to another instance. For durable multi-user deployment, move persistence to a managed database such as PostgreSQL and configure access credentials through Streamlit secrets.
- Magic links are bearer credentials. Anyone holding a valid link can attempt to use it. Use HTTPS, short expiry, one-time use, rate limits, monitoring and vendor access controls for any real deployment.
- This prototype uses one SQLite database and is not designed for concurrent production traffic.
- The email workflow creates drafts only; no email is sent.
- Synthetic identifiers and documents are fictional. The engine does not verify government tax registration, bank existence or account ownership.
- Do not enter real vendor, personal, tax or bank information in a public demo.
- Before making a repository public, review every file for secrets and personal data.

## Suggested live demo sequence
1. Dashboard: load or show the 30 synthetic cases.
2. Case details: open CASE-0001 and explain the cross-country signals.
3. Corrections: show the generated email draft and one-time magic link.
4. Vendor correction: use a test case and a newly generated link; submit a targeted correction.
5. Audit timeline: show VENDOR_RESUBMITTED and the subsequent ASSESSMENT_COMPLETED event.
6. Evaluation: explain the 30-case synthetic benchmark and its limitations.

## Stage 8 checklist
- [ ] GitHub repository created and project files pushed.
- [ ] Streamlit app deployed successfully.
- [ ] Public HTTPS URL opens in an incognito browser.
- [ ] `VENDORFLOW_BASE_URL` secret set to the exact public URL.
- [ ] Public magic link points to the deployed URL and can be used once.
- [ ] No real vendor data or secrets are included.
