"""
Generate synthetic policy and SOP PDFs for the Diversion use case.
These PDFs are grounded in the diversion.md schema and contain realistic
controlled-substance policy content for Genie Agent knowledge retrieval.
"""

def generate_cii_waste_policy_html():
    """Controlled Substance Waste and Witnessing Policy for CII medications."""
    return """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 50px; color: #202124; line-height: 1.8; }
        .watermark { color: #ccc; font-size: 14px; margin-bottom: 20px; }
        h1 { color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 15px; font-size: 28px; }
        h2 { color: #202124; margin-top: 30px; font-size: 18px; border-left: 4px solid #1a73e8; padding-left: 15px; }
        h3 { color: #5f6368; font-size: 14px; margin-top: 15px; }
        .policy-section { margin: 20px 0; }
        .requirement { background: #e8f0fe; padding: 15px; border-left: 4px solid #1a73e8; margin: 15px 0; }
        .critical { background: #fce8e6; padding: 15px; border-left: 4px solid #d33b27; margin: 15px 0; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { border: 1px solid #dadce0; padding: 12px; text-align: left; }
        th { background: #f1f3f4; }
        ul { margin: 10px 0; padding-left: 20px; }
        li { margin: 8px 0; }
        .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #dadce0; color: #5f6368; font-size: 12px; }
    </style>
</head>
<body>
    <div class="watermark">SAMPLE/SYNTHETIC DOCUMENT - For Training and Demonstration Only</div>

    <h1>Controlled Substance Waste and Witnessing Policy</h1>

    <p><strong>Policy Number:</strong> MED-POL-2024-001</p>
    <p><strong>Effective Date:</strong> January 1, 2024</p>
    <p><strong>Last Revised:</strong> September 2024</p>
    <p><strong>Scope:</strong> St. Luke's Health System - All Facilities</p>

    <div class="policy-section">
        <h2>1. Purpose</h2>
        <p>This policy establishes procedures for the proper destruction and witnessing of controlled substances, particularly Schedule II (CII) medications, to ensure compliance with federal and state regulations, prevent medication diversion, and maintain accurate records of all controlled substance transactions.</p>
    </div>

    <div class="policy-section">
        <h2>2. Scope</h2>
        <p>This policy applies to all licensed healthcare providers, pharmacy technicians, and nursing staff at St. Luke's Health System facilities who handle, prepare, administer, or dispose of controlled substances.</p>
    </div>

    <div class="policy-section">
        <h2>3. Policy</h2>

        <h3>3.1 CII Medication Waste Requirements</h3>
        <div class="critical">
            <strong>Mandatory Requirement:</strong> All waste or return of Schedule II (CII) controlled substances must be witnessed by a second licensed healthcare provider (RN, LPN, or other authorized provider).
        </div>
        <p>This requirement applies to:</p>
        <ul>
            <li>Partial doses that cannot be safely administered</li>
            <li>Unused portions of previously opened vials or ampules</li>
            <li>Medications that have expired or been discontinued</li>
            <li>Medications damaged or contaminated during handling</li>
        </ul>

        <h3>3.2 Witness Requirements</h3>
        <div class="requirement">
            <p><strong>Witness Qualifications:</strong> The witnessing provider must:</p>
            <ul>
                <li>Be a licensed healthcare provider (not ancillary staff)</li>
                <li>Have a valid DEA license and current prescriptive authority</li>
                <li>Independently verify the medication, strength, and quantity being wasted</li>
                <li>Document their full name and credentials in the waste record</li>
                <li>Physically observe the entire waste/destruction process</li>
            </ul>
        </div>

        <h3>3.3 Documentation Requirements</h3>
        <p>All controlled substance waste must be documented within the Omnicell system with the following information:</p>
        <table>
            <tr>
                <th>Required Field</th>
                <th>Details</th>
            </tr>
            <tr>
                <td>Witness Name and ID</td>
                <td>Full name and employee ID of witnessing provider</td>
            </tr>
            <tr>
                <td>Date and Time</td>
                <td>Exact timestamp of waste disposal</td>
            </tr>
            <tr>
                <td>Medication Name</td>
                <td>Generic and brand name if applicable</td>
            </tr>
            <tr>
                <td>Strength and Quantity</td>
                <td>Dose amount and unit of measure</td>
            </tr>
            <tr>
                <td>Reason for Waste</td>
                <td>Specific reason (e.g., patient refused, expired, contaminated)</td>
            </tr>
            <tr>
                <td>DEA Form 106</td>
                <td>Reference number if required by pharmacy</td>
            </tr>
        </table>

        <h3>3.4 Waste Destruction Methods</h3>
        <p>CII medications must be destroyed using one of the following approved methods:</p>
        <ul>
            <li><strong>Approved Chemical Destruction:</strong> Omnicell ChemLock pouches or similar DEA-approved kits that render the medication non-recoverable</li>
            <li><strong>Pharmacy Destruction:</strong> Return to pharmacy for destruction via incineration or DEA-approved waste disposal</li>
            <li><strong>Toilet Flushing:</strong> Only if medication is on the FDA flush list; documented and witnessed</li>
        </ul>
    </div>

    <div class="policy-section">
        <h2>4. Audit and Compliance</h2>
        <p>The Diversion Support Team will conduct monthly audits of controlled substance waste records, with particular attention to:</p>
        <ul>
            <li>Waste transactions lacking a documented witness</li>
            <li>Witness credentials not verified in the system</li>
            <li>Frequency of waste by employee or unit</li>
            <li>Reasons for waste discrepancies</li>
        </ul>
        <p>Any waste record found to be non-compliant will trigger an immediate investigation.</p>
    </div>

    <div class="policy-section">
        <h2>5. Violations and Disciplinary Action</h2>
        <p>Violations of this policy may result in:</p>
        <ul>
            <li>Immediate suspension of controlled substance access pending investigation</li>
            <li>Mandatory retraining on controlled substance handling</li>
            <li>Formal disciplinary action up to and including termination</li>
            <li>Report to professional licensing boards</li>
            <li>Referral to law enforcement or DEA as appropriate</li>
        </ul>
    </div>

    <div class="policy-section">
        <h2>6. References</h2>
        <ul>
            <li>21 CFR 1304.23: Records of controlled substances destruction</li>
            <li>State Board of Nursing regulations on controlled substance handling</li>
            <li>St. Luke's Medication Management Policy</li>
            <li>Omnicell System Administration Guidelines</li>
        </ul>
    </div>

    <div class="footer">
        <p>Policy Approved By: Pharmacy Director, Chief Nursing Officer</p>
        <p>This is a synthetic sample document created for training and demonstration purposes.</p>
    </div>
</body>
</html>"""


