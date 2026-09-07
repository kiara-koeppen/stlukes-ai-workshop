"""
Generate synthetic vendor end-of-life/end-of-support bulletins for HTM equipment.
These PDFs are grounded in the htm.md schema and reference realistic device families
and end-of-support dates for Genie Agent knowledge retrieval.
"""

def generate_anesthesia_machine_eol_html():
    """End-of-life bulletin for anesthesia machines."""
    return """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 50px; color: #202124; line-height: 1.8; }
        .watermark { color: #ccc; font-size: 14px; margin-bottom: 20px; }
        .header { background: #003d82; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        h1 { color: #003d82; font-size: 28px; margin: 0; }
        .header p { margin: 5px 0; color: white; }
        h2 { color: #003d82; border-bottom: 2px solid #003d82; padding-bottom: 10px; margin-top: 25px; }
        .critical { background: #fce8e6; padding: 15px; border-left: 4px solid #d33b27; margin: 15px 0; }
        .action-box { background: #e8f0fe; padding: 15px; border-left: 4px solid #1a73e8; margin: 15px 0; }
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

    <div class="header">
        <h1>ANESTHESIA MACHINE END-OF-LIFE BULLETIN</h1>
        <p><strong>Manufacturer:</strong> Draeger Medical Systems</p>
        <p><strong>Product Line:</strong> Aisys CS2 and Aisys Compact2</p>
        <p><strong>Bulletin Date:</strong> June 2024</p>
    </div>

    <h2>Executive Summary</h2>
    <p>Draeger Medical Systems is announcing the end of technical support for the Aisys CS2 series anesthesia machines, effective December 31, 2026. This bulletin outlines the support timeline, available options, and recommended replacement pathway.</p>

    <div class="critical">
        <strong>Critical Notice:</strong> All Aisys CS2 units currently in service will reach end-of-life (EOL) status on December 31, 2026. After this date, Draeger will no longer provide technical support, software updates, or spare parts availability on a guaranteed basis.
    </div>

    <h2>Product Information</h2>
    <table>
        <tr>
            <th>Model</th>
            <th>Serial Numbers Affected</th>
            <th>Current Status</th>
            <th>End-of-Support Date</th>
        </tr>
        <tr>
            <td>Aisys CS2</td>
            <td>All units manufactured 2010-2020</td>
            <td>Extended Support Available Until 12/31/2026</td>
            <td>December 31, 2026</td>
        </tr>
        <tr>
            <td>Aisys Compact2</td>
            <td>All units manufactured 2015-2021</td>
            <td>Extended Support Available Until 06/30/2027</td>
            <td>June 30, 2027</td>
        </tr>
    </table>

    <h2>Support Timeline</h2>
    <table>
        <tr>
            <th>Phase</th>
            <th>Dates</th>
            <th>Support Level</th>
        </tr>
        <tr>
            <td>Current</td>
            <td>Through 12/31/2026</td>
            <td>Full technical support, software updates, spare parts</td>
        </tr>
        <tr>
            <td>Extended End-of-Life</td>
            <td>01/01/2027-12/31/2027</td>
            <td>Limited support; spare parts on availability basis only</td>
        </tr>
        <tr>
            <td>Obsolete</td>
            <td>01/01/2028 onward</td>
            <td>No support, no spare parts availability</td>
        </tr>
    </table>

    <h2>Impact on Your Facility</h2>
    <p>After December 31, 2026, the following services will no longer be available:</p>
    <ul>
        <li>Preventive maintenance and calibration services</li>
        <li>Software updates and bug fixes</li>
        <li>Technical support via phone or field service</li>
        <li>Spare parts availability (valves, bellows, CO2 absorbers)</li>
        <li>Regulatory compliance support</li>
    </ul>

    <div class="critical">
        <strong>Regulatory Implication:</strong> Facilities operating unsupported anesthesia equipment may face compliance challenges during regulatory inspections. Patients may also express concerns about equipment age and safety.
    </div>

    <h2>Recommended Actions</h2>

    <div class="action-box">
        <strong>Immediate (2024-2025):</strong>
        <ol>
            <li>Conduct a full inventory of Aisys CS2 and Compact2 units at your facility</li>
            <li>Assess replacement budget and capital planning timelines</li>
            <li>Request quotations from Draeger for replacement systems (Aisys ONE or next-generation models)</li>
            <li>Verify current maintenance contracts; confirm coverage through 12/31/2026</li>
        </ol>
    </div>

    <div class="action-box">
        <strong>Near-Term (2025-2026):</strong>
        <ol>
            <li>Develop replacement plan aligned with OR schedules and budget</li>
            <li>Schedule replacement installations to occur before 12/31/2026</li>
            <li>Budget for operator training on new equipment (2-3 days per staff member)</li>
            <li>Plan for increased maintenance on aging equipment during final year</li>
        </ol>
    </div>

    <h2>Replacement Options</h2>
    <p>Draeger recommends the following replacement models:</p>
    <table>
        <tr>
            <th>Current Equipment</th>
            <th>Recommended Replacement</th>
            <th>Key Benefits</th>
        </tr>
        <tr>
            <td>Aisys CS2</td>
            <td>Aisys ONE</td>
            <td>Improved patient monitoring, advanced ventilation modes, 10-year support commitment</td>
        </tr>
        <tr>
            <td>Aisys Compact2</td>
            <td>Aisys Compact ONE</td>
            <td>Portable design retained, enhanced drug library, extended product lifecycle</td>
        </tr>
    </table>

    <h2>Contact Information</h2>
    <p>For questions or to discuss replacement options:</p>
    <ul>
        <li>Draeger Clinical Support: 1-800-DRAEGER (1-800-372-3437)</li>
        <li>Regional Technical Manager: Available upon request</li>
        <li>Email: healthcare.support@draeger.com</li>
    </ul>

    <div class="footer">
        <p>This bulletin is based on synthetic product information created for training and demonstration purposes.</p>
        <p>For actual end-of-life notices, please contact your equipment manufacturers directly.</p>
    </div>
</body>
</html>"""


