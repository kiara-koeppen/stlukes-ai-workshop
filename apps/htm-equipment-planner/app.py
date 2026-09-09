"""
HTM Equipment Replacement Planner
---------------------------------
Capital replacement-planning tool for St. Luke's Healthcare Technology
Management (HTM / clinical engineering) team.

An HTM planner uses this to:
  1. OVERVIEW: headline KPI tiles (total assets, assets reaching end-of-life
     in 2026, total replacement cost due 2026) plus replacement cost by
     end-of-life year.
  2. PLANNER: filter the 8,000-asset fleet by facility, device family, and
     end-of-life year; see each matching asset's replacement cost and risk score.
  3. INTERACTIVE FUNCTION - build a capital replacement plan: check assets into
     a plan, enter an annual capital budget, watch the app sum selected
     replacement cost against the budget (over / under), and SAVE the plan to
     the Delta table kk_test.htm.replacement_plans. Saved plans are shown back.
  4. Optional: generate a live AI prioritization rationale for the selected
     plan via ai_query().

Runs as the app service principal. All reads/writes go through the app's SQL
warehouse resource. No secrets or tokens are hardcoded.
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
CATALOG = os.getenv("DATABRICKS_CATALOG", "kk_test")
SCHEMA = "htm"
ASSETS = f"{CATALOG}.{SCHEMA}.medical_assets"
METRICS_VIEW = f"{CATALOG}.{SCHEMA}.htm_metrics"
FORECAST = f"{CATALOG}.{SCHEMA}.work_order_forecast"
PLANS = f"{CATALOG}.{SCHEMA}.replacement_plans"

WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")
GENIE_SPACE_ID = os.getenv("HTM_GENIE_SPACE_ID", "").strip()
LLM_ENDPOINT = os.getenv("HTM_LLM_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct")

st.set_page_config(page_title="HTM Equipment Replacement Planner", page_icon="🩺", layout="wide")

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
    """Run a query and return a DataFrame (uncached — for live / write-adjacent reads)."""
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
            COUNT(*)                                                                AS total_assets,
            SUM(CASE WHEN YEAR(support_end_date) = 2026 THEN 1 ELSE 0 END)          AS due_2026,
            SUM(CASE WHEN YEAR(support_end_date) = 2026 THEN replacement_cost ELSE 0 END) AS cost_2026
        FROM {ASSETS}
        """
    )
    r = df.iloc[0]
    return {
        "total_assets": int(r["total_assets"]),
        "due_2026": int(r["due_2026"]),
        "cost_2026": float(r["cost_2026"]),
    }


@st.cache_data(ttl=300)
def load_cost_by_eol() -> pd.DataFrame:
    df = run_query(
        f"""
        SELECT YEAR(support_end_date) AS eol_year,
               COUNT(*)               AS asset_count,
               SUM(replacement_cost)  AS replacement_cost
        FROM {ASSETS}
        WHERE support_end_date IS NOT NULL
        GROUP BY YEAR(support_end_date)
        ORDER BY eol_year
        """
    )
    df["eol_year"] = df["eol_year"].astype(int)
    df["replacement_cost"] = pd.to_numeric(df["replacement_cost"], errors="coerce")
    df["asset_count"] = pd.to_numeric(df["asset_count"], errors="coerce").astype(int)
    return df


@st.cache_data(ttl=300)
def load_filter_options() -> dict:
    fac = run_query(f"SELECT DISTINCT facility FROM {ASSETS} WHERE facility IS NOT NULL ORDER BY facility")
    fam = run_query(f"SELECT DISTINCT asset_description FROM {ASSETS} WHERE asset_description IS NOT NULL ORDER BY asset_description")
    yrs = run_query(
        f"SELECT DISTINCT YEAR(support_end_date) AS y FROM {ASSETS} WHERE support_end_date IS NOT NULL ORDER BY y"
    )
    return {
        "facilities": fac["facility"].tolist(),
        "families": fam["asset_description"].tolist(),
        "eol_years": [int(y) for y in yrs["y"].tolist()],
    }


