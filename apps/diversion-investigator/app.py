"""
Medication Diversion Investigation Workspace
--------------------------------------------
Case-management workspace for St. Luke's controlled-substance diversion program.

A compliance / pharmacy investigator uses this to:
  1. WATCHLIST: employees ranked by composite anomaly score (from the
     diversion_metrics metric view), with IRIS risk score. Highest-signal
     employees rise to the top.
  2. INVESTIGATE: pick an employee, see their five-factor anomaly breakdown
     (waste-without-witness, admin-without-order, low-pain opioid, off-shift,
     out-of-department) benchmarked against their peer-group average, plus a
     sample of their flagged medication_activity events.
  3. LIVE NARRATIVE: a "Generate investigation summary" button that calls
     ai_query() live for the selected employee (objective, peer-benchmarked,
     descriptive - never accusatory).
  4. CASE MANAGEMENT (human-in-the-loop writeback): set a case status
     (Open / Under Review / Escalated / Cleared), add reviewer notes, and SAVE.
     Saving writes a row to kk_test.med_diversion.investigation_cases and the
     current case log is shown back. This replaces the manual Excel workbook.

This is HR/legal-sensitive, SYNTHETIC-only workshop data. All wording is kept
objective and descriptive, not accusatory. The app runs as its service
principal; data is read/written through the app's SQL warehouse resource.
No secrets or tokens are hardcoded.
"""

import os
import time
import uuid

import pandas as pd
import requests
import streamlit as st
from databricks import sql as dbsql
from databricks.sdk.core import Config

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CATALOG = "kk_test"
SCHEMA = "med_diversion"
METRICS_VIEW = f"{CATALOG}.{SCHEMA}.diversion_metrics"
ACTIVITY = f"{CATALOG}.{SCHEMA}.medication_activity"
EMPLOYEE_RISK = f"{CATALOG}.{SCHEMA}.employee_risk"
PEER_GROUP = f"{CATALOG}.{SCHEMA}.peer_group"
NARRATIVES = f"{CATALOG}.{SCHEMA}.investigation_narratives"
CASES = f"{CATALOG}.{SCHEMA}.investigation_cases"

WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")
GENIE_SPACE_ID = os.getenv("DIVERSION_GENIE_SPACE_ID", "").strip()
LLM_ENDPOINT = os.getenv("DIVERSION_LLM_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct")

STATUS_OPTIONS = ["Open", "Under Review", "Escalated", "Cleared"]

# The five anomaly factors, aligned exactly with the diversion_metrics measures.
FACTORS = [
    ("waste_no_witness", "Waste without witness (CII)"),
    ("admin_no_order", "Administration without order"),
    ("low_pain_opioid", "Opioid admin, low/no pain score"),
    ("off_shift", "Off-shift activity"),
    ("out_of_dept", "Out-of-department activity"),
]

