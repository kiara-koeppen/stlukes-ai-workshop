"""
CKD Clinician Review
--------------------
Single-page review UI for St. Luke's chronic-kidney-disease (CKD) care-gap program.

A clinician / quality reviewer uses this to:
  1. See headline KPI tiles (CKD population, care gaps, high risk, undocumented rate).
  2. Work a filterable, risk-sorted worklist of care-gap patients
     (lab-evidence CKD that is not documented in Epic).
  3. Inspect the AI note-signal for a selected patient (what the note extractor found).
  4. LIVE AI DRAFTING: generate a clinician-ready CKD problem-list entry + nephrology
     referral on demand via ai_query() (real genAI, ~2-5s), ready to paste into Epic.
  5. HUMAN-IN-THE-LOOP WRITEBACK: record the clinician's decision (Accept / Defer /
     Refer) into kk_test.clinical.ckd_review_actions and show the loop closing.
  6. Ask the CKD Genie Agent a free-text question and see the answer + generated SQL.

Runs as the app service principal. Data is read/written through the app's SQL
warehouse resource. No secrets or tokens are hardcoded.
"""

import os
import time

import pandas as pd
import requests
import streamlit as st
from databricks import sql as dbsql
from databricks.sdk.core import Config

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CATALOG = os.getenv("DATABRICKS_CATALOG", "kk_test")
SCHEMA = "clinical"
METRICS_VIEW = f"{CATALOG}.{SCHEMA}.ckd_metrics"
REGISTRY = f"{CATALOG}.{SCHEMA}.ckd_patient_registry"
SIGNALS = f"{CATALOG}.{SCHEMA}.notes_ckd_signals"
NOTES = f"{CATALOG}.{SCHEMA}.clinical_notes"
REVIEW_ACTIONS = f"{CATALOG}.{SCHEMA}.ckd_review_actions"

WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")
GENIE_SPACE_ID = os.getenv("CKD_GENIE_SPACE_ID", "").strip()
LLM_ENDPOINT = os.getenv("CKD_LLM_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct")

# Stage severity ordering used to rank the worklist by clinical risk.
STAGE_RANK = {"CKD 5": 5, "CKD 4": 4, "CKD 3b": 3, "CKD 3a": 2, "CKD 2": 1, "None": 0}

st.set_page_config(page_title="CKD Clinician Review", page_icon="🫘", layout="wide")

_cfg = Config()  # picks up service-principal creds injected by Databricks Apps


def current_user() -> str:
    """The logged-in app user, from Databricks Apps forwarded headers."""
    try:
        h = st.context.headers or {}
        for k in ("X-Forwarded-Email", "X-Forwarded-Preferred-Username", "X-Forwarded-User"):
            if h.get(k):
                return h[k]
    except Exception:  # noqa: BLE001
        pass
    return "app-user"


def sql_str(value: str) -> str:
    """Single-quote-escape a Python string for safe inline SQL."""
    return (value or "").replace("'", "''")


# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------
@st.cache_resource
def get_connection():
    """One cached SQL-warehouse connection for the app (service principal auth)."""
    return dbsql.connect(
        server_hostname=_cfg.host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: _cfg.authenticate,
    )