def load_planner_assets(facility, family, eol_year) -> pd.DataFrame:
    where = ["support_end_date IS NOT NULL"]
    if facility != "All facilities":
        where.append(f"facility = '{sql_str(facility)}'")
    if family != "All device families":
        where.append(f"asset_description = '{sql_str(family)}'")
    if eol_year != "All years":
        where.append(f"YEAR(support_end_date) = {int(eol_year)}")
    clause = " AND ".join(where)
    df = run_query(
        f"""
        SELECT
            asset_number,
            asset_description        AS device_family,
            manufacturer,
            model_number,
            facility,
            department,
            device_status,
            YEAR(support_end_date)   AS eol_year,
            replacement_cost,
            risk_score
        FROM {ASSETS}
        WHERE {clause}
        ORDER BY risk_score DESC, replacement_cost DESC
        LIMIT 500
        """
    )
    df["eol_year"] = pd.to_numeric(df["eol_year"], errors="coerce").astype("Int64")
    df["replacement_cost"] = pd.to_numeric(df["replacement_cost"], errors="coerce")
    df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce")
    return df


def save_plan(plan_id, plan_name, created_by, facility, target_year,
              total_cost, budget, asset_count) -> None:
    exec_dml(
        f"""
        INSERT INTO {PLANS}
            (plan_id, plan_name, created_by, facility, target_year,
             total_cost, budget, asset_count, created_at)
        VALUES (
            '{sql_str(plan_id)}', '{sql_str(plan_name)}', '{sql_str(created_by)}',
            '{sql_str(facility)}', {int(target_year)},
            CAST({float(total_cost)} AS DECIMAL(14,2)),
            CAST({float(budget)} AS DECIMAL(14,2)),
            {int(asset_count)}, current_timestamp()
        )
        """
    )


def load_saved_plans(limit: int = 25) -> pd.DataFrame:
    return exec_df(
        f"""
        SELECT plan_name, created_by, facility, target_year,
               total_cost, budget, asset_count, created_at
        FROM {PLANS}
        ORDER BY created_at DESC
        LIMIT {limit}
        """
    )


def ai_prioritization_rationale(assets_df: pd.DataFrame, budget: float, target_year: int) -> str:
    """LIVE ai_query() call: prioritization rationale for the selected plan."""
    total = float(assets_df["replacement_cost"].sum())
    lines = []
    for _, a in assets_df.head(25).iterrows():
        lines.append(
            f"{a['asset_number']} | {a['device_family']} | {a['facility']} | "
            f"risk {a['risk_score']} | ${float(a['replacement_cost']):,.0f} | EOL {a['eol_year']}"
        )
    fleet = "\\n".join(lines).replace("'", "''")
    prompt = (
        "You are a healthcare technology management (HTM) capital planning advisor for St. Luke's. "
        f"A planner is building a {target_year} equipment replacement plan with a capital budget of "
        f"${budget:,.0f}. The selected assets total ${total:,.0f}. "
        "Given the asset list below (asset | device family | facility | risk score 0-100 | replacement cost | EOL year), "
        "write a concise prioritization rationale (4-6 sentences): which assets to fund first if the budget is tight, "
        "why (weigh clinical risk score, end-of-life year, and cost), and one sentence on any budget shortfall. "
        "Do not invent assets.\\n\\nSELECTED ASSETS:\\n" + fleet
    )
    df = exec_df(f"SELECT ai_query('{LLM_ENDPOINT}', '{prompt}') AS rationale")
    if df.empty or df.iloc[0]["rationale"] is None:
        return "_(No rationale returned.)_"
    return str(df.iloc[0]["rationale"])


# ---------------------------------------------------------------------------
# Genie Conversation API
# ---------------------------------------------------------------------------
def ask_genie(space_id: str, question: str, timeout_s: int = 120) -> dict:
    headers = _cfg.authenticate()
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
st.title("🩺 HTM Equipment Replacement Planner")
st.caption(
    "Capital replacement planning for St. Luke's Healthcare Technology Management. "
    "Fleet lifecycle, end-of-life forecasting, and interactive budget planning over "
    f"`{ASSETS}` (8,000 assets)."
)

if not WAREHOUSE_ID:
    st.error("No SQL warehouse configured. Add a **sql-warehouse** resource to this app.")
    st.stop()

try:
    kpis = load_kpis()
except Exception as e:  # noqa: BLE001
    st.error(f"Could not load metrics from `{ASSETS}`.\n\n```\n{e}\n```")
    st.info(
        "If this is a permissions error, the app service principal needs SELECT on the "
        "kk_test.htm tables plus USE CATALOG / USE SCHEMA, and CAN USE on the warehouse."
    )
    st.stop()

