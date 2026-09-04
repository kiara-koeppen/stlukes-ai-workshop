"""
AI Huddle Management board - St. Luke's South Clinic (Nampa)

Centerpiece Databricks App for the "AI Huddle" use case. Supports the morning
triage huddle workflow:

  1. Show the day's patient list (Epic Clarity demographics + AI-extracted
     factors from Teams huddle transcripts) for huddle_date 2026-09-15.
  2. Let a physician enter relationship/complexity scores + assignment for a
     patient and WRITE those inputs back to the Delta table
     kk_test.huddle.physician_inputs (INSERT via the SQL warehouse).
  3. Render the organized huddle board: patients grouped by assigned team
     member, with complexity, assignment balance, and optimal-vs-assigned
     mismatches.

Workshop writeback path: Delta table via the SQL warehouse (implemented here).
PRODUCTION path (documented, not built here): Lakebase Postgres - a low-latency
OLTP store written via the App's OAuth managed credentials, with a synced table
back to Delta for analytics. See README.md.
"""

import os
import datetime as dt

import pandas as pd
import streamlit as st
from databricks import sql
from databricks.sdk.core import Config

# ----------------------------------------------------------------------------
# Configuration (catalog/schema hardcoded per workshop; warehouse via resource)
# ----------------------------------------------------------------------------
CATALOG = "kk_test"
SCHEMA = "huddle"
HUDDLE_DATE = "2026-09-15"  # the day's morning huddle
# Warehouse id: prefer the app resource env var, fall back to the workshop id.
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "c68a614580fefe22")

T_DEMO = f"{CATALOG}.{SCHEMA}.patient_demographics"
T_AIEXT = f"{CATALOG}.{SCHEMA}.transcript_ai_extractions"
T_INPUTS = f"{CATALOG}.{SCHEMA}.physician_inputs"

st.set_page_config(
    page_title="AI Huddle Management | St. Luke's",
    page_icon="🩺",
    layout="wide",
)


# ----------------------------------------------------------------------------
# SQL warehouse connectivity (service-principal OAuth via SDK Config)
# ----------------------------------------------------------------------------
@st.cache_resource
def get_connection():
    """Cached connection to the SQL warehouse using the app's OAuth creds."""
    cfg = Config()  # auto-detects service-principal creds injected by the app
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: cfg.authenticate,
    )


def run_query(statement: str, parameters: dict | None = None) -> pd.DataFrame:
    """Run a SELECT and return a DataFrame. Reconnects once on a stale conn."""
    for attempt in range(2):
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(statement, parameters or {})
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()
            return pd.DataFrame([list(r) for r in rows], columns=cols)
        except Exception:
            get_connection.clear()
            if attempt == 1:
                raise
    return pd.DataFrame()


def run_write(statement: str, parameters: dict | None = None) -> None:
    """Run an INSERT/DML statement. Reconnects once on a stale connection."""
    for attempt in range(2):
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(statement, parameters or {})
            return
        except Exception:
            get_connection.clear()
            if attempt == 1:
                raise


# ----------------------------------------------------------------------------
# Data access
# ----------------------------------------------------------------------------
@st.cache_data(ttl=30)
def load_patients() -> pd.DataFrame:
    return run_query(
        f"""
        SELECT d.pat_id,
               d.pat_name,
               d.age,
               d.sex,
               d.scheduled_visit_reason,
               x.visit_complexity_projection,
               x.psychosocial_complexity_projection,
               x.social_determinants_of_health,
               x.relationship_context
        FROM {T_DEMO} d
        LEFT JOIN {T_AIEXT} x ON d.pat_id = x.pat_id
        WHERE d.huddle_date = DATE'{HUDDLE_DATE}'
        ORDER BY d.pat_name
        """
    )


@st.cache_data(ttl=15)
def load_inputs() -> pd.DataFrame:
    return run_query(
        f"""
        SELECT pi.pat_id,
               d.pat_name,
               pi.provider_name,
               pi.provider_patient_relationship_score AS rel_score,
               pi.patient_complexity_score            AS complexity_score,
               pi.optimal_team_member,
               pi.assigned_team_member,
               pi.non_optimal_assignment_notes,
               pi.physician_notes,
               pi.created_at
        FROM {T_INPUTS} pi
        LEFT JOIN {T_DEMO} d
               ON pi.pat_id = d.pat_id AND pi.huddle_date = d.huddle_date
        WHERE pi.huddle_date = DATE'{HUDDLE_DATE}'
        ORDER BY pi.assigned_team_member, pi.patient_complexity_score DESC
        """
    )