def generate_medication_administration_sop_html():
    """Medication Administration and Pain Reassessment SOP for opioid medications."""
    return """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 50px; color: #202124; line-height: 1.8; }
        .watermark { color: #ccc; font-size: 14px; margin-bottom: 20px; }
        h1 { color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 15px; font-size: 28px; }
        h2 { color: #202124; margin-top: 30px; font-size: 18px; border-left: 4px solid #1a73e8; padding-left: 15px; }
        h3 { color: #5f6368; font-size: 14px; margin-top: 15px; }
        .step-box { background: #e8f0fe; padding: 15px; margin: 10px 0; border-left: 4px solid #1a73e8; }
        .critical { background: #fce8e6; padding: 15px; border-left: 4px solid #d33b27; margin: 15px 0; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { border: 1px solid #dadce0; padding: 12px; text-align: left; }
        th { background: #f1f3f4; }
        ol { margin: 10px 0; padding-left: 20px; }
        li { margin: 8px 0; }
        .flowchart { background: #f1f3f4; padding: 20px; margin: 20px 0; border-radius: 5px; }
        .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #dadce0; color: #5f6368; font-size: 12px; }
    </style>
</head>
<body>
    <div class="watermark">SAMPLE/SYNTHETIC DOCUMENT - For Training and Demonstration Only</div>

    <h1>Medication Administration and Pain Reassessment Standard Operating Procedure</h1>

    <p><strong>SOP Number:</strong> MED-ADMIN-2024-012</p>
    <p><strong>Effective Date:</strong> January 15, 2024</p>
    <p><strong>Last Revised:</strong> August 2024</p>
    <p><strong>Scope:</strong> Nursing staff administering opioid and analgesic medications</p>

    <div style="margin: 20px 0;">
        <h2>Purpose</h2>
        <p>This SOP establishes standardized procedures for the safe administration of opioid and non-opioid analgesic medications, with emphasis on pain assessment, appropriate documentation, and verification of provider orders to ensure patient safety and regulatory compliance.</p>
    </div>

    <div style="margin: 20px 0;">
        <h2>Pain Assessment and Documentation Requirements</h2>

        <h3>Pre-Administration Assessment (Prior to Medication Dispensing)</h3>
        <div class="critical">
            <strong>Mandatory:</strong> All opioid medications MUST have documented evidence of clinical justification prior to administration, including pain assessment and patient complaint.
        </div>

        <div class="step-box">
            <strong>Step 1: Assess Patient Pain Level</strong>
            <ol>
                <li>Obtain current pain score using facility-approved pain scale (0-10 numeric rating scale)</li>
                <li>Document pain location, quality, and duration</li>
                <li>Assess impact on function and patient goals</li>
                <li>Record assessment in Epic at Time = Admission/Latest Assessment</li>
            </ol>
        </div>

        <p><strong>Pain Score Documentation Requirements:</strong></p>
        <table>
            <tr>
                <th>Opioid Type</th>
                <th>Minimum Pre-Admin Pain Score</th>
                <th>Documentation Required</th>
            </tr>
            <tr>
                <td>All Schedule II opioids (morphine, fentanyl, hydromorphone)</td>
                <td>Pain score 4 or greater, OR documented clinical reason</td>
                <td>Pain reassessment within 30 min pre-administration</td>
            </tr>
            <tr>
                <td>Schedule III/IV opioids (codeine, tramadol)</td>
                <td>Pain score 3 or greater OR documented reason (preventive pre-procedure)</td>
                <td>Pain reassessment or clinical note within 1 hour</td>
            </tr>
            <tr>
                <td>Opioids for palliative/end-of-life care</td>
                <td>Clinical judgment; may vary based on goals of care</td>
                <td>Documented palliative care plan in chart</td>
            </tr>
        </table>

        <h3>Verification of Provider Order</h3>
        <div class="step-box">
            <strong>Step 2: Verify Provider Order</strong>
            <ol>
                <li>Confirm provider order exists in Epic before medication dispensing</li>
                <li>Verify order date and time is PRIOR to administration time</li>
                <li>Check medication name, dose, route, and frequency match order exactly</li>
                <li>Confirm order has not been cancelled or discontinued</li>
                <li>If discrepancy exists, STOP and contact provider immediately</li>
            </ol>
        </div>

        <div class="critical">
            <strong>Critical Safety Rule:</strong> Do not administer any medication without a valid, active provider order dated PRIOR to administration. Administration before order documentation is a medication error.
        </div>

        <h3>Post-Administration Pain Reassessment</h3>
        <div class="step-box">
            <strong>Step 3: Post-Administration Follow-up</strong>
            <ol>
                <li>Reassess pain score 30-60 minutes after opioid administration</li>
                <li>Document post-administration pain score in Epic</li>
                <li>Note pain relief achieved and any adverse effects</li>
                <li>If pain remains above goal, contact provider for additional interventions</li>
            </ol>
        </div>

        <p><strong>Documentation Template in Epic Nursing Note:</strong></p>
        <pre style="background: #f1f3f4; padding: 10px; border-radius: 5px;">
Pre-Admin Assessment: Pain 7/10, right shoulder, sharp quality, limiting arm movement
Order Verified: Morphine 4 mg IV q4h ordered 0730 by Dr. Smith, active order confirmed in Epic
Administration: Morphine 4 mg IV administered 0745 in right antecubital fossa
Post-Admin (0815): Pain reassessment 3/10, patient reports excellent relief, able to perform PT exercises
Witness (if applicable): Jane Doe, RN, observed administration
        </pre>
    </div>

    <div style="margin: 20px 0;">
        <h2>Deviation and Exception Handling</h2>

        <p><strong>When Pain Score Does Not Support Opioid Administration:</strong></p>
        <div class="requirement" style="background: #fff3e0; border-left: 4px solid #f9ab00;">
            <p>If patient pain score is below threshold for opioid (e.g., pain 2/10 but provider ordered morphine):</p>
            <ol>
                <li>Contact ordering provider BEFORE administration</li>
                <li>Verify clinical reason (e.g., preventive pre-procedure medication)</li>
                <li>If provider confirms order despite low pain score, document provider's clinical justification in Epic</li>
                <li>Proceed with administration only after documented justification</li>
            </ol>
        </div>

        <p><strong>When Provider Order Cannot Be Located:</strong></p>
        <ol>
            <li>Contact ordering provider to confirm order placement</li>
            <li>Do not administer from memory or standing orders</li>
            <li>Wait for order entry in Epic before dispensing</li>
            <li>Document communication with provider and time order was placed</li>
        </ol>
    </div>

    <div style="margin: 20px 0;">
        <h2>Audit and Monitoring</h2>
        <p>The Diversion Support Team will monitor medication administration records for:</p>
        <ul>
            <li>Opioid administrations lacking pre-admin pain documentation</li>
            <li>Administration times before documented provider order times</li>
            <li>Missing post-admin pain reassessment</li>
            <li>Inconsistent pain documentation patterns by provider</li>
        </ul>
    </div>

    <div style="margin: 20px 0;">
        <h2>References</h2>
        <ul>
            <li>Joint Commission standards on pain management and medication safety</li>
            <li>Institute for Safe Medication Practices (ISMP) guidelines</li>
            <li>DEA Pharmacy Compliance requirements</li>
            <li>St. Luke's Pain Management Policy</li>
            <li>Epic Medication Administration Module Training Manual</li>
        </ul>
    </div>

    <div class="footer">
        <p>SOP Approved By: Chief Nursing Officer, Pharmacy Director, Medical Staff Leadership</p>
        <p>This is a synthetic sample document created for training and demonstration purposes.</p>
    </div>
</body>
</html>"""