tab_overview, tab_planner, tab_plans = st.tabs(["Overview", "Build a plan", "Saved plans"])

# ===========================================================================
# TAB 1: OVERVIEW
# ===========================================================================
with tab_overview:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total medical assets", f"{kpis['total_assets']:,}")
    c2.metric("Reaching end-of-life in 2026", f"{kpis['due_2026']:,}",
              help="Assets whose manufacturer support ends in 2026")
    c3.metric("Replacement cost due 2026", f"${kpis['cost_2026']:,.0f}")

    st.divider()
    st.subheader("Replacement cost by end-of-life year")
    st.caption("When the fleet reaches manufacturer end-of-support, and the capital exposure each year.")
    cost_df = load_cost_by_eol()
    chart_df = cost_df.set_index("eol_year")[["replacement_cost"]].rename(
        columns={"replacement_cost": "Replacement cost ($)"})
    st.bar_chart(chart_df, height=340)
    show = cost_df.rename(columns={
        "eol_year": "EOL year", "asset_count": "Assets", "replacement_cost": "Replacement cost ($)"})
    show["Replacement cost ($)"] = show["Replacement cost ($)"].map(lambda v: f"${v:,.0f}")
    st.dataframe(show, use_container_width=True, hide_index=True)

# ===========================================================================
# TAB 2: BUILD A PLAN  (interactive cart + writeback)
# ===========================================================================
with tab_planner:
    opts = load_filter_options()
    st.subheader("1. Filter the fleet")
    f1, f2, f3 = st.columns(3)
    sel_facility = f1.selectbox("Facility", ["All facilities"] + opts["facilities"])
    sel_family = f2.selectbox("Device family", ["All device families"] + opts["families"])
    sel_year = f3.selectbox("End-of-life year", ["All years"] + [str(y) for y in opts["eol_years"]],
                            index=(["All years"] + [str(y) for y in opts["eol_years"]]).index("2026")
                            if 2026 in opts["eol_years"] else 0)

    assets = load_planner_assets(sel_facility, sel_family, sel_year)
    st.caption(f"{len(assets):,} matching assets (top 500, sorted by risk then cost). "
               "Check the box to add an asset to your replacement plan.")

    st.subheader("2. Select assets for the plan")
    editable = assets.copy()
    editable.insert(0, "Add to plan", False)
    edited = st.data_editor(
        editable,
        use_container_width=True,
        hide_index=True,
        height=380,
        key=f"planner_editor_{sel_facility}_{sel_family}_{sel_year}",
        column_config={
            "Add to plan": st.column_config.CheckboxColumn("Add to plan", default=False),
            "asset_number": "Asset",
            "device_family": "Device family",
            "manufacturer": "Manufacturer",
            "model_number": "Model",
            "facility": "Facility",
            "department": "Department",
            "device_status": "Status",
            "eol_year": st.column_config.NumberColumn("EOL year", format="%d"),
            "replacement_cost": st.column_config.NumberColumn("Replacement cost", format="$%.0f"),
            "risk_score": st.column_config.NumberColumn("Risk", format="%.1f"),
        },
        disabled=[c for c in editable.columns if c != "Add to plan"],
    )
    selected = edited[edited["Add to plan"]].drop(columns=["Add to plan"])

    st.subheader("3. Budget check")
    total_cost = float(selected["replacement_cost"].sum()) if not selected.empty else 0.0
    default_budget = float(kpis["cost_2026"]) if sel_year == "2026" else 25_000_000.0
    b1, b2 = st.columns([1, 2])
    budget = b1.number_input("Annual capital budget ($)", min_value=0.0,
                             value=float(round(default_budget)), step=1_000_000.0, format="%.0f")

    m1, m2, m3 = st.columns(3)
    m1.metric("Assets selected", f"{len(selected):,}")
    m2.metric("Plan replacement cost", f"${total_cost:,.0f}")
    remaining = budget - total_cost
    m3.metric("Budget remaining", f"${remaining:,.0f}",
              delta=("Under budget" if remaining >= 0 else "OVER budget"),
              delta_color=("normal" if remaining >= 0 else "inverse"))
    if budget > 0:
        pct = min(total_cost / budget, 1.0)
        st.progress(pct, text=f"{total_cost / budget * 100:.0f}% of budget committed")
        if remaining < 0:
            st.warning(f"This plan is **${abs(remaining):,.0f} over** the entered budget.")

    st.subheader("4. Save the plan")
    with st.form(key="save_plan_form", clear_on_submit=False):
        pc1, pc2 = st.columns(2)
        plan_name = pc1.text_input("Plan name", placeholder="e.g. Boise 2026 capital refresh")
        target_year = pc2.number_input("Target year", min_value=2026, max_value=2035,
                                       value=int(sel_year) if sel_year != "All years" else 2026, step=1)
        plan_facility = sel_facility if sel_facility != "All facilities" else "Multiple / all"
        submitted = st.form_submit_button("Save replacement plan", type="primary")
        if submitted:
            if selected.empty:
                st.error("Select at least one asset before saving.")
            elif not plan_name.strip():
                st.error("Give the plan a name.")
            else:
                try:
                    pid = str(uuid.uuid4())
                    save_plan(pid, plan_name.strip(), current_user(), plan_facility,
                              int(target_year), total_cost, budget, len(selected))
                    st.success(
                        f"Saved plan **{plan_name.strip()}** — {len(selected):,} assets, "
                        f"${total_cost:,.0f} vs ${budget:,.0f} budget "
                        f"({'under' if remaining >= 0 else 'OVER'} by ${abs(remaining):,.0f})."
                    )
                except Exception as e:  # noqa: BLE001
                    st.error(f"Save failed (SP needs MODIFY on `{PLANS}`):\n\n```\n{e}\n```")

    # ---- Optional: live AI prioritization rationale ----
    st.subheader("5. AI prioritization rationale (optional)")
    st.caption("Live `ai_query()` call — asks the model how to prioritize the selected assets against the budget.")
    if st.button("Generate prioritization rationale", disabled=selected.empty):
        with st.spinner(f"Generating with {LLM_ENDPOINT} (live)..."):
            try:
                ty = int(target_year)
                st.session_state["ai_rationale"] = ai_prioritization_rationale(selected, budget, ty)
            except Exception as e:  # noqa: BLE001
                st.session_state["ai_rationale"] = f"_(ai_query failed: {e})_"
    if st.session_state.get("ai_rationale"):
        st.markdown(st.session_state["ai_rationale"])

