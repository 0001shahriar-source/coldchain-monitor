import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import os

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_demo_links_doc():
    doc = docx.Document()
    
    # 1-inch margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    primary_color = RGBColor(30, 58, 138)     # Navy Blue
    secondary_color = RGBColor(14, 116, 144)  # Cyan Teal
    text_color = RGBColor(30, 41, 59)         # Dark Slate
    link_color = RGBColor(2, 132, 199)        # Vibrant Blue

    # Document Header
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_before = Pt(0)
    p_top.paragraph_format.space_after = Pt(2)
    r_track = p_top.add_run("BUBT TECHATHON 2026 — SUBMISSION COMPONENT\n")
    r_track.font.size = Pt(11)
    r_track.font.bold = True
    r_track.font.color.rgb = secondary_color
    
    r_main = p_top.add_run("Website & Software Demo Links")
    r_main.font.size = Pt(22)
    r_main.font.bold = True
    r_main.font.color.rgb = primary_color

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(15)
    r_sub = p_sub.add_run("Project: ColdChain — Vaccine & Medicine Storage Monitor")
    r_sub.font.size = Pt(11)
    r_sub.font.italic = True
    r_sub.font.color.rgb = text_color

    # Divider
    p_line = doc.add_paragraph()
    p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_line.paragraph_format.space_after = Pt(20)
    r_line = p_line.add_run("―" * 65)
    r_line.font.color.rgb = secondary_color

    # Heading
    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("Live System Demonstration & Simulator Links")
    r_h1.font.color.rgb = primary_color
    r_h1.font.size = Pt(15)
    r_h1.font.bold = True

    p_intro = doc.add_paragraph()
    p_intro.paragraph_format.space_after = Pt(10)
    p_intro.paragraph_format.line_spacing = 1.15
    p_intro.add_run(
        "Judges and evaluators can interact with the complete ColdChain ecosystem through the online simulator, "
        "live web dashboard, and cryptographic audit tools listed below:"
    )

    # Links Table
    table = doc.add_table(rows=5, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    headers = ["System / Component", "Live Access URL", "Evaluation & Testing Instructions"]
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        set_cell_background(hdr_cells[i], "1E3A8A")
        set_cell_margins(hdr_cells[i], top=100, bottom=100, left=120, right=120)
        p = hdr_cells[i].paragraphs[0]
        for r in p.runs:
            r.font.bold = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(255, 255, 255)

    data = [
        ("Wokwi Online Hardware Simulator", 
         "https://wokwi.com/projects/479836419904773121", 
         "Click 'Play' to test live dual NTC temp sliders, door switches, compressor relays, buzzers & real-time OLED status display."),
        
        ("Full-Stack Web Dashboard & API", 
         "http://localhost:5000\n(Or Deployed Cloud Domain)", 
         "Explore real-time dual cooler telemetry, active batch heat budgets, pharmacist batch registration & 1-Click relocation."),
        
        ("Public QR Code Verification", 
         "http://localhost:5000/?tab=publicQr&batchId=BATCH-COV-001", 
         "Scan via smartphone camera to verify live batch viability, heat exposure minutes, and expiration date without login."),
        
        ("Cryptographic Ledger Integrity", 
         "Dashboard -> 'Tamper Logs & Integrity'", 
         "Click 'Verify Integrity' to recalculate the SHA-256 genesis hash chain across all audit logs in real time.")
    ]

    col_widths = [Inches(1.8), Inches(2.7), Inches(2.2)]
    for r_idx, r_val in enumerate(data):
        cells = table.rows[r_idx + 1].cells
        for c_idx, val in enumerate(r_val):
            cells[c_idx].text = val
            set_cell_background(cells[c_idx], "F8FAFC" if r_idx % 2 == 0 else "FFFFFF")
            set_cell_margins(cells[c_idx], top=80, bottom=80, left=100, right=100)
            p = cells[c_idx].paragraphs[0]
            for r in p.runs:
                r.font.size = Pt(8.5)
                r.font.color.rgb = text_color
                if c_idx == 0:
                    r.font.bold = True
                elif c_idx == 1 and "http" in val:
                    r.font.bold = True
                    r.font.color.rgb = link_color

    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

    # User Credentials Section
    h2 = doc.add_heading(level=2)
    r_h2 = h2.add_run("Role-Based Test Credentials for Judges")
    r_h2.font.color.rgb = secondary_color
    r_h2.font.size = Pt(12)
    r_h2.font.bold = True
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(4)
    p_sp.paragraph_format.space_after = Pt(6)

    creds = [
        ("Admin Role: ", "Username: admin | Password: admin123 (Full system control + Discard Red LED latch supervisor override)."),
        ("Pharmacist Role: ", "Username: pharmacist | Password: pharma123 (Register vaccine batches, move batches, and 1-Click Proactive Relocation)."),
        ("Inspector Role: ", "Username: inspector | Password: inspect123 (Read-only compliance audit, live dashboard, and 1-Click Verify Integrity).")
    ]
    for c_title, c_desc in creds:
        p_c = doc.add_paragraph(style='List Bullet')
        p_c.paragraph_format.space_after = Pt(4)
        p_c.paragraph_format.line_spacing = 1.15
        r_cb = p_c.add_run(c_title)
        r_cb.font.bold = True
        r_cb.font.color.rgb = text_color
        p_c.add_run(c_desc)

    out_file = os.path.abspath("ColdChain_Demo_Links.docx")
    doc.save(out_file)
    print(f"Generated standalone demo links document: {out_file}")

if __name__ == "__main__":
    create_demo_links_doc()