def generate_diversion_investigation_sop_html():
    """Diversion Investigation Procedure SOP."""
    return """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 50px; color: #202124; line-height: 1.8; }
        .watermark { color: #ccc; font-size: 14px; margin-bottom: 20px; }
        h1 { color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 15px; font-size: 28px; }
        h2 { color: #202124; margin-top: 30px; font-size: 18px; border-left: 4px solid #1a73e8; padding-left: 15px; }
        h3 { color: #5f6368; font-size: 14px; margin-top: 15px; }
        .phase-box { background: #e8f0fe; padding: 15px; margin: 15px 0; border-left: 4px solid #1a73e8; }
        .critical { background: #fce8e6; padding: 15px; border-left: 4px solid #d33b27; margin: 15px 0; }
        ol { margin: 10px 0; padding-left: 20px; }
        li { margin: 8px 0; }
        .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #dadce0; color: #5f6368; font-size: 12px; }
    </style>
</head>
<body>
    <div class="watermark">SAMPLE/SYNTHETIC DOCUMENT - For Training and Demonstration Only</div>

    <h1>Diversion Investigation Standard Operating Procedure</h1>

    <p><strong>SOP Number:</strong> DIVERS-INV-2024-005</p>
    <p><strong>Effective Date:</strong> February 1, 2024</p>
    <p><strong>Last Revised:</strong> September 2024</p>
    <p><strong>Scope:</strong> Diversion Support Team and Management - Confidential</p>

    <div style="margin: 20px 0;">
        <h2>Purpose</h2>
        <p>This SOP establishes the standardized investigation process for suspected medication diversion incidents, ensuring thorough, objective analysis while maintaining confidentiality and protecting employee rights. The investigation aims to determine whether diversion has occurred, identify factors contributing to risk, and recommend corrective action.</p>
    </div>

    <div style="margin: 20px 0;">
        <h2>Investigation Phases</h2>

        <div class="phase-box">
            <h3>Phase 1: Report Receipt and Initial Assessment (Days 1-2)</h3>
            <ol>
                <li><strong>Initiation:</strong> Diversion Support Team receives report from pharmacy, nursing management, or audit system alert</li>
                <li><strong>Triage:</strong> Classify severity:
                    <ul>
                        <li>High: CII/CIII loss, multiple red flags, known substance abuse history</li>
                        <li>Medium: Pattern anomalies, single concerning transaction, unwitnessed waste</li>
                        <li>Low: Isolated transaction, benign explanation likely</li>
                    </ul>
                </li>
                <li><strong>Documentation:</strong> Create investigation case record with date, reporter, affected employee, and preliminary facts</li>
                <li><strong>Confidentiality Notice:</strong> Notify all involved parties of confidentiality requirements and investigation protocols</li>
            </ol>
        </div>

        <div class="phase-box">
            <h3>Phase 2: Data Collection and Analysis (Days 3-7)</h3>
            <ol>
                <li><strong>Omnicell Records:</strong> Pull complete medication activity for subject employee for 60-90 days prior
                    <ul>
                        <li>Dispense transactions</li>
                        <li>Waste and return transactions</li>
                        <li>Administration patterns</li>
                        <li>Witness documentation</li>
                    </ul>
                </li>
                <li><strong>Epic Clinical Records:</strong> Obtain corresponding patient records and clinical orders to match against medications dispensed</li>
                <li><strong>Peer Comparison:</strong> Extract medication activity for peer exemplar cohort (same role, unit, shift) for same period to establish baseline</li>
                <li><strong>Anomaly Analysis:</strong> Compare subject vs peers on:
                    <ul>
                        <li>Waste rate and CII waste rate</li>
                        <li>Null transactions (dispense without administration)</li>
                        <li>Pain score correlation with opioid administration</li>
                        <li>Off-shift and out-of-department activity</li>
                    </ul>
                </li>
            </ol>
        </div>

        <div class="phase-box">
            <h3>Phase 3: Interview and Context Gathering (Days 5-10)</h3>
            <div class="critical">
                <strong>Important:</strong> Employee has the right to union representation and legal counsel during interviews. Coordinate with HR and legal before scheduling.
            </div>
            <ol>
                <li><strong>Immediate Supervisor Interview:</strong> Gather contextual information about employee performance, work patterns, any observed behavioral changes</li>
                <li><strong>Peer Interviews (Optional):</strong> If appropriate, brief interviews with co-workers who witnessed activity or can provide context</li>
                <li><strong>Subject Employee Interview:</strong> Conduct only if warranted; allow representation; ask factual questions about specific transactions, not leading questions about suspected diversion</li>
            </ol>
        </div>

        <div class="phase-box">
            <h3>Phase 4: Findings and Recommendations (Days 8-12)</h3>
            <ol>
                <li><strong>Assessment:</strong> Determine level of concern:
                    <ul>
                        <li>No substantial evidence of diversion</li>
                        <li>Anomalies present; requires process improvement or retraining</li>
                        <li>Probable diversion; recommend disciplinary action and possible law enforcement referral</li>
                        <li>Confirmed diversion; immediate referral to law enforcement and professional licensing</li>
                    </ul>
                </li>
                <li><strong>Corrective Actions:</strong> Recommend interventions:
                    <ul>
                        <li>Retraining on medication safety protocols</li>
                        <li>Supervised work period</li>
                        <li>Suspension of controlled substance access</li>
                        <li>Termination (for confirmed diversion)</li>
                    </ul>
                </li>
                <li><strong>System Improvements:</strong> Identify any process or system gaps that enabled anomalies (e.g., inadequate witnessing, poor audit frequency)</li>
            </ol>
        </div>

        <div class="phase-box">
            <h3>Phase 5: Documentation and Reporting (Days 12-15)</h3>
            <ol>
                <li><strong>Investigation Report:</strong> Comprehensive written report including findings, methodology, evidence summary, and recommendations</li>
                <li><strong>Confidentiality:</strong> Report filed in restricted access location; shared only with leadership, HR, legal, and as required by law</li>
                <li><strong>External Reporting:</strong> If law enforcement or DEA referral warranted, coordinate with legal and compliance</li>
                <li><strong>Professional Board Notification:</strong> If confirmed diversion and license suspension warranted, notify state nursing board per regulatory requirements</li>
            </ol>
        </div>
    </div>

    <div style="margin: 20px 0;">
        <h2>Investigation Standards</h2>
        <ul>
            <li>All investigations conducted objectively and without bias</li>
            <li>Presumption of innocence until evidence demonstrates otherwise</li>
            <li>Documentation of all evidence and methodology</li>
            <li>Confidentiality maintained throughout and after investigation</li>
            <li>Legal review of any disciplinary actions or external reporting</li>
        </ul>
    </div>

    <div class="footer">
        <p>SOP Approved By: Chief Medical Officer, Chief Nursing Officer, Legal Counsel, HR Director</p>
        <p>This is a synthetic sample document created for training and demonstration purposes.</p>
    </div>
</body>
</html>"""