def generate_infusion_pump_eol_html():
    """End-of-life bulletin for infusion pumps."""
    return """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 50px; color: #202124; line-height: 1.8; }
        .watermark { color: #ccc; font-size: 14px; margin-bottom: 20px; }
        .header { background: #c41e3a; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        h1 { color: #c41e3a; font-size: 28px; margin: 0; }
        .header p { margin: 5px 0; color: white; }
        h2 { color: #c41e3a; border-bottom: 2px solid #c41e3a; padding-bottom: 10px; margin-top: 25px; }
        .critical { background: #fce8e6; padding: 15px; border-left: 4px solid #d33b27; margin: 15px 0; }
        .action-box { background: #fff3cd; padding: 15px; border-left: 4px solid #f9ab00; margin: 15px 0; }
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

    <div class="header">
        <h1>INFUSION PUMP END-OF-SUPPORT NOTICE</h1>
        <p><strong>Manufacturer:</strong> Baxter International</p>
        <p><strong>Product Line:</strong> COLLEAGUE 3 Infusion Pumps</p>
        <p><strong>Notice Date:</strong> July 2024</p>
    </div>

    <h2>Product Discontinuation Notice</h2>
    <p>Baxter International is announcing the discontinuation of technical support for COLLEAGUE 3 series infusion pumps. This notice outlines the support termination schedule and transition options.</p>

    <div class="critical">
        <strong>End-of-Support Date: June 30, 2026</strong>
        <p>Effective June 30, 2026, Baxter will discontinue technical support and spare parts availability for all COLLEAGUE 3 infusion pump models.</p>
    </div>

    <h2>Affected Models</h2>
    <table>
        <tr>
            <th>Model Number</th>
            <th>Configuration</th>
            <th>Support Ends</th>
        </tr>
        <tr>
            <td>COLLEAGUE 3 Basic</td>
            <td>Single Channel, Standard Drug Library</td>
            <td>06/30/2026</td>
        </tr>
        <tr>
            <td>COLLEAGUE 3 Dual Channel</td>
            <td>Two Infusion Channels, Enhanced Library</td>
            <td>06/30/2026</td>
        </tr>
        <tr>
            <td>COLLEAGUE 3 PCA</td>
            <td>Patient-Controlled Analgesia Module</td>
            <td>06/30/2026</td>
        </tr>
    </table>

    <h2>Support Phase-Out Schedule</h2>
    <ul>
        <li><strong>July 2024 - June 2025:</strong> Full support available. No further software updates planned.</li>
        <li><strong>July 2025 - June 2026:</strong> Limited support. Spare parts available on request but not guaranteed.</li>
        <li><strong>July 2026 onward:</strong> No support. Parts and service unavailable.</li>
    </ul>

    <h2>Spare Parts Availability During Support Period</h2>
    <div class="action-box">
        <p>Baxter will provide the following spare parts on a limited basis through June 30, 2026:</p>
        <ul>
            <li>Pump head and mechanism components</li>
            <li>Door assemblies and seals</li>
            <li>Power supply modules</li>
            <li>Display screens (if available)</li>
        </ul>
        <p><strong>Note:</strong> Battery modules and obsolete electronic components may not be available. Facilities should order critical spare parts by December 31, 2025.</p>
    </div>

    <h2>Recommended Replacement Strategy</h2>

    <p><strong>Phase 1: Assessment (Q3 2024)</strong></p>
    <ul>
        <li>Inventory all COLLEAGUE 3 pumps in service</li>
        <li>Assess condition and expected useful life</li>
        <li>Identify critical clinical needs (ICU, oncology, PCA, etc.)</li>
    </ul>

    <p><strong>Phase 2: Planning (Q4 2024 - Q1 2025)</strong></p>
    <ul>
        <li>Evaluate replacement platforms (Baxter INFUSOR 7000 or competitive products)</li>
        <li>Obtain pricing and lead times</li>
        <li>Budget for replacement hardware and staff training</li>
    </ul>

    <p><strong>Phase 3: Implementation (Q2 2025 - Q2 2026)</strong></p>
    <ul>
        <li>Schedule phased replacement before June 30, 2026</li>
        <li>Conduct staff training on new systems (2-4 hours per user)</li>
        <li>Plan for overlap period where both systems run in parallel</li>
    </ul>

    <h2>Replacement Platform Options</h2>
    <table>
        <tr>
            <th>Replacement Option</th>
            <th>Key Features</th>
            <th>Support Period</th>
        </tr>
        <tr>
            <td>Baxter INFUSOR 7000</td>
            <td>Wireless connectivity, advanced therapy library, electronic charting integration</td>
            <td>10 years</td>
        </tr>
        <tr>
            <td>Hospira Plum A+ Series</td>
            <td>High-acuity infusion, barcode capability, cloud monitoring</td>
            <td>7 years</td>
        </tr>
        <tr>
            <td>B. Braun Space Station</td>
            <td>Multi-channel platform, modular design, European regulatory compliance</td>
            <td>8 years</td>
        </tr>
    </table>

    <h2>Regulatory Compliance</h2>
    <p>Continuing to operate unsupported medical devices may result in:</p>
    <ul>
        <li>FDA warning letters or citations during inspections</li>
        <li>Inability to demonstrate compliance with medical device reporting requirements</li>
        <li>Increased liability in event of adverse patient outcome</li>
        <li>Patient safety concerns and potential loss of accreditation</li>
    </ul>

    <h2>Support Contact</h2>
    <p>For questions regarding COLLEAGUE 3 support or replacement:</p>
    <ul>
        <li>Baxter Clinical Support: 1-800-933-0303</li>
        <li>Equipment Services Manager: Available by appointment</li>
        <li>Email: equipment-eol@baxter.com</li>
    </ul>

    <div class="footer">
        <p>This bulletin contains synthetic product information created for training purposes.</p>
        <p>Please contact manufacturers directly for actual support timelines and replacement guidance.</p>
    </div>
</body>
</html>"""