# ===========================================================================
# TAB 3: SAVED PLANS
# ===========================================================================
with tab_plans:
    st.subheader("Saved replacement plans")
    st.caption(f"Written to `{PLANS}` by the app service principal.")
    if st.button("Refresh"):
        pass
    try:
        plans = load_saved_plans()
        if plans.empty:
            st.info("No plans saved yet. Build one in the **Build a plan** tab.")
        else:
            disp = plans.copy()
            disp["total_cost"] = pd.to_numeric(disp["total_cost"], errors="coerce").map(lambda v: f"${v:,.0f}")
            disp["budget"] = pd.to_numeric(disp["budget"], errors="coerce").map(lambda v: f"${v:,.0f}")
            disp = disp.rename(columns={
                "plan_name": "Plan", "created_by": "Created by", "facility": "Facility",
                "target_year": "Target year", "total_cost": "Plan cost", "budget": "Budget",
                "asset_count": "Assets", "created_at": "Created at"})
            st.dataframe(disp, use_container_width=True, hide_index=True, height=400)
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not load saved plans (SP needs SELECT on `{PLANS}`):\n\n```\n{e}\n```")

# ===========================================================================
# Ask Genie (optional)
# ===========================================================================
if GENIE_SPACE_ID:
    st.divider()
    with st.expander("Ask the HTM Genie Agent"):
        q = st.text_input("Question", placeholder="e.g. How many anesthesia machines need replacement in 2026?")
        if st.button("Ask Genie", key="genie_btn") and q:
            with st.spinner("Genie is thinking..."):
                try:
                    res = ask_genie(GENIE_SPACE_ID, q)
                except Exception as e:  # noqa: BLE001
                    res = None
                    st.error(f"Genie call failed (SP needs CAN RUN on space `{GENIE_SPACE_ID}`).\n\n```\n{e}\n```")
            if res:
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
    "St. Luke's AI Dev Collaboration Workshop · HTM use case · "
    f"data: `{CATALOG}.{SCHEMA}` · interactive capital planning with Delta write-back to `replacement_plans`"
)