@st.cache_data(ttl=300)
def load_providers() -> pd.DataFrame:
    return run_query(
        f"""
        SELECT DISTINCT provider_id, provider_name
        FROM {T_INPUTS}
        WHERE provider_name IS NOT NULL
        ORDER BY provider_name
        """
    )


def insert_physician_input(row: dict) -> None:
    """INSERT one physician-input row into the Delta writeback table."""
    run_write(
        f"""
        INSERT INTO {T_INPUTS} (
            pat_id, huddle_date, provider_id, provider_name,
            provider_patient_relationship_score, patient_complexity_score,
            physician_notes, optimal_team_member, assigned_team_member,
            non_optimal_assignment_notes, created_at
        )
        VALUES (
            :pat_id, DATE'{HUDDLE_DATE}', :provider_id, :provider_name,
            :rel_score, :complexity_score,
            :physician_notes, :optimal_team_member, :assigned_team_member,
            :non_optimal_assignment_notes, current_timestamp()
        )
        """,
        row,
    )


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------
st.title("🩺 AI Huddle Management")
st.caption(
    f"South Clinic (Nampa) morning triage huddle · {HUDDLE_DATE} · "
    "Epic Clarity demographics + AI-extracted transcript factors + physician input"
)

tab_list, tab_input, tab_board = st.tabs(
    ["📋 Patient List", "✍️ Physician Input", "🗂️ Huddle Board"]
)