def generate_ventilator_eol_html():
    """End-of-life bulletin for ventilators."""
    return """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 50px; color: #202124; line-height: 1.8; }
        .watermark { color: #ccc; font-size: 14px; margin-bottom: 20px; }
        .header { background: #1a5c46; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        h1 { color: #1a5c46; font-size: 28px; margin: 0; }
        .header p { margin: 5px 0; color: white; }
        h2 { color: #1a5c46; border-bottom: 2px solid #1a5c46; padding-bottom: 10px; margin-top: 25px; }
        .critical { background: #fce8e6; padding: 15px; border-left: 4px solid #d33b27; margin: 15px 0; }
        .action-box { background: #e8f0fe; padding: 15px; border-left: 4px solid #1a73e8; margin: 15px 0; }
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

    <div class="header">
        <h1>MECHANICAL VENTILATOR END-OF-LIFE ANNOUNCEMENT</h1>
        <p><strong>Manufacturer:</strong> Philips Respironics</p>
        <p><strong>Product Lines:</strong> Achieva and Achieva PS Ventilators</p>
        <p><strong>Announcement Date:</strong> August 2024</p>
    </div>

    <h2>Executive Summary</h2>
    <p>Philips Respironics announces the end of technical support for Achieva series mechanical ventilators effective December 31, 2026. These ventilators have been in service for 10-12 years and are being replaced by next-generation platforms with enhanced monitoring and connectivity.</p>

    <h2>Affected Product Lines</h2>
    <table>
        <tr>
            <th>Ventilator Model</th>
            <th>Manufacturing Period</th>
            <th>Units in Field (Estimate)</th>
            <th>Support End Date</th>
        </tr>
        <tr>
            <td>Achieva v60</td>
            <td>2012-2018</td>
            <td>2,500+</td>
            <td>12/31/2026</td>
        </tr>
        <tr>
            <td>Achieva PS v80</td>
            <td>2014-2020</td>
            <td>3,200+</td>
            <td>12/31/2026</td>
        </tr>
    </table>

    <div class="critical">
        <strong>Critical Timeline:</strong> All Achieva series ventilators will reach end-of-service status on December 31, 2026. After this date, Philips will not provide software updates, spare parts, or technical support.
    </div>

    <h2>Support Phases</h2>

    <p><strong>Phase 1: Current (through 12/31/2025)</strong></p>
    <ul>
        <li>Full technical support available</li>
        <li>Preventive maintenance via service contracts</li>
        <li>Spare parts availability for all components</li>
        <li>Software updates (if applicable)</li>
    </ul>

    <p><strong>Phase 2: End-of-Life (01/01/2026 - 12/31/2026)</strong></p>
    <ul>
        <li>Limited technical support; response times may increase</li>
        <li>Critical spare parts on request (availability not guaranteed)</li>
        <li>No further software updates</li>
    </ul>

    <p><strong>Phase 3: Post-EOL (01/01/2027 onward)</strong></p>
    <ul>
        <li>No technical support</li>
        <li>No spare parts availability</li>
        <li>Facility assumes all maintenance and repair risk</li>
    </ul>

    <h2>Clinical and Operational Implications</h2>

    <div class="action-box">
        <p><strong>Key Considerations for Your ICU/Respiratory Teams:</strong></p>
        <ul>
            <li>Extended repair times if equipment fails after 12/31/2026</li>
            <li>Inability to obtain replacement parts, forcing equipment retirement</li>
            <li>Potential regulatory compliance issues if unsupported equipment is in use</li>
            <li>Need for staff retraining on new ventilator platforms</li>
        </ul>
    </div>

    <h2>Replacement Strategy</h2>

    <div class="action-box">
        <strong>Recommended Approach: Phased Replacement by 2026</strong>
        <ol>
            <li><strong>Assessment Phase (Q4 2024):</strong> Inventory all Achieva units; assess age, condition, and maintenance history</li>
            <li><strong>Planning Phase (Q1 2025):</strong> Evaluate replacement platforms; obtain pricing and lead times</li>
            <li><strong>Budget Phase (Q1-Q2 2025):</strong> Approve capital expenditure; plan financing if needed</li>
            <li><strong>Implementation Phase (Q3 2025-Q3 2026):</strong> Order and install replacement ventilators; conduct staff training</li>
        </ol>
    </div>

    <h2>Recommended Replacement Models</h2>
    <table>
        <tr>
            <th>Current Equipment</th>
            <th>Replacement Model</th>
            <th>Key Improvements</th>
            <th>Support Period</th>
        </tr>
        <tr>
            <td>Achieva v60</td>
            <td>Philips Respironics V680</td>
            <td>Cloud connectivity, touchscreen interface, enhanced lung-protective modes</td>
            <td>10 years</td>
        </tr>
        <tr>
            <td>Achieva PS v80</td>
            <td>Philips Respironics V680 PS</td>
            <td>All V680 features plus pressure support and spontaneous modes</td>
            <td>10 years</td>
        </tr>
    </table>

    <h2>Lead Time and Planning</h2>
    <ul>
        <li><strong>Order Lead Time:</strong> 8-12 weeks typical for ventilators</li>
        <li><strong>Installation Time:</strong> 1-2 weeks per site</li>
        <li><strong>Staff Training:</strong> 3-5 days of intensive training per clinical unit</li>
        <li><strong>Recommended Final Order Date:</strong> September 2026 to ensure installation before EOL</li>
    </ul>

    <h2>Support Contact Information</h2>
    <ul>
        <li>Philips Respironics Customer Care: 1-800-PHILIPS (1-800-745-5747)</li>
        <li>Regional Service Manager: Contact via main number or your account representative</li>
        <li>Email: healthcare.support@philips.com</li>
    </ul>

    <div class="footer">
        <p>This document contains synthetic product information created for training and demonstration purposes.</p>
        <p>For actual end-of-life notices, please contact Philips Respironics or your equipment representative directly.</p>
    </div>
</body>
</html>"""


