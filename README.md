# VendorFlow AI — Stage 3 dataset

## Generate
```bash
python generate_dataset.py
```

No third-party packages are required for this stage.

## Outputs
- `vendor_submissions.jsonl`: nested submissions, one JSON object per line.
- `vendor_submissions.csv`: flattened analysis-friendly dataset.
- `ground_truth.json`: expected decisions, scenario labels and flags.
- `dataset_summary.json`: dataset counts and provenance warning.
- `documents/`: fictional text-based sample evidence.

All records are synthetic. Tax identifiers are test fixtures and must not be represented as government-verified.


See `README_STAGE5.md` for the Stage 5 open-case workflow.


See `README_STAGE6.md` for running the Streamlit UI.


See `README_STAGE7.md` for benchmark evaluation and metrics.


See `README_STAGE8.md` for GitHub and Streamlit deployment preparation.