# ---- Tab 1: Patient list --------------------------------------------------
with tab_list:
    st.subheader("Today's patients")
    try:
        patients = load_patients()
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not load patients: {e}")
        patients = pd.DataFrame()

    if not patients.empty:
        st.metric("Patients on the huddle list", len(patients))
        st.dataframe(
            patients.rename(
                columns={
                    "pat_id": "Patient ID",
                    "pat_name": "Name",
                    "age": "Age",
                    "sex": "Sex",
                    "scheduled_visit_reason": "Visit reason",
                    "visit_complexity_projection": "Visit complexity (AI)",
                    "psychosocial_complexity_projection": "Psychosocial complexity (AI)",
                    "social_determinants_of_health": "SDOH (AI)",
                    "relationship_context": "Relationship context (AI)",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No patients found for this huddle date.")

# ---- Tab 2: Physician input + writeback -----------------------------------
with tab_input:
    st.subheader("Enter physician input")
    st.caption(
        "Scores are written to the Delta table "
        f"`{T_INPUTS}` via the SQL warehouse (workshop writeback path)."
    )

    try:
        patients = load_patients()
        providers = load_providers()
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not load reference data: {e}")
        patients, providers = pd.DataFrame(), pd.DataFrame()

    if patients.empty:
        st.info("No patients available to score.")
    else:
        pat_options = {
            f"{r.pat_name}  ({r.pat_id})": r.pat_id
            for r in patients.itertuples()
        }
        prov_map = {
            r.provider_name: r.provider_id for r in providers.itertuples()
        }
        prov_names = list(prov_map.keys())
        team_members = prov_names  # optimal/assigned drawn from same roster

        with st.form("physician_input_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                pat_label = st.selectbox("Patient", list(pat_options.keys()))
                provider_name = st.selectbox("Physician (you)", prov_names)
                rel_score = st.slider(
                    "Provider-patient relationship score", -10, 10, 0,
                    help="-10 = no/negative relationship, +10 = strong equity",
                )
                complexity_score = st.slider(
                    "Patient complexity score", -10, 10, 0,
                    help="-10 = very low, +10 = very high complexity",
                )
            with c2:
                optimal_team_member = st.selectbox(
                    "Optimal team member", team_members
                )
                assigned_team_member = st.selectbox(
                    "Assigned team member", team_members
                )
                physician_notes = st.text_area(
                    "Physician notes (optional)", height=80
                )
                non_optimal_notes = st.text_area(
                    "Non-optimal assignment notes (optional)", height=80,
                    help="Why the assigned member differs from optimal, if it does.",
                )

            submitted = st.form_submit_button("Save physician input", type="primary")

        if submitted:
            row = {
                "pat_id": pat_options[pat_label],
                "provider_id": prov_map.get(provider_name, provider_name),
                "provider_name": provider_name,
                "rel_score": int(rel_score),
                "complexity_score": int(complexity_score),
                "physician_notes": physician_notes or None,
                "optimal_team_member": optimal_team_member,
                "assigned_team_member": assigned_team_member,
                "non_optimal_assignment_notes": non_optimal_notes or None,
            }
            try:
                insert_physician_input(row)
                load_inputs.clear()
                st.success(
                    f"Saved input for {pat_label} by {provider_name}. "
                    "Row written to Delta - see the Huddle Board."
                )
                if optimal_team_member != assigned_team_member:
                    st.warning(
                        "Optimal and assigned team members differ - this shows "
                        "up as a mismatch on the Huddle Board."
                    )
            except Exception as e:  # noqa: BLE001
                st.error(f"Writeback failed: {e}")

# ---- Tab 3: Huddle board --------------------------------------------------
with tab_board:
    st.subheader("Organized huddle board")
    st.caption("Patients grouped by assigned team member, highest complexity first.")

    if st.button("🔄 Refresh board"):
        load_inputs.clear()

    try:
        inputs = load_inputs()
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not load huddle board: {e}")
        inputs = pd.DataFrame()

    if inputs.empty:
        st.info("No physician inputs recorded yet for this huddle date.")
    else:
        # Assignment balance across providers
        st.markdown("#### Assignment balance")
        balance = (
            inputs.groupby("assigned_team_member")
            .agg(
                patients=("pat_id", "nunique"),
                inputs=("pat_id", "count"),
                avg_complexity=("complexity_score", "mean"),
            )
            .reset_index()
            .sort_values("inputs", ascending=False)
        )
        bcols = st.columns(len(balance))
        for col, r in zip(bcols, balance.itertuples()):
            col.metric(
                r.assigned_team_member,
                f"{int(r.inputs)} assigned",
                f"avg complexity {r.avg_complexity:.1f}",
            )

        # Mismatch summary
        mismatches = inputs[
            inputs["optimal_team_member"] != inputs["assigned_team_member"]
        ]
        st.markdown(
            f"#### Optimal vs assigned mismatches: **{len(mismatches)}** "
            f"of {len(inputs)} inputs"
        )
        if not mismatches.empty:
            st.dataframe(
                mismatches[
                    [
                        "pat_name", "provider_name", "optimal_team_member",
                        "assigned_team_member", "complexity_score",
                        "non_optimal_assignment_notes",
                    ]
                ].rename(
                    columns={
                        "pat_name": "Patient",
                        "provider_name": "Scored by",
                        "optimal_team_member": "Optimal",
                        "assigned_team_member": "Assigned",
                        "complexity_score": "Complexity",
                        "non_optimal_assignment_notes": "Notes",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        st.markdown("#### Board by assigned team member")
        for member in balance["assigned_team_member"]:
            group = inputs[inputs["assigned_team_member"] == member]
            with st.expander(
                f"{member} — {group['pat_id'].nunique()} patient(s)", expanded=True
            ):
                display = group[
                    [
                        "pat_name", "provider_name", "complexity_score",
                        "rel_score", "optimal_team_member",
                        "non_optimal_assignment_notes",
                    ]
                ].copy()
                display["mismatch"] = (
                    group["optimal_team_member"] != group["assigned_team_member"]
                ).map({True: "⚠️ yes", False: ""})
                st.dataframe(
                    display.rename(
                        columns={
                            "pat_name": "Patient",
                            "provider_name": "Scored by",
                            "complexity_score": "Complexity",
                            "rel_score": "Relationship",
                            "optimal_team_member": "Optimal",
                            "non_optimal_assignment_notes": "Notes",
                            "mismatch": "Mismatch",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

st.divider()
st.caption(
    "Workshop writeback: Delta table via SQL warehouse. "
    "Production path: Lakebase Postgres (OLTP) via the app's OAuth managed "
    "credentials, synced back to Delta for analytics."
)