def exec_df(query: str) -> pd.DataFrame:
    """Run a query and return a DataFrame (not cached — for live / write-adjacent reads)."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(query)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)


def exec_dml(query: str) -> None:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(query)


@st.cache_data(ttl=300)
def run_query(query: str) -> pd.DataFrame:
    return exec_df(query)


@st.cache_data(ttl=300)
def load_kpis() -> dict:
    df = run_query(
        f"""
        SELECT
            MEASURE(`Patients With CKD`)   AS ckd_patients,
            MEASURE(`Care Gap Patients`)   AS care_gap,
            MEASURE(`High Risk Patients`)  AS high_risk,
            MEASURE(`Undocumented CKD Rate`) AS undoc_rate
        FROM {METRICS_VIEW}
        """
    )
    r = df.iloc[0]
    return {
        "ckd_patients": int(r["ckd_patients"]),
        "care_gap": int(r["care_gap"]),
        "high_risk": int(r["high_risk"]),
        "undoc_rate": float(r["undoc_rate"]),
    }


@st.cache_data(ttl=300)
def load_worklist() -> pd.DataFrame:
    """Care-gap patients: lab-evidence CKD stage 3a-5 not documented in Epic.

    Matches the `Care Gap` definition in the ckd_metrics metric view exactly.
    """
    df = run_query(
        f"""
        SELECT
            patient_id,
            actual_ckd_stage,
            documented_ckd,
            sees_nephrology,
            assigned_provider_name,
            age,
            ROUND((gfr_1 + gfr_2 + gfr_3) / 3.0, 1) AS avg_gfr,
            microalbumin_category
        FROM {REGISTRY}
        WHERE actual_ckd_stage IN ('CKD 3a','CKD 3b','CKD 4','CKD 5')
          AND documented_ckd IN ('No','None')
        """
    )
    df["stage_rank"] = df["actual_ckd_stage"].map(STAGE_RANK).fillna(0).astype(int)
    df["avg_gfr"] = pd.to_numeric(df["avg_gfr"], errors="coerce")
    # Risk sort: most severe stage first, then those NOT in nephrology, then lowest GFR.
    df = df.sort_values(
        by=["stage_rank", "sees_nephrology", "avg_gfr"],
        ascending=[False, True, True],
    ).reset_index(drop=True)
    return df


@st.cache_data(ttl=300)
def load_signal(patient_id: str) -> pd.DataFrame:
    return run_query(
        f"""
        SELECT
            s.patient_id, s.note_id, s.note_date,
            s.ai_indicates_ckd, s.ai_suggested_stage, s.ai_mentions_nephrology,
            s.ai_flag_undocumented,
            n.author, n.note_type, n.note_text
        FROM {SIGNALS} s
        LEFT JOIN {NOTES} n ON s.note_id = n.note_id
        WHERE s.patient_id = '{sql_str(patient_id)}'
        ORDER BY s.note_date DESC
        """
    )


def draft_referral(patient_id: str) -> str:
    """LIVE ai_query() call: draft a KDIGO problem-list entry + nephrology referral.

    Passes the patient's real labs (3x creatinine, 3x eGFR, microalbumin, stage,
    nephrology status) plus the most recent clinical note straight into the model.
    """
    pid = sql_str(patient_id)
    prompt = (
        "'You are a nephrology clinical assistant helping a St. Lukes primary care clinician. "
        "Based only on the data below, produce two clearly labeled sections.\\n\\n"
        "SECTION 1 - SUGGESTED PROBLEM-LIST ENTRY: one line with the KDIGO CKD stage and a "
        "two-sentence rationale citing the eGFR trend and albuminuria.\\n"
        "SECTION 2 - NEPHROLOGY REFERRAL: a short 3-4 sentence referral paragraph addressed to "
        "nephrology. Do not invent data.\\n\\nPATIENT DATA\\nLab-derived CKD stage: '"
    )
    query = f"""
        WITH p AS (
            SELECT r.patient_id, r.actual_ckd_stage, r.sees_nephrology,
                   r.creatinine_1, r.creatinine_2, r.creatinine_3,
                   r.gfr_1, r.gfr_2, r.gfr_3,
                   r.microalbumin_value, r.microalbumin_category,
                   (SELECT n.note_text FROM {NOTES} n
                    WHERE n.patient_id = r.patient_id
                    ORDER BY n.note_date DESC LIMIT 1) AS note_text
            FROM {REGISTRY} r
            WHERE r.patient_id = '{pid}'
        )
        SELECT ai_query('{LLM_ENDPOINT}', CONCAT(
            {prompt},
            COALESCE(actual_ckd_stage,'unknown'),
            '\\neGFR (3 readings): ', COALESCE(CAST(gfr_1 AS STRING),'NA'), ', ',
            COALESCE(CAST(gfr_2 AS STRING),'NA'), ', ', COALESCE(CAST(gfr_3 AS STRING),'NA'),
            ' mL/min/1.73m2\\nCreatinine (3 readings): ',
            COALESCE(CAST(creatinine_1 AS STRING),'NA'), ', ',
            COALESCE(CAST(creatinine_2 AS STRING),'NA'), ', ',
            COALESCE(CAST(creatinine_3 AS STRING),'NA'),
            ' mg/dL\\nMicroalbumin: ', COALESCE(CAST(microalbumin_value AS STRING),'NA'),
            ' (', COALESCE(microalbumin_category,'NA'), ')\\nCurrently seeing nephrology: ',
            CASE WHEN sees_nephrology THEN 'yes' ELSE 'no' END,
            '\\n\\nMost recent clinical note:\\n', COALESCE(note_text,'(no note on file)')
        )) AS draft
        FROM p
    """
    df = exec_df(query)
    if df.empty or df.iloc[0]["draft"] is None:
        return "_(No draft returned — patient may have no labs on file.)_"
    return str(df.iloc[0]["draft"])


def record_review(patient_id, reviewed_by, action, accepted_stage, note) -> None:
    exec_dml(
        f"""
        INSERT INTO {REVIEW_ACTIONS}
            (patient_id, reviewed_by, action, accepted_stage, note, reviewed_at)
        VALUES (
            '{sql_str(patient_id)}', '{sql_str(reviewed_by)}', '{sql_str(action)}',
            '{sql_str(accepted_stage)}', '{sql_str(note)}', current_timestamp()
        )
        """
    )


def load_recent_reviews(limit: int = 8) -> pd.DataFrame:
    return exec_df(
        f"""
        SELECT patient_id, action, accepted_stage, reviewed_by, reviewed_at, note
        FROM {REVIEW_ACTIONS}
        ORDER BY reviewed_at DESC
        LIMIT {limit}
        """
    )


# ---------------------------------------------------------------------------
# Genie Conversation API
# ---------------------------------------------------------------------------
def ask_genie(space_id: str, question: str, timeout_s: int = 120) -> dict:
    headers = _cfg.authenticate()  # {'Authorization': 'Bearer ...'}
    headers["Content-Type"] = "application/json"
    base = f"{_cfg.host}/api/2.0/genie/spaces/{space_id}"

    r = requests.post(f"{base}/start-conversation", headers=headers,
                      json={"content": question}, timeout=30)
    r.raise_for_status()
    j = r.json()
    cid = j.get("conversation_id") or j["conversation"]["id"]
    mid = j.get("message_id") or j["message"]["id"]

    m, status = {}, None
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        m = requests.get(f"{base}/conversations/{cid}/messages/{mid}",
                         headers=headers, timeout=30).json()
        status = m.get("status")
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        time.sleep(3)

    out = {"status": status, "text": None, "sql": None, "rows": None, "columns": None}
    for a in m.get("attachments", []) or []:
        if a.get("text", {}).get("content") and not out["text"]:
            out["text"] = a["text"]["content"]
        if a.get("query") and not out["sql"]:
            out["sql"] = a["query"].get("query", "").strip()
            aid = a.get("attachment_id")
            try:
                qr = requests.get(
                    f"{base}/conversations/{cid}/messages/{mid}/attachments/{aid}/query-result",
                    headers=headers, timeout=60).json()
                sr = qr.get("statement_response", {})
                out["rows"] = sr.get("result", {}).get("data_array", [])
                out["columns"] = [c["name"] for c in
                                  sr.get("manifest", {}).get("schema", {}).get("columns", [])]
            except Exception as e:  # noqa: BLE001
                out["text"] = (out["text"] or "") + f"\n\n_(result fetch error: {e})_"
    return out


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("🫘 CKD Clinician Review")
st.caption(
    "Chronic kidney disease care-gap worklist for St. Luke's. "
    "Lab evidence of CKD (eGFR / creatinine) reconciled against what is documented in Epic."
)

if not WAREHOUSE_ID:
    st.error("No SQL warehouse configured. Add a **sql-warehouse** resource to this app.")
    st.stop()

try:
    kpis = load_kpis()
except Exception as e:  # noqa: BLE001
    st.error(f"Could not load metrics from `{METRICS_VIEW}`.\n\n```\n{e}\n```")
    st.info(
        "If this is a permissions error, the app service principal needs SELECT on the "
        "kk_test.clinical tables plus USE CATALOG / USE SCHEMA, and CAN USE on the warehouse."
    )
    st.stop()

# --- KPI tiles ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Patients with CKD", f"{kpis['ckd_patients']:,}")
c2.metric("Care-gap patients", f"{kpis['care_gap']:,}",
          help="CKD stage 3a-5 with lab evidence, not documented in Epic")
c3.metric("High risk (stage 4/5, no nephrology)", f"{kpis['high_risk']:,}")
c4.metric("Undocumented CKD rate", f"{kpis['undoc_rate'] * 100:.1f}%")

st.divider()

worklist = load_worklist()

left, right = st.columns([2, 3])

# --- Worklist + filters ---
with left:
    st.subheader("Care-gap worklist")
    providers = ["All providers"] + sorted(worklist["assigned_provider_name"].dropna().unique().tolist())
    stages = ["All stages"] + [s for s in ["CKD 5", "CKD 4", "CKD 3b", "CKD 3a"]
                               if s in worklist["actual_ckd_stage"].unique()]
    fc1, fc2 = st.columns(2)
    sel_provider = fc1.selectbox("Provider", providers)
    sel_stage = fc2.selectbox("Stage", stages)

filtered = worklist.copy()
if sel_provider != "All providers":
    filtered = filtered[filtered["assigned_provider_name"] == sel_provider]
if sel_stage != "All stages":
    filtered = filtered[filtered["actual_ckd_stage"] == sel_stage]

display_cols = {
    "patient_id": "Patient ID",
    "actual_ckd_stage": "Actual CKD stage",
    "documented_ckd": "Documented in Epic",
    "avg_gfr": "Avg eGFR",
    "sees_nephrology": "Sees nephrology",
    "assigned_provider_name": "Assigned provider",
    "microalbumin_category": "Albuminuria",
}

with left:
    st.caption(f"{len(filtered):,} of {len(worklist):,} care-gap patients (sorted by risk)")
    st.dataframe(
        filtered.rename(columns=display_cols)[list(display_cols.values())],
        use_container_width=True, hide_index=True, height=430,
    )

# --- Patient detail: AI signal + live drafting + writeback ---
with right:
    st.subheader("Patient review")
    if filtered.empty:
        st.info("No patients match the current filters.")
    else:
        patient_ids = filtered["patient_id"].tolist()
        sel_patient = st.selectbox("Select a patient from the worklist", patient_ids)
        row = filtered[filtered["patient_id"] == sel_patient].iloc[0]

        m1, m2, m3 = st.columns(3)
        m1.metric("Actual stage", row["actual_ckd_stage"])
        m2.metric("Avg eGFR", f"{row['avg_gfr']:.0f}" if pd.notna(row["avg_gfr"]) else "n/a")
        m3.metric("In nephrology", "Yes" if row["sees_nephrology"] else "No")

        sig = load_signal(sel_patient)
        suggested_stage = row["actual_ckd_stage"]
        if sig.empty:
            st.info("No AI note signal on file (not in the 200-note AI-scored sample).")
        else:
            s = sig.iloc[0]
            if s["ai_suggested_stage"]:
                suggested_stage = str(s["ai_suggested_stage"])
            st.markdown("**AI note extractor found:**")
            b1, b2, b3 = st.columns(3)
            b1.metric("AI indicates CKD", str(s["ai_indicates_ckd"]))
            b2.metric("AI suggested stage", str(s["ai_suggested_stage"]) if s["ai_suggested_stage"] else "n/a")
            b3.metric("AI mentions nephrology", str(s["ai_mentions_nephrology"]))
            if bool(s["ai_flag_undocumented"]):
                st.warning("AI flag: note describes CKD that is **undocumented** in the problem list.")
            if s["note_text"]:
                with st.expander("View clinical note"):
                    st.caption(f"{s['note_type'] or 'Note'} · {s['author'] or 'unknown'} · {s['note_date']}")
                    st.write(s["note_text"])

        # ---- Feature 1: LIVE AI DRAFTING ----
        st.markdown("#### ✍️ Draft for Epic write-back")
        st.caption("Live `ai_query()` call — generates a KDIGO problem-list entry + referral from this patient's labs and note.")
        if st.button("Draft nephrology referral + problem-list update", type="primary", key="draft_btn"):
            with st.spinner("Generating with databricks-meta-llama-3-3-70b-instruct (live)..."):
                t0 = time.time()
                try:
                    draft = draft_referral(sel_patient)
                    st.session_state[f"draft_{sel_patient}"] = draft
                    st.session_state[f"draft_secs_{sel_patient}"] = time.time() - t0
                except Exception as e:  # noqa: BLE001
                    st.session_state[f"draft_{sel_patient}"] = f"_(ai_query failed: {e})_"
                    st.session_state[f"draft_secs_{sel_patient}"] = time.time() - t0
        draft = st.session_state.get(f"draft_{sel_patient}")
        if draft:
            secs = st.session_state.get(f"draft_secs_{sel_patient}")
            if secs:
                st.caption(f"Generated live in {secs:.1f}s")
            st.markdown(draft)

        # ---- Feature 2: HUMAN-IN-THE-LOOP WRITEBACK ----
        st.markdown("#### ✅ Record clinician decision")
        with st.form(key=f"review_form_{sel_patient}", clear_on_submit=False):
            wc1, wc2 = st.columns(2)
            action = wc1.selectbox("Action", ["Accepted", "Deferred", "Referred"])
            stage_opts = ["CKD 5", "CKD 4", "CKD 3b", "CKD 3a", "CKD 2"]
            default_idx = stage_opts.index(suggested_stage) if suggested_stage in stage_opts else 0
            accepted_stage = wc2.selectbox("Accepted stage", stage_opts, index=default_idx)
            review_note = st.text_input("Note (optional)", placeholder="e.g. Referral placed in Epic")
            submitted = st.form_submit_button("Accept suggested stage / mark reviewed")
            if submitted:
                try:
                    record_review(sel_patient, current_user(), action, accepted_stage, review_note)
                    st.success(f"Recorded: {action} · {accepted_stage} for {sel_patient} (by {current_user()}).")
                except Exception as e:  # noqa: BLE001
                    st.error(f"Write-back failed (SP needs MODIFY on {REVIEW_ACTIONS}):\n\n```\n{e}\n```")

        # Recently reviewed — makes the loop visible
        st.markdown("**Recently reviewed**")
        try:
            recent = load_recent_reviews()
            if recent.empty:
                st.caption("No reviews recorded yet.")
            else:
                st.dataframe(recent, use_container_width=True, hide_index=True, height=180)
        except Exception as e:  # noqa: BLE001
            st.caption(f"Could not load recent reviews: {e}")

st.divider()

# --- Ask Genie ---
st.subheader("Ask the CKD Genie Agent")
if not GENIE_SPACE_ID:
    st.info("Genie space not configured (set `CKD_GENIE_SPACE_ID`).")
else:
    st.caption(
        "Natural-language questions answered by the CKD Genie space over the same data. "
        "Example: *How many patients have lab-evidence CKD that is not documented in Epic?*"
    )
    q = st.text_input("Question", placeholder="Ask about the CKD population, care gaps, or risk...")
    if st.button("Ask Genie", key="genie_btn") and q:
        with st.spinner("Genie is thinking..."):
            try:
                res = ask_genie(GENIE_SPACE_ID, q)
            except Exception as e:  # noqa: BLE001
                res = None
                st.error(f"Genie call failed (SP needs CAN RUN on space `{GENIE_SPACE_ID}`).\n\n```\n{e}\n```")
        if res:
            if res["status"] != "COMPLETED":
                st.warning(f"Genie returned status: {res['status']}")
            if res.get("text"):
                st.markdown(res["text"])
            if res.get("rows") is not None and res.get("columns"):
                st.dataframe(pd.DataFrame(res["rows"], columns=res["columns"]),
                             use_container_width=True, hide_index=True)
            if res.get("sql"):
                with st.expander("Generated SQL"):
                    st.code(res["sql"], language="sql")

st.divider()
st.caption(
    "St. Luke's AI Dev Collaboration Workshop · CKD use case · "
    f"data: `{CATALOG}.{SCHEMA}` · live ai_query drafting + human-in-the-loop write-back"
)