def generate_imaging_equipment_eol_html():
    """End-of-life bulletin for imaging equipment."""
    return """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 50px; color: #202124; line-height: 1.8; }
        .watermark { color: #ccc; font-size: 14px; margin-bottom: 20px; }
        .header { background: #004b87; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        h1 { color: #004b87; font-size: 28px; margin: 0; }
        .header p { margin: 5px 0; color: white; }
        h2 { color: #004b87; border-bottom: 2px solid #004b87; padding-bottom: 10px; margin-top: 25px; }
        .critical { background: #fce8e6; padding: 15px; border-left: 4px solid #d33b27; margin: 15px 0; }
        .warning { background: #fff3cd; padding: 15px; border-left: 4px solid #f9ab00; margin: 15px 0; }
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

    <div class="header">
        <h1>COMPUTED RADIOGRAPHY SYSTEM END-OF-SUPPORT BULLETIN</h1>
        <p><strong>Manufacturer:</strong> Canon Medical Systems</p>
        <p><strong>Product Line:</strong> Aquilion LB and LB Ultra CR Systems</p>
        <p><strong>Bulletin Date:</strong> September 2024</p>
    </div>

    <h2>Product Discontinuation Notice</h2>
    <p>Canon Medical Systems announces the discontinuation of technical support for Aquilion LB series computed radiography (CR) systems effective June 30, 2027. This notice applies to all Aquilion LB and LB Ultra systems manufactured between 2008 and 2016.</p>

    <div class="critical">
        <strong>End-of-Support Date: June 30, 2027</strong>
        <p>Canon will discontinue technical support, spare parts availability, and software updates for all Aquilion LB series CR systems on June 30, 2027.</p>
    </div>

    <h2>Affected Equipment</h2>
    <table>
        <tr>
            <th>Model</th>
            <th>Manufacturing Years</th>
            <th>Configuration</th>
            <th>Support End Date</th>
        </tr>
        <tr>
            <td>Aquilion LB</td>
            <td>2008-2015</td>
            <td>Standard 40-slice with standard workstation</td>
            <td>06/30/2027</td>
        </tr>
        <tr>
            <td>Aquilion LB Ultra</td>
            <td>2013-2016</td>
            <td>Enhanced 64-slice with advanced reconstruction</td>
            <td>06/30/2027</td>
        </tr>
    </table>

    <h2>Support Timeline</h2>
    <ul>
        <li><strong>Present - 12/31/2025:</strong> Full technical and software support</li>
        <li><strong>01/01/2026 - 06/30/2027:</strong> Limited support; spare parts availability subject to inventory</li>
        <li><strong>07/01/2027 onward:</strong> No support or parts availability</li>
    </ul>

    <div class="warning">
        <strong>Spare Parts Ordering:</strong> Facilities should place orders for critical spare parts (tube assemblies, detector systems, cooling modules) by December 31, 2025 to ensure availability.
    </div>

    <h2>Clinical Impact</h2>
    <p>End-of-support has significant implications for your imaging department:</p>
    <ul>
        <li><strong>Extended Downtime:</strong> Equipment failures may require extended repair times or equipment rental</li>
        <li><strong>Tube Replacement:</strong> X-ray tubes are expensive ($15,000-$30,000); no manufacturer support after EOL</li>
        <li><strong>Regulatory Compliance:</strong> Continuing to operate unsupported diagnostic equipment may affect accreditation and certification</li>
        <li><strong>Clinical Workflow:</strong> Longer repair times disrupt imaging schedules and patient access</li>
    </ul>

    <h2>Recommended Transition Plan</h2>

    <div class="warning">
        <strong>Phase 1: Immediate Assessment (Q4 2024 - Q1 2025)</strong>
        <ul>
            <li>Document all Aquilion LB/LB Ultra systems at your facility</li>
            <li>Assess equipment condition and maintenance history</li>
            <li>Forecast expected component failures based on MTBF data</li>
            <li>Evaluate volume and throughput needs for replacement planning</li>
        </ul>
    </div>

    <div class="warning">
        <strong>Phase 2: Replacement Planning (Q1 - Q2 2025)</strong>
        <ul>
            <li>Evaluate next-generation CT systems from Canon and competitors</li>
            <li>Request proposals and pricing for replacement equipment</li>
            <li>Assess space, power, and network requirements for new equipment</li>
            <li>Plan financing and obtain board approval</li>
        </ul>
    </div>

    <div class="warning">
        <strong>Phase 3: Transition Implementation (Q3 2025 - Q2 2027)</strong>
        <ul>
            <li>Order replacement equipment (lead time 12-16 weeks typical)</li>
            <li>Plan installation and room renovation if needed</li>
            <li>Schedule staff training on new systems (3-4 weeks of intensive training)</li>
            <li>Plan for parallel operation period (both systems running simultaneously)</li>
            <li>Target new equipment operational before 06/30/2027</li>
        </ul>
    </div>

    <h2>Replacement Equipment Options</h2>
    <table>
        <tr>
            <th>Replacement Platform</th>
            <th>Key Features</th>
            <th>Support Commitment</th>
        </tr>
        <tr>
            <td>Canon Aquilion Prime SP</td>
            <td>128-slice MDCT, AI-assisted imaging, cloud-connected, lower radiation dose</td>
            <td>10-year support commitment</td>
        </tr>
        <tr>
            <td>Siemens SOMATOM Drive</td>
            <td>Dual-source 192-slice, cardiology capability, advanced 3D reconstruction</td>
            <td>8-year support contract</td>
        </tr>
        <tr>
            <td>GE Revolution CT</td>
            <td>256-detector-row, spectral imaging capability, AI integration</td>
            <td>10-year support commitment</td>
        </tr>
    </table>

    <h2>Compliance and Regulatory Considerations</h2>
    <ul>
        <li>CMS and accreditation bodies may question use of unsupported diagnostic equipment</li>
        <li>Image quality assurance programs require vendor support for validations</li>
        <li>ACR accreditation may require compliance with equipment age and support guidelines</li>
        <li>Patient liability increases if equipment failure results in diagnostic delay</li>
    </ul>

    <h2>Support Contact</h2>
    <ul>
        <li>Canon Medical Systems Customer Support: 1-888-237-7066</li>
        <li>Regional Service Manager: Contact via main support line</li>
        <li>Email: equipment-support@canon-medical.com</li>
    </ul>

    <div class="footer">
        <p>This document contains synthetic product information created for training and demonstration purposes.</p>
        <p>For actual manufacturer support timelines, contact your equipment vendor directly.</p>
    </div>
</body>
</html>"""


if __name__ == "__main__":
    print("HTM Vendor Bulletin PDF Generator")
    print("This script generates HTML content for synthetic vendor end-of-life bulletins.")
    print("\nAvailable functions:")
    print("  - generate_anesthesia_machine_eol_html()")
    print("  - generate_infusion_pump_eol_html()")
    print("  - generate_ventilator_eol_html()")
    print("  - generate_imaging_equipment_eol_html()")
