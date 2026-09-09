# Setup: load the data into any Databricks environment

`00_load_all_data.py` is a one-shot, parameterized loader. It creates the schemas, loads all four
use cases' Delta tables from the CSVs committed in `synthetic-data/data/`, creates the volumes,
uploads the unstructured files (CKD clinical notes, Huddle transcripts, and the Diversion policy /
HTM vendor-bulletin PDFs), and — depending on the `load_metric_views` toggle — optionally builds the
four metric views. Schema/table/column names mirror the SLHS prod paths, so moving from workshop to
prod is just the `catalog` widget.

**Two modes (the `load_metric_views` widget):**
- `yes` (default) = full facilitator/answer-key load, including the 4 metric views.
- `no` = **attendee data-only load** (raw tables + volumes only). Use this for the workshop, where
  attendees build the metric views (and everything downstream) live with Genie Code.

## Run it
1. Add this repo to your Databricks workspace as a **Git folder** (Repos), so the CSVs come with it.
2. Open `setup/00_load_all_data.py` on serverless (or any cluster with Unity Catalog).
3. Set the **`catalog`** widget to a catalog you can create schemas/volumes/tables in
   (workshop default is a placeholder `healthcare_ai`; the facilitator build used `kk_test`).
   Leave `data_dir` blank to auto-detect from the repo, or set it to `<repo>/synthetic-data/data`.
4. **Run All.** Each section prints row counts so you can confirm the load.

## What it loads
| Schema | Tables | Volumes |
|---|---|---|
| `clinical` | ckd_patient_registry, clinical_notes | landing, clinical_notes_files |
| `med_diversion` | medication_activity, employee_risk, peer_group | landing, policy_docs (PDFs) |
| `htm` | medical_assets, work_orders | landing, vendor_bulletins (PDFs) |
| `huddle` | patient_demographics, transcript_extractions, physician_inputs | landing, transcripts |

Plus, **only when `load_metric_views=yes`**, the four metric views: `clinical.ckd_metrics`,
`med_diversion.diversion_metrics`, `htm.htm_metrics`, `huddle.huddle_metrics`. (For the attendee
data-only load, set `load_metric_views=no` and attendees build these with Genie Code.)

## Not loaded here (separate, downstream)
The AI-function output tables, Genie Agents, AI/BI dashboards, and Apps are built by the scripts in
each `solutions/0X-*/` folder and described in the guides. They currently reference `kk_test`; swap in
your catalog. The generators in `synthetic-data/generators/` can regenerate the CSVs if needed.
