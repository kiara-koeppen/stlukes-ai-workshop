#!/usr/bin/env python3
"""Render the Diversion + HTM policy/bulletin HTML (from gen_05/gen_06) to PDFs with fpdf2.
Pure-Python, no system deps. Writes PDFs next to this script under ../data/<uc>/docs/.
Run: uv run --with fpdf2 --python 3.11 python render_pdfs.py
"""
import os, re, importlib.util
from fpdf import FPDF

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = {
    "diversion": os.path.join(HERE, "..", "data", "diversion", "docs"),
    "htm": os.path.join(HERE, "..", "data", "htm", "docs"),
}


def load(mod_file):
    spec = importlib.util.spec_from_file_location(mod_file.replace(".py", ""), os.path.join(HERE, mod_file))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def html_to_pdf(html, out_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    # fpdf2 write_html handles a useful HTML subset (h1-h6, p, ul/ol, table, b/i).
    # Strip <style>/<head> which write_html does not need and can choke on.
    body = re.sub(r"(?is)<style.*?</style>", "", html)
    body = re.sub(r"(?is)<head.*?</head>", "", body)
    try:
        pdf.write_html(body)
    except Exception:
        # Fallback: strip tags to plain text so the PDF still carries the content for Genie.
        text = re.sub(r"(?s)<[^>]+>", " ", body)
        text = re.sub(r"\s+", " ", text).strip()
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 6, text)
    pdf.output(out_path)


def main():
    for d in OUT.values():
        os.makedirs(d, exist_ok=True)
    div = load("gen_05_diversion_pdfs.py")
    htm = load("gen_06_htm_pdfs.py")
    jobs = [
        ("diversion", "01_cii_waste_policy.pdf", div.generate_cii_waste_policy_html),
        ("diversion", "02_medication_admin_sop.pdf", div.generate_medication_administration_sop_html),
        ("diversion", "03_diversion_investigation_sop.pdf", div.generate_diversion_investigation_sop_html),
        ("diversion", "04_peer_comparison_reference.pdf", div.generate_peer_comparison_reference_html),
        ("htm", "01_anesthesia_machine_eol.pdf", htm.generate_anesthesia_machine_eol_html),
        ("htm", "02_infusion_pump_eol.pdf", htm.generate_infusion_pump_eol_html),
        ("htm", "03_ventilator_eol.pdf", htm.generate_ventilator_eol_html),
        ("htm", "04_imaging_equipment_eol.pdf", htm.generate_imaging_equipment_eol_html),
    ]
    for uc, name, fn in jobs:
        out = os.path.join(OUT[uc], name)
        html_to_pdf(fn(), out)
        print(f"{uc:10} {name:36} {os.path.getsize(out):>7} bytes")


if __name__ == "__main__":
    main()
