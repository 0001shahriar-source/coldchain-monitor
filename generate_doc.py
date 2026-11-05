import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
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

def create_document():
    doc = docx.Document()
    
    # Page Margins: 1 inch all sides
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    primary_color = RGBColor(30, 58, 138)     # Navy Blue
    secondary_color = RGBColor(14, 116, 144)  # Teal Cyan
    text_color = RGBColor(30, 41, 59)         # Slate 800
    gray_color = RGBColor(100, 116, 139)      # Slate 500

    # ------------------ TITLE & COVER HEADER ------------------
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(2)
    run_sub = p_title.add_run("BUBT TECHATHON 2026 — PROJECT DOCUMENTATION & SUBMISSION\n")
    run_sub.font.size = Pt(11)
    run_sub.font.bold = True
    run_sub.font.color.rgb = secondary_color
    
    run_main = p_title.add_run("ColdChain — Vaccine & Medicine Storage Monitor")
    run_main.font.size = Pt(22)
    run_main.font.bold = True
    run_main.font.color.rgb = primary_color
    
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_after = Pt(20)
    r_meta = p_meta.add_run("Smart IoT, Biochemical Heat-Exposure Budget, Cryptographic Trust & Predictive AI")
    r_meta.font.size = Pt(10.5)
    r_meta.font.italic = True
    r_meta.font.color.rgb = gray_color

    # Horizontal Divider Line
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_after = Pt(15)
    r_div = p_div.add_run("―" * 65)
    r_div.font.color.rgb = secondary_color
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ------------------ STEP 1: PROJECT OVERVIEW & CONCEPT ------------------
    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("1. Project Overview & Concept")
    r_h1.font.color.rgb = primary_color
    r_h1.font.size = Pt(15)
    r_h1.font.bold = True

    # 1.1 Executive Summary
    h1_1 = doc.add_heading(level=2)
    r_h1_1 = h1_1.add_run("1.1 Executive Summary")
    r_h1_1.font.color.rgb = secondary_color
    r_h1_1.font.size = Pt(12)
    r_h1_1.font.bold = True

    p_exec = doc.add_paragraph()
    p_exec.paragraph_format.space_after = Pt(8)
    p_exec.paragraph_format.line_spacing = 1.15
    p_exec.add_run(
        "ColdChain is an enterprise-grade IoT cold-storage monitoring, cryptographic audit, and predictive intelligence ecosystem "
        "engineered for biological medicines, insulin, and life-saving vaccines (e.g., COVID-19 mRNA, OPV, Pentavalent). "
        "Unlike conventional data-loggers that passively record failures after vaccines are spoiled, ColdChain implements proactive thermal forecasting, "
        "hardware-level fail-safe protection, cumulative heat-exposure budget modeling, and cryptographic tamper-evident audit ledgers."
    )

    # 1.2 Problem Statement & Global Impact
    h1_2 = doc.add_heading(level=2)
    r_h1_2 = h1_2.add_run("1.2 Problem Statement & Critical Industry Challenges")
    r_h1_2.font.color.rgb = secondary_color
    r_h1_2.font.size = Pt(12)
    r_h1_2.font.bold = True

    p_prob = doc.add_paragraph()
    p_prob.paragraph_format.space_after = Pt(6)
    p_prob.paragraph_format.line_spacing = 1.15
    p_prob.add_run(
        "According to the World Health Organization (WHO), over 50% of vaccines and biological medicines are wasted globally each year "
        "due to temperature excursions in the cold chain. Traditional storage management faces three catastrophic vulnerabilities:"
    )

    bullet_points = [
        ("Passive Spoilage Discovery (Post-Mortem): ", "Traditional USB/memory loggers only notify supervisors after vaccines have experienced irreversible denaturing. Zero real-time alerting leads to silent product degradation."),
        ("Binary Threshold Blindness: ", "Standard systems treat 8.1°C and 15°C as identical 'out of range' events. In reality, biochemical denaturation accelerates exponentially; 13°C destroys potency more than twice as fast as 9°C."),
        ("Tampering & Audit Vulnerability: ", "Centralized hospital/hub databases are vulnerable to data manipulation, accidental deletion, or concealment of improper storage compliance records."),
        ("Unannounced Mechanical Breakdown: ", "Compressor fatigue and power blackouts occur unexpectedly, leaving clinics without contingency relocation windows.")
    ]
    for b_title, b_desc in bullet_points:
        p_bp = doc.add_paragraph(style='List Bullet')
        p_bp.paragraph_format.space_after = Pt(4)
        p_bp.paragraph_format.line_spacing = 1.15
        r_b_title = p_bp.add_run(b_title)
        r_b_title.font.bold = True
        r_b_title.font.color.rgb = text_color
        p_bp.add_run(b_desc)

    # 1.3 The ColdChain Four-Pillar Architecture
    h1_3 = doc.add_heading(level=2)
    r_h1_3 = h1_3.add_run("1.3 The ColdChain Solution (Four Strategic Pillars)")
    r_h1_3.font.color.rgb = secondary_color
    r_h1_3.font.size = Pt(12)
    r_h1_3.font.bold = True

    pillars = [
        ("Pillar 1: Resilient Dual-Chamber IoT Node — ", "A single dual-core ESP32 manages two refrigerated chambers independently. Features dedicated NTC probes, door switches, compressor relays, buzzers, and an integrated OLED status display with local circular offline buffering."),
        ("Pillar 2: Cumulative Heat-Exposure Budget — ", "Enforces a strict 60-minute lifetime allowance above 8°C. Incorporates a 2x double penalty rate for temperatures above 12°C. Automatically transitions batches into 'At Risk' (< 20%) and 'Discard' (0%) with hardware Red LED latching."),
        ("Pillar 3: Cryptographic Trust & SHA-256 Ledger — ", "Telemetry is signed using HMAC-SHA256 with monotonic nonces. Critical operations (moves, overrides, syncs) are immutably chained in a SHA-256 tamper-evident block ledger with 1-click verification."),
        ("Pillar 4: Predictive AI & 1-Click Relocation — ", "A Gradient Boosting Machine forecasts temperatures 30 minutes ahead and scores compressor health (0–100). Imminent breaches trigger an automated, capacity-aware batch relocation recommendation for pharmacists.")
    ]
    for p_title, p_desc in pillars:
        p_pil = doc.add_paragraph(style='List Bullet')
        p_pil.paragraph_format.space_after = Pt(4)
        p_pil.paragraph_format.line_spacing = 1.15
        r_pt = p_pil.add_run(p_title)
        r_pt.font.bold = True
        r_pt.font.color.rgb = primary_color
        p_pil.add_run(p_desc)

    # Add System Architecture Diagram if available
    arch_path = os.path.abspath("bubt hechathon/system architeture.jpg")
    if os.path.exists(arch_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(4)
        doc.add_picture(arch_path, width=Inches(5.8))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(15)
        r_cap = p_cap.add_run("Figure 1: End-to-End ColdChain System Architecture & Telemetry Pipeline")
        r_cap.font.size = Pt(9)
        r_cap.font.italic = True
        r_cap.font.color.rgb = gray_color

    # ------------------ STEP 2: HARDWARE & IMPLEMENTATION DETAILS ------------------
    h2 = doc.add_heading(level=1)
    r_h2 = h2.add_run("2. Hardware Implementation & Fail-Safe Engineering")
    r_h2.font.color.rgb = primary_color
    r_h2.font.size = Pt(15)
    r_h2.font.bold = True

    p_hw = doc.add_paragraph()
    p_hw.paragraph_format.space_after = Pt(8)
    p_hw.paragraph_format.line_spacing = 1.15
    p_hw.add_run(
        "The hardware subsystem is engineered around the high-performance dual-core ESP32 microcontroller, "
        "controlling Cooler A (Fridge 1) and Cooler B (Fridge 2) simultaneously without cross-chamber interference. "
        "The circuit diagram and all hardware behaviors are verified directly in the official Wokwi simulation environment."
    )

    # 2.1 Complete Pinout Table
    h2_1 = doc.add_heading(level=2)
    r_h2_1 = h2_1.add_run("2.1 ESP32 Microcontroller Complete Pinout Mapping")
    r_h2_1.font.color.rgb = secondary_color
    r_h2_1.font.size = Pt(12)
    r_h2_1.font.bold = True

    # Pinout Table
    table = doc.add_table(rows=12, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    headers = ["Subsystem", "Peripheral Component", "ESP32 Pin", "Operational Description & Logic"]
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        set_cell_background(hdr_cells[i], "1E3A8A") # Navy
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=150, right=150)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.bold = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(255, 255, 255)

    pin_data = [
        ("Fridge 1 (Cooler A)", "NTC Temperature Sensor", "GPIO 34 (ADC1)", "10k NTC thermistor (B=3950), Steinhart-Hart equation"),
        ("Fridge 1 (Cooler A)", "Door Switch", "GPIO 15 (Input)", "Active HIGH on unsealed door, triggers instant MQTT report"),
        ("Fridge 1 (Cooler A)", "Compressor Relay", "GPIO 18 (Output)", "ON >= 7.0°C, OFF <= 3.0°C, with 60s min off-delay guard"),
        ("Fridge 1 (Cooler A)", "Red Alert LED", "GPIO 19 (Output)", "Lights on > 8.0°C; Permanently latches on 0% Discard"),
        ("Fridge 1 (Cooler A)", "Dedicated Buzzer", "GPIO 4 (Output)", "Pulsing audible alert when door > 60s continuously open"),
        ("Fridge 2 (Cooler B)", "NTC Temperature Sensor", "GPIO 35 (ADC1)", "10k NTC thermistor (B=3950), Steinhart-Hart equation"),
        ("Fridge 2 (Cooler B)", "Door Switch", "GPIO 13 (Input)", "Active HIGH on unsealed door, triggers instant MQTT report"),
        ("Fridge 2 (Cooler B)", "Compressor Relay", "GPIO 25 (Output)", "ON >= 7.0°C, OFF <= 3.0°C, with 60s min off-delay guard"),
        ("Fridge 2 (Cooler B)", "Red Alert LED", "GPIO 26 (Output)", "Lights on > 8.0°C; Permanently latches on 0% Discard"),
        ("Fridge 2 (Cooler B)", "Dedicated Buzzer", "GPIO 27 (Output)", "Pulsing audible alert when door > 60s continuously open"),
        ("Shared Display & Power", "I2C OLED (SSD1306)", "GPIO 21 (SDA)\nGPIO 22 (SCL)", "128x64 display: Live Temp, Comp, Door, Batt & Safe/Warn/Breach"),
    ]

    col_widths = [Inches(1.5), Inches(1.8), Inches(1.1), Inches(2.3)]
    for row_idx, row in enumerate(pin_data):
        cells = table.rows[row_idx + 1].cells
        bg_color = "F8FAFC" if row_idx % 2 == 0 else "FFFFFF"
        for col_idx, val in enumerate(row):
            cells[col_idx].text = val
            set_cell_background(cells[col_idx], bg_color)
            set_cell_margins(cells[col_idx], top=80, bottom=80, left=120, right=120)
            p = cells[col_idx].paragraphs[0]
            if col_idx == 2:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.size = Pt(8.5)
                r.font.color.rgb = text_color
                if col_idx == 0:
                    r.font.bold = True

    # Set column widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

    # 2.2 Built-In Fail-Safe Mechanisms
    h2_2 = doc.add_heading(level=2)
    r_h2_2 = h2_2.add_run("2.2 Hardware Fail-Safe Guards & Autonomous Protection")
    r_h2_2.font.color.rgb = secondary_color
    r_h2_2.font.size = Pt(12)
    r_h2_2.font.bold = True

    guards = [
        ("Compressor Thermal Off-Delay Guard: ", "Compressor motors burn out if restarted against high head-pressure. The firmware enforces a non-blocking 60-second minimum off-time delay (f1_compOffTime / f2_compOffTime) before restarting."),
        ("Physical Hardware Red LED Latch: ", "When a vaccine batch's heat budget hits 0% (Discard), the firmware latches the physical Red LED permanently ON. It cannot be cleared locally; it requires an HMAC-SHA256 signed supervisor override (CLEAR_RED_LED_LATCH) dispatched from the web backend."),
        ("Audible Door Alarm Guard: ", "If either cooler door is left unsealed for > 60 seconds, the dedicated piezo buzzer (GPIO 4 or GPIO 27) sounds an autonomous hardware alarm, alerting medical staff before thermal damage occurs."),
        ("Circular Offline Buffer (30+ Minutes): ", "During network blackouts, readings are buffered in a local circular memory queue (up to 30+ minutes). Upon reconnecting to HiveMQ, buffered packets auto-replay sequentially (FIFO) to the backend /api/telemetry/sync-offline endpoint with zero duplicates."),
        ("Anti-Replay & HMAC Security: ", "Every telemetry payload is signed using mbedTLS HMAC-SHA256 with per-device monotonic nonces. Replayed or forged packets are rejected immediately by the backend.")
    ]
    for g_title, g_desc in guards:
        p_g = doc.add_paragraph(style='List Bullet')
        p_g.paragraph_format.space_after = Pt(4)
        p_g.paragraph_format.line_spacing = 1.15
        r_gt = p_g.add_run(g_title)
        r_gt.font.bold = True
        r_gt.font.color.rgb = text_color
        p_g.add_run(g_desc)

    # ------------------ STEP 3: DEMO LINKS & SUBMISSION DIRECTORY ------------------
    h3 = doc.add_heading(level=1)
    r_h3 = h3.add_run("3. Live Demonstration, Simulation & Evaluation Links")
    r_h3.font.color.rgb = primary_color
    r_h3.font.size = Pt(15)
    r_h3.font.bold = True

    p_links = doc.add_paragraph()
    p_links.paragraph_format.space_after = Pt(8)
    p_links.paragraph_format.line_spacing = 1.15
    p_links.add_run(
        "All components of ColdChain are fully developed, verified, and accessible for judge review. "
        "The complete online simulator, live code repositories, and demo endpoints are detailed in the official directory below:"
    )

    # Links Table
    link_table = doc.add_table(rows=6, cols=3)
    link_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    link_table.autofit = False

    link_headers = ["Deliverable / Component", "Live Access URL / Repository Location", "Verification Instructions"]
    l_hdr_cells = link_table.rows[0].cells
    for i, h in enumerate(link_headers):
        l_hdr_cells[i].text = h
        set_cell_background(l_hdr_cells[i], "0E7490") # Teal Cyan
        set_cell_margins(l_hdr_cells[i], top=120, bottom=120, left=150, right=150)
        p = l_hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.bold = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(255, 255, 255)

    link_data = [
        ("Wokwi Online Hardware Simulator", "https://wokwi.com/projects/479836419904773121", "Click 'Play' to test dual NTCs, slide switches, compressor relays, buzzers & live OLED display."),
        ("Full-Stack Web Dashboard & API", "http://localhost:5000\n(Deployed: Railway / Localhost)", "Explore live dual cooler cards, heat budgets, 1-Click relocation & tamper-evident ledger."),
        ("Public Scannable QR Verification", "http://localhost:5000/?tab=publicQr&batchId=BATCH-COV-001", "Open or scan QR via smartphone camera to verify batch viability without login."),
        ("Presentation Slides Deck", "ColdChain_Techathon.pptx (14 Slides, 16:9)", "Comprehensive slide deck detailing architecture, security, heat budget, and AI performance."),
        ("Project Demo & Pitch Video (MP4)", "Uploaded to Google Classroom / Drive Link", "3-Minute concise walkthrough following DEMO_VIDEO_SCRIPT_3MIN.md.")
    ]

    l_col_widths = [Inches(1.8), Inches(2.6), Inches(2.3)]
    for row_idx, row in enumerate(link_data):
        cells = link_table.rows[row_idx + 1].cells
        bg_color = "F0FDFA" if row_idx % 2 == 0 else "FFFFFF"
        for col_idx, val in enumerate(row):
            cells[col_idx].text = val
            set_cell_background(cells[col_idx], bg_color)
            set_cell_margins(cells[col_idx], top=90, bottom=90, left=120, right=120)
            p = cells[col_idx].paragraphs[0]
            for r in p.runs:
                r.font.size = Pt(8.5)
                r.font.color.rgb = text_color
                if col_idx == 0:
                    r.font.bold = True
                elif col_idx == 1 and "http" in val:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(2, 132, 199)

    for row in link_table.rows:
        for idx, width in enumerate(l_col_widths):
            row.cells[idx].width = width

    # 3.1 Test User Accounts
    h3_1 = doc.add_heading(level=2)
    r_h3_1 = h3_1.add_run("3.1 Role-Based Access Credentials for Judges")
    r_h3_1.font.color.rgb = secondary_color
    r_h3_1.font.size = Pt(12)
    r_h3_1.font.bold = True

    roles = [
        ("Admin Role: ", "Username: admin | Password: admin123 (Full system authority + Discard Red LED latch supervisor override)."),
        ("Pharmacist Role: ", "Username: pharmacist | Password: pharma123 (Batch registration, cooler transfer, and 1-Click Proactive Relocation)."),
        ("Inspector Role: ", "Username: inspector | Password: inspect123 (Audit access: live dashboard, audit log ledger, and 1-Click Verify Integrity).")
    ]
    for r_title, r_desc in roles:
        p_r = doc.add_paragraph(style='List Bullet')
        p_r.paragraph_format.space_after = Pt(4)
        p_r.paragraph_format.line_spacing = 1.15
        r_rt = p_r.add_run(r_title)
        r_rt.font.bold = True
        r_rt.font.color.rgb = text_color
        p_r.add_run(r_desc)

    # ------------------ STEP 4: AI & SECURITY HIGHLIGHTS ------------------
    h4 = doc.add_heading(level=1)
    r_h4 = h4.add_run("4. Scientific Model Metrics & Cryptographic Integrity")
    r_h4.font.color.rgb = primary_color
    r_h4.font.size = Pt(15)
    r_h4.font.bold = True

    p_sci = doc.add_paragraph()
    p_sci.paragraph_format.space_after = Pt(6)
    p_sci.paragraph_format.line_spacing = 1.15
    p_sci.add_run(
        "To satisfy the technical competition standards, all Machine Learning metrics and Cryptographic ledger operations "
        "are empirically verified through unit execution:"
    )

    sci_facts = [
        ("Machine Learning Predictive Model: ", "Trained using Gradient Boosting Regressor over 8,640 records of thermodynamic simulation (80/20 chronological split). Achieves Mean Absolute Error (MAE) of 0.914°C on a 30-minute ahead horizon, R² of 0.683, with 93.4% breach detection precision."),
        ("Compressor Degradation Scoring: ", "Dynamically computed from thermal extraction gradients during active pumping: Health Score = clip(((cooling_rate - 0.02) / 0.08) * 100, 0, 100). Scores < 50 automatically initiate proactive relocation."),
        ("SHA-256 Tamper-Evident Ledger: ", "Every batch movement, supervisor reset, and offline sync creates a block: Hash_i = SHA-256(Hash_{i-1} || Action || Details || Actor || Timestamp). Clicking 'Verify Integrity' in the UI recalculates the genesis chain in milliseconds.")
    ]
    for s_title, s_desc in sci_facts:
        p_sf = doc.add_paragraph(style='List Bullet')
        p_sf.paragraph_format.space_after = Pt(4)
        p_sf.paragraph_format.line_spacing = 1.15
        r_sft = p_sf.add_run(s_title)
        r_sft.font.bold = True
        r_sft.font.color.rgb = text_color
        p_sf.add_run(s_desc)

    # Save Document
    doc_path = os.path.abspath("ColdChain_Project_Documentation.docx")
    doc.save(doc_path)
    print(f"Generated Word Document: {doc_path}")

if __name__ == "__main__":
    create_document()

