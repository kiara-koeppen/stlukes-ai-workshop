# CKD Identification & Risk Flagging: Participant Guide

## The Problem

CKD stages are frequently missing or incorrectly documented in Epic. Physicians manually review large cohorts to find undocumented cases, high-risk patients, and documentation mismatches. This review is time-consuming and error-prone.

**What we are solving**: Build a system that automatically identifies patients whose lab evidence indicates CKD (stage 3 or higher) but whose Epic documentation is missing or wrong, suggests the correct KDIGO stage, and flags patients at highest risk (advanced stage, not seeing nephrology) for urgent review.

## What You'll Build

You will construct an end-to-end solution using these Databricks assets, all working together:

### 1. Structured Data Layer
- **Registry table**: patient demographics, lab history (creatinine, GFR), albuminuria, documented CKD stage, nephrology referral status, medications.
- **Clinical notes table**: free-text progress notes with embedded clinical signals.

### 2. Semantic Layer (Metric View)
A **metric view** over the registry that defines reusable business logic: what is a "care gap" (lab evidence of CKD but not documented), what is "high-risk" (advanced stage, not seeing nephrology), age bands, etc. This becomes the single source of truth that both your dashboard and your AI agent query.

**Example measures you will compute**:
- Total CKD patients: 1,524
- Care gap patients (undocumented CKD stage 3+): 500
- High-risk patients (stage 4+, no nephrology): 230
- Undocumented CKD rate: 33%

### 3. AI Functions
- **ai_query**: Run against clinical notes to extract whether the note indicates CKD per KDIGO logic and suggests a stage. The LLM returns JSON, which you parse into a struct and flag as "undocumented" if Epic says "No" but the AI says "Yes".

**Output**: 200 notes scored, 102 AI-flagged as undocumented. Precision verified: 102/102 truly have lab-derived stage >= 3.

### 4. Genie Agent
A natural-language query interface over your metric view and tables. Business users ask questions like "How many patients are undocumented for CKD?" and get instant answers without writing SQL.

**Example questions the agent will answer**:
- "Show me the high-risk patients by assigned provider."
- "What is the average GFR in the care-gap cohort?"
- "Break down undocumented CKD by age band."

### 5. AI/BI Dashboard
A visual summary: KPIs for total CKD, care gap, high-risk; charts showing distribution by stage, provider, facility; a table of high-risk patients flagged for review.

## Genie Code Prompts to Get Started

Genie Code is a conversational interface where you describe what you want to build. Here are a few opening prompts to use:

### Build the Metric View
```
I have a table kk_test.clinical.ckd_patient_registry with columns for patient id, actual CKD stage (from labs), 
documented CKD (from Epic), nephrology referral status, age, sex, albuminuria, and medications. 
I need a metric view with dimensions for actual stage, documented stage, age band (45-54, 55-64, 65-74, 75+), 
sex, nephrology status, and a "care gap" flag (true if actual stage >= 3 AND documented in No/None).
Add measures for patient count, count of CKD patients, count of care gap patients, count of high-risk patients 
(stage 4/5, no nephrology), and the undocumented rate. Call it ckd_metrics.
```

### Score Clinical Notes
```
I have a table kk_test.clinical.clinical_notes with columns patient_id, note_id, note_date, and note_text.
I want to use an AI function to extract CKD signals from the notes. For each note, ask: does it indicate CKD? 
What stage? Does it mention nephrology? Return the results as a JSON string, then parse it into a struct so 
I can flag when the AI says CKD but Epic says No/None. Call the result notes_ckd_signals and include the 
undocumented flag.
```

### Create a Dashboard
```
I have a metric view kk_test.clinical.ckd_metrics. Build me a dashboard with:
- KPI tiles for total CKD count, care gap count, high-risk count
- A bar chart of care gap count by actual stage
- A bar chart of high-risk patients by provider
- A table showing high-risk patients with stage, provider, age, nephrology status
Add filters for age band and sex.
```

## From POC to Production

What you build in the workshop is a proof of concept. Moving to production requires:

### 1. Data Ingestion
**Workshop**: We use synthetic data in kk_test. **Production**: Consume the real Epic data via **Lakeflow Connect**, which will pull the FHIR feed on a schedule.

### 2. Governance & Security
**Workshop**: No guardrails (we are learning). **Production**: Use **Unity AI Gateway** to govern the `ai_query` calls. Set rate limits and budgets per team, monitor cost, and ensure only authorized users query PHI-adjacent data. RBAC via Unity Catalog.

### 3. Epic Write-Back (Future Phase)
Leadership has asked whether we can write stage recommendations back into Epic. This is outside the workshop scope but is achievable in a follow-on phase: a downstream job compiles the high-risk list and writes it back via Epic's ADT / HL7 interface or FHIR adaptor.

### 4. Model Quality Monitoring
**Workshop**: We achieve 102/102 precision on 200 scored notes. **Production**: Log the extraction outputs to **MLflow** so you can track precision/recall over time. If performance drifts, retrain or adjust the prompt.

### 5. Genie-on-Volumes for Full Notes
**Workshop**: We score a 200-note sample. **Production**: Attach the full clinical-notes corpus to the Genie Agent using **Genie-on-Volumes** (Beta). This allows business users to ask questions about the notes themselves without manual SQL. Note: Genie-on-Volumes is currently in Beta, so test thoroughly before committing to an SLA.

### 6. Real-Time Alerting
Once you are confident in the care-gap detection, set up a Databricks Alert on the high-risk cohort so that when new patients enter that category, a clinician is notified immediately.

## Key Takeaways

- **Metric Views** are your semantic layer: one place to define "care gap" and "high-risk," shared by dashboards, Genie agents, and downstream jobs.
- **ai_query** can extract structured business logic from unstructured text (notes), and `from_json` lets you parse the JSON response into queryable columns.
- **Genie Agents** are democratizing: now clinicians can ask SQL-like questions without knowing SQL.
- **Governance**: PHI-adjacent data needs budgets, rate limits, and audit logs. Unity AI Gateway makes this enforceable.