st.set_page_config(page_title="Diversion Investigation Workspace", page_icon="🔍", layout="wide")

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
    return "investigator"


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
    """Run a query and return a DataFrame (not cached - for live / write-adjacent reads)."""
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
def load_watchlist() -> pd.DataFrame:
    """All employees, ranked by composite anomaly score from the metric view.

    The five-factor breakdown columns match the diversion_metrics measures
    exactly, so on-screen numbers reconcile with the governed metric layer.
    IRIS score + peer group are joined from employee_risk.
    """
    metrics = run_query(
        f"""
        SELECT
            `Employee`                             AS employee_id,
            `Employee Name`                        AS employee_name,
            `Role`                                 AS role,
            `Department`                           AS department,
            MEASURE(`Composite Anomaly Score`)     AS composite,
            MEASURE(`Waste Without Witness CII`)   AS waste_no_witness,
            MEASURE(`Administration Without Order`) AS admin_no_order,
            MEASURE(`Opioid Low Pain Score`)       AS low_pain_opioid,
            MEASURE(`Off Shift Activity Count`)    AS off_shift,
            MEASURE(`Out Of Department Activity Count`) AS out_of_dept,
            MEASURE(`Total Events`)                AS total_events
        FROM {METRICS_VIEW}
        GROUP BY `Employee`, `Employee Name`, `Role`, `Department`
        """
    )
    risk = run_query(
        f"SELECT employee_id, iris_score, peer_group_id FROM {EMPLOYEE_RISK}"
    )
    df = metrics.merge(risk, on="employee_id", how="left")

    num_cols = ["composite", "waste_no_witness", "admin_no_order", "low_pain_opioid",
                "off_shift", "out_of_dept", "total_events", "iris_score"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.sort_values(by=["composite", "iris_score"], ascending=[False, False]).reset_index(drop=True)
    df.insert(0, "rank", df.index + 1)
    return df


def peer_averages(watchlist: pd.DataFrame, peer_group_id: str) -> dict:
    """Mean of each anomaly factor + composite across the employee's peer group."""
    if not peer_group_id:
        peers = watchlist
    else:
        peers = watchlist[watchlist["peer_group_id"] == peer_group_id]
    if peers.empty:
        peers = watchlist
    cols = ["composite"] + [f for f, _ in FACTORS]
    return {c: float(peers[c].mean()) for c in cols}


@st.cache_data(ttl=300)
def load_flagged_events(employee_id: str, limit: int = 100) -> pd.DataFrame:
    """Sample of the selected employee's flagged medication_activity events.

    A row is flagged if it triggers any of the five anomaly factors (definitions
    match the diversion_metrics measures). flag_reason labels which factor(s).
    """
    pid = sql_str(employee_id)
    return run_query(
        f"""
        SELECT
            event_datetime, shift, department, unit, medication, med_class,
            dea_schedule, event_type, dose_amount, dose_unit, order_id,
            pain_score_before, witness_id, off_shift_flag, out_of_department_flag,
            CONCAT_WS(' | ',
                CASE WHEN event_type='waste' AND witness_id IS NULL AND dea_schedule='CII'
                     THEN 'waste w/o witness (CII)' END,
                CASE WHEN event_type='administer' AND order_id IS NULL
                     THEN 'admin w/o order' END,
                CASE WHEN event_type='administer' AND med_class='opioid'
                          AND (pain_score_before IS NULL OR pain_score_before < 3)
                     THEN 'opioid low/no pain score' END,
                CASE WHEN off_shift_flag THEN 'off-shift' END,
                CASE WHEN out_of_department_flag THEN 'out-of-department' END
            ) AS flag_reason
        FROM {ACTIVITY}
        WHERE employee_id = '{pid}'
          AND (
                (event_type='waste' AND witness_id IS NULL AND dea_schedule='CII')
             OR (event_type='administer' AND order_id IS NULL)
             OR (event_type='administer' AND med_class='opioid'
                 AND (pain_score_before IS NULL OR pain_score_before < 3))
             OR off_shift_flag
             OR out_of_department_flag
          )
        ORDER BY event_datetime DESC
        LIMIT {limit}
        """
    )


def generate_narrative(row: pd.Series, peer_avg_total: float) -> str:
    """LIVE ai_query() call: objective, peer-benchmarked investigation summary.

    Reuses the prompt shape from solutions/02-diversion/02_ai_functions.sql.
    Anomaly counts come straight from the metric-view-aligned watchlist row;
    the peer-group average total is computed in-app and passed in, so the
    narrative matches the benchmark shown on screen.
    """
    prompt = (
        "'You are a controlled-substance diversion analyst. Write a 3-sentence "
        "investigation summary explaining why this employee is flagged, comparing "
        "to the peer-group average. Do not accuse; describe the patterns objectively "
        "and note that findings require human review. Employee '"
    )
    name = sql_str(str(row["employee_name"]))
    role = sql_str(str(row["role"]))
    dept = sql_str(str(row["department"]))
    iris = "NA" if pd.isna(row.get("iris_score")) else f"{float(row['iris_score']):.1f}"
    query = f"""
        SELECT ai_query('{LLM_ENDPOINT}', CONCAT(
            {prompt}, '{name}', ' (', '{role}', ', ', '{dept}', ').',
            ' IRIS risk score {iris}.',
            ' Anomalies over {int(row['total_events'])} recorded events:',
            ' waste-without-witness={int(row['waste_no_witness'])},',
            ' administrations-without-matching-order={int(row['admin_no_order'])},',
            ' opioid-administrations-with-low-or-missing-pain-score={int(row['low_pain_opioid'])},',
            ' off-shift activity={int(row['off_shift'])},',
            ' out-of-department activity={int(row['out_of_dept'])}.',
            ' This employee''s composite anomaly score is {int(row['composite'])};',
            ' the peer group averages roughly {peer_avg_total:.1f} total such anomalies.'
        )) AS narrative
    """
    df = exec_df(query)
    if df.empty or df.iloc[0]["narrative"] is None:
        return "_(No narrative returned.)_"
    return str(df.iloc[0]["narrative"])


# ---------------------------------------------------------------------------
# Case management writeback
# ---------------------------------------------------------------------------
def save_case(employee_id, status, reviewer, notes, composite_score) -> str:
    case_id = str(uuid.uuid4())
    comp = "NULL" if composite_score is None or pd.isna(composite_score) else f"{float(composite_score)}"
    exec_dml(
        f"""
        INSERT INTO {CASES}
            (case_id, employee_id, status, reviewer, notes, composite_score, updated_at)
        VALUES (
            '{sql_str(case_id)}', '{sql_str(employee_id)}', '{sql_str(status)}',
            '{sql_str(reviewer)}', '{sql_str(notes)}', {comp}, current_timestamp()
        )
        """
    )
    return case_id


def load_case_log(employee_id: str = None, limit: int = 20) -> pd.DataFrame:
    where = f"WHERE employee_id = '{sql_str(employee_id)}'" if employee_id else ""
    return exec_df(
        f"""
        SELECT case_id, employee_id, status, reviewer, notes, composite_score, updated_at
        FROM {CASES}
        {where}
        ORDER BY updated_at DESC
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
st.title("🔍 Medication Diversion Investigation Workspace")
st.caption(
    "Controlled-substance diversion case management for St. Luke's. Peer-benchmarked "
    "anomaly signals from Automated Dispensing Cabinet activity, reconciled into a "
    "human-in-the-loop investigation case log. Synthetic workshop data - findings are "
    "descriptive signals that require human review, not determinations of wrongdoing."
)

if not WAREHOUSE_ID:
    st.error("No SQL warehouse configured. Add a **sql-warehouse** resource to this app.")
    st.stop()

try:
    watchlist = load_watchlist()
except Exception as e:  # noqa: BLE001
    st.error(f"Could not load the watchlist from `{METRICS_VIEW}`.\n\n```\n{e}\n```")
    st.info(
        "If this is a permissions error, the app service principal needs SELECT on the "
        "kk_test.med_diversion tables + metric view, USE CATALOG / USE SCHEMA, and CAN USE "
        "on the warehouse."
    )
    st.stop()

# --- Headline tiles ---
planted = watchlist.head(4)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Employees monitored", f"{len(watchlist):,}")
c2.metric("Top composite anomaly score", f"{int(watchlist['composite'].max())}")
c3.metric("Employees with anomalies", f"{int((watchlist['composite'] > 0).sum()):,}")
c4.metric("Avg IRIS (top 4)", f"{planted['iris_score'].mean():.0f}")

st.divider()

left, right = st.columns([2, 3])

# --- Watchlist ---
with left:
    st.subheader("Watchlist")
    st.caption("Ranked by composite anomaly score (from the diversion_metrics metric view).")
    wl_display = watchlist.rename(columns={
        "rank": "#", "employee_id": "Employee", "employee_name": "Name",
        "role": "Role", "department": "Dept", "composite": "Composite",
        "iris_score": "IRIS",
    })[["#", "Employee", "Name", "Role", "Dept", "Composite", "IRIS"]]
    st.dataframe(wl_display, use_container_width=True, hide_index=True, height=460)

# --- Investigate ---
with right:
    st.subheader("Investigate")
    emp_labels = [
        f"#{r['rank']}  {r['employee_id']} - {r['employee_name']} "
        f"(composite {int(r['composite'])})"
        for _, r in watchlist.iterrows()
    ]
    label_to_id = dict(zip(emp_labels, watchlist["employee_id"]))
    sel_label = st.selectbox("Select an employee from the watchlist", emp_labels)
    sel_id = label_to_id[sel_label]
    row = watchlist[watchlist["employee_id"] == sel_id].iloc[0]

    m1, m2, m3 = st.columns(3)
    m1.metric("Composite score", f"{int(row['composite'])}")
    m2.metric("IRIS risk score", "n/a" if pd.isna(row["iris_score"]) else f"{row['iris_score']:.1f}")
    m3.metric("Recorded events", f"{int(row['total_events']):,}")
    st.caption(f"{row['role']} · {row['department']} · peer group {row.get('peer_group_id') or 'n/a'}")

    # ---- Anomaly breakdown vs peer-group average ----
    st.markdown("#### Anomaly breakdown vs peer-group average")
    pavg = peer_averages(watchlist, row.get("peer_group_id"))
    breakdown = pd.DataFrame(
        [
            {
                "Factor": label,
                "This employee": int(row[key]),
                "Peer-group avg": round(pavg[key], 1),
            }
            for key, label in FACTORS
        ]
    )
    st.dataframe(breakdown, use_container_width=True, hide_index=True)
    st.caption(
        f"Composite: this employee {int(row['composite'])} vs peer-group average "
        f"{pavg['composite']:.1f}."
    )

    # ---- Live AI narrative ----
    st.markdown("#### 🧠 Investigation summary (live `ai_query`)")
    st.caption(
        "Objective, peer-benchmarked summary generated live from this employee's "
        "anomaly counts. Descriptive only - requires human review."
    )
    if st.button("Generate investigation summary", type="primary", key="narr_btn"):
        with st.spinner(f"Generating with {LLM_ENDPOINT} (live)..."):
            t0 = time.time()
            try:
                narr = generate_narrative(row, pavg["composite"])
                st.session_state[f"narr_{sel_id}"] = narr
                st.session_state[f"narr_secs_{sel_id}"] = time.time() - t0
            except Exception as e:  # noqa: BLE001
                st.session_state[f"narr_{sel_id}"] = f"_(ai_query failed: {e})_"
                st.session_state[f"narr_secs_{sel_id}"] = time.time() - t0
    narr = st.session_state.get(f"narr_{sel_id}")
    if narr:
        secs = st.session_state.get(f"narr_secs_{sel_id}")
        if secs:
            st.caption(f"Generated live in {secs:.1f}s")
        st.info(narr)

    # ---- Flagged events ----
    st.markdown("#### Flagged events (sample)")
    try:
        events = load_flagged_events(sel_id)
        if events.empty:
            st.caption("No flagged events for this employee.")
        else:
            st.caption(f"Showing {len(events)} most recent flagged events.")
            st.dataframe(events, use_container_width=True, hide_index=True, height=240)
    except Exception as e:  # noqa: BLE001
        st.caption(f"Could not load flagged events: {e}")

    # ---- CASE MANAGEMENT: human-in-the-loop writeback ----
    st.markdown("#### 🗂️ Investigation case (replaces the manual Excel workbook)")
    with st.form(key=f"case_form_{sel_id}", clear_on_submit=False):
        fc1, fc2 = st.columns(2)
        status = fc1.selectbox("Case status", STATUS_OPTIONS)
        reviewer = fc2.text_input("Reviewer", value=current_user())
        notes = st.text_area(
            "Reviewer notes",
            placeholder="Objective, descriptive notes only (e.g. 'Reviewed ADC logs; "
                        "off-shift pattern aligns with a covering-shift assignment - pending manager confirmation').",
            height=90,
        )
        submitted = st.form_submit_button("Save case", type="primary")
        if submitted:
            try:
                cid = save_case(sel_id, status, reviewer, notes, row["composite"])
                st.success(
                    f"Saved case {cid[:8]}… for {sel_id}: **{status}** (by {reviewer})."
                )
            except Exception as e:  # noqa: BLE001
                st.error(
                    f"Save failed (SP needs SELECT+MODIFY on {CASES}):\n\n```\n{e}\n```"
                )

    st.markdown("**Case log for this employee**")
    try:
        log = load_case_log(sel_id)
        if log.empty:
            st.caption("No cases recorded for this employee yet.")
        else:
            st.dataframe(log, use_container_width=True, hide_index=True, height=180)
    except Exception as e:  # noqa: BLE001
        st.caption(f"Could not load case log: {e}")

st.divider()

# --- Full case log ---
st.subheader("All recent investigation cases")
try:
    all_log = load_case_log(limit=25)
    if all_log.empty:
        st.caption("No cases recorded yet. Save one above to start the log.")
    else:
        st.dataframe(all_log, use_container_width=True, hide_index=True)
except Exception as e:  # noqa: BLE001
    st.caption(f"Could not load case log: {e}")

st.divider()

# --- Ask Genie ---
st.subheader("Ask the Diversion Genie Agent")
if not GENIE_SPACE_ID:
    st.info("Genie space not configured (set `DIVERSION_GENIE_SPACE_ID`).")
else:
    st.caption(
        "Natural-language questions answered by the Diversion Genie space over the same data. "
        "Example: *Which employees have the highest composite anomaly score?*"
    )
    q = st.text_input("Question", placeholder="Ask about anomaly patterns, employees, or peer groups...")
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
    "St. Luke's AI Dev Collaboration Workshop · Diversion use case · "
    f"data: `{CATALOG}.{SCHEMA}` · live ai_query narrative + human-in-the-loop case writeback to "
    "`investigation_cases`"
)