def generate_peer_comparison_reference_html():
    """Peer Comparison Methodology Reference document."""
    return """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 50px; color: #202124; line-height: 1.8; }
        .watermark { color: #ccc; font-size: 14px; margin-bottom: 20px; }
        h1 { color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 15px; font-size: 28px; }
        h2 { color: #202124; margin-top: 30px; font-size: 18px; border-left: 4px solid #1a73e8; padding-left: 15px; }
        h3 { color: #5f6368; font-size: 14px; margin-top: 15px; }
        .concept-box { background: #e8f0fe; padding: 15px; margin: 15px 0; border-left: 4px solid #1a73e8; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { border: 1px solid #dadce0; padding: 12px; text-align: left; }
        th { background: #f1f3f4; }
        .formula { background: #f1f3f4; padding: 10px; border-radius: 5px; font-family: monospace; margin: 10px 0; }
        .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #dadce0; color: #5f6368; font-size: 12px; }
    </style>
</head>
<body>
    <div class="watermark">SAMPLE/SYNTHETIC DOCUMENT - For Training and Demonstration Only</div>

    <h1>Peer Comparison Methodology Reference</h1>

    <p><strong>Document Number:</strong> DIVERS-REF-PEER-2024</p>
    <p><strong>Effective Date:</strong> March 1, 2024</p>
    <p><strong>Audience:</strong> Diversion Support Team, Clinical Leadership</p>

    <div style="margin: 20px 0;">
        <h2>Overview</h2>
        <p>Peer comparison analysis is a statistical method used to identify medication dispensing and administration patterns that deviate significantly from a defined peer exemplar cohort. This reference document defines the methodology, cohort selection criteria, metrics, and interpretation guidelines used by the Diversion Support Team.</p>
    </div>

    <div style="margin: 20px 0;">
        <h2>Peer Cohort Definition</h2>

        <div class="concept-box">
            <p><strong>Peer Exemplar Cohort:</strong> A group of 15-30 licensed healthcare providers who share key characteristics with the subject employee, used as a statistical baseline for comparison.</p>
        </div>

        <h3>Cohort Selection Criteria</h3>
        <table>
            <tr>
                <th>Criterion</th>
                <th>Definition</th>
                <th>Rationale</th>
            </tr>
            <tr>
                <td>Licensed Role</td>
                <td>RN, LPN, Tech (same as subject)</td>
                <td>Role determines scope of practice and medication access</td>
            </tr>
            <tr>
                <td>Unit/Department</td>
                <td>Same as subject (e.g., Med-Surg, ICU, ED)</td>
                <td>Patient acuity and medication utilization varies by unit</td>
            </tr>
            <tr>
                <td>Shift</td>
                <td>Same shift as subject (Day/Evening/Night)</td>
                <td>Medication utilization patterns differ by shift</td>
            </tr>
            <tr>
                <td>Time Period</td>
                <td>Minimum 60 days of concurrent activity</td>
                <td>Sufficient data for meaningful statistical comparison</td>
            </tr>
            <tr>
                <td>Data Quality</td>
                <td>Providers with complete record documentation</td>
                <td>Excludes providers with intermittent charting or gaps</td>
            </tr>
        </table>
    </div>

    <div style="margin: 20px 0;">
        <h2>Comparison Metrics</h2>

        <h3>1. Waste Rate and CII Waste Rate</h3>
        <div class="concept-box">
            <p><strong>Definition:</strong> Percentage of medications dispensed that were wasted (not administered to patient).</p>
            <p><strong>Formula:</strong></p>
            <div class="formula">
            Waste Rate = (Total Waste Transactions / Total Dispense Transactions) * 100%
            CII Waste Rate = (CII Waste Transactions / Total CII Dispense Transactions) * 100%
            </div>
            <p><strong>Interpretation:</strong> Rates significantly above peer group (>2 standard deviations) may indicate inappropriate dispensing, poor technique, or concerning patterns.</p>
        </div>

        <h3>2. Null Transaction Rate</h3>
        <div class="concept-box">
            <p><strong>Definition:</strong> Percentage of dispensed medications with no corresponding administration record.</p>
            <p><strong>Formula:</strong></p>
            <div class="formula">
            Null Rate = (Dispense with No Admin Record / Total Dispense) * 100%
            </div>
            <p><strong>Interpretation:</strong> Elevated null rates suggest medications dispensed but not given, potentially diverted.</p>
        </div>

        <h3>3. Pain-Score Correlation Index</h3>
        <div class="concept-box">
            <p><strong>Definition:</strong> Percentage of opioid administrations preceded by documented pain assessment at threshold level (pain >= 4/10).</p>
            <p><strong>Calculation:</strong></p>
            <div class="formula">
            Correlation Index = (Opioid Admins with Pain >= 4 / Total Opioid Admins) * 100%
            </div>
            <p><strong>Peer Baseline:</strong> Typical range 85-95% for nurses in med-surg and critical care settings.</p>
            <p><strong>Interpretation:</strong> Scores significantly below peer baseline (<70%) suggest opioids administered without clear clinical justification.</p>
        </div>

        <h3>4. Off-Shift Activity Percentage</h3>
        <div class="concept-box">
            <p><strong>Definition:</strong> Percentage of medication transactions occurring outside scheduled shift hours.</p>
            <p><strong>Interpretation:</strong> Elevated off-shift activity may indicate unauthorized access or system manipulation.</p>
        </div>
    </div>

    <div style="margin: 20px 0;">
        <h2>Statistical Thresholds for Concern</h2>

        <p>Deviations from peer baseline are categorized by statistical distance:</p>
        <table>
            <tr>
                <th>Distance from Peer Mean</th>
                <th>Level of Concern</th>
                <th>Action</th>
            </tr>
            <tr>
                <td>Within 1 SD (normal variation)</td>
                <td>None</td>
                <td>No action required</td>
            </tr>
            <tr>
                <td>1-2 SD above mean</td>
                <td>Low</td>
                <td>Monitor; document in system</td>
            </tr>
            <tr>
                <td>2-3 SD above mean</td>
                <td>Moderate</td>
                <td>Discuss with manager; may initiate brief investigation</td>
            </tr>
            <tr>
                <td>>3 SD above mean</td>
                <td>High</td>
                <td>Initiate full investigation; consider disciplinary action</td>
            </tr>
        </table>
    </div>

    <div style="margin: 20px 0;">
        <h2>Limitations and Cautions</h2>
        <ul>
            <li><strong>Patient Mix Variation:</strong> Even within same unit, patient acuity can vary; accounts for some medication utilization differences</li>
            <li><strong>Experience Level:</strong> Newer staff may have higher waste rates; should be compared only to similar-experience peers when possible</li>
            <li><strong>One Month is Not Enough:</strong> A single outlier month does not confirm diversion; 60-90 day patterns are more meaningful</li>
            <li><strong>Multiple Comparisons:</strong> If many metrics are compared, expect some anomalies by chance; focus on consistent patterns across multiple metrics</li>
        </ul>
    </div>

    <div class="footer">
        <p>Document Approved By: Diversion Support Team Lead, Pharmacy Director, Statistical Analysis Consultant</p>
        <p>This is a synthetic sample document created for training and demonstration purposes.</p>
    </div>
</body>
</html>"""


if __name__ == "__main__":
    print("Diversion PDF Generator")
    print("This script generates HTML content for synthetic policy PDFs.")
    print("\nTo use these functions with generate_and_upload_pdf:")
    print("  1. Call generate_cii_waste_policy_html()")
    print("  2. Call generate_medication_administration_sop_html()")
    print("  3. Call generate_diversion_investigation_sop_html()")
    print("  4. Call generate_peer_comparison_reference_html()")
