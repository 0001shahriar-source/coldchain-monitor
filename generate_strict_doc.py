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

def generate_strict_serial_document():
    doc = docx.Document()
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    primary_color = RGBColor(30, 58, 138)     # Navy Blue (#1E3A8A)
    secondary_color = RGBColor(14, 116, 144)  # Cyan Teal (#0E7490)
    text_color = RGBColor(30, 41, 59)         # Dark Slate (#1E293B)
    gray_color = RGBColor(100, 116, 139)      # Muted Gray (#64748B)

    # ------------------ TITLE & HEADER ------------------
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_before = Pt(0)
    p_top.paragraph_format.space_after = Pt(2)
    r_track = p_top.add_run("BUBT TECHATHON 2026 — PROJECT DOCUMENTATION / CONCEPT SUBMISSION\n")
    r_track.font.size = Pt(11)
    r_track.font.bold = True
    r_track.font.color.rgb = secondary_color
    
    r_main = p_top.add_run("Project: ColdChain — Vaccine & Medicine Storage Monitor")
    r_main.font.size = Pt(22)
    r_main.font.bold = True
    r_main.font.color.rgb = primary_color

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(15)
    r_sub = p_sub.add_run("Intelligent Dual-Chamber IoT Controller, Heat-Exposure Budget, Cryptographic Trust & Predictive AI")
    r_sub.font.size = Pt(10.5)
    r_sub.font.italic = True
    r_sub.font.color.rgb = gray_color

    p_line = doc.add_paragraph()
    p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_line.paragraph_format.space_after = Pt(20)
    r_line = p_line.add_run("―" * 65)
    r_line.font.color.rgb = secondary_color

    # =========================================================================
    # SERIAL 1: Project Overview & Concept
    # =========================================================================
    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("1. Project Overview & Concept")
    r_h1.font.color.rgb = primary_color
    r_h1.font.size = Pt(16)
    r_h1.font.bold = True

    # 1.1 Executive Summary
    p1 = doc.add_paragraph()
    p1.paragraph_format.space_after = Pt(8)
    p1.paragraph_format.line_spacing = 1.15
    r_t1 = p1.add_run("Executive Summary: ")
    r_t1.font.bold = True
    r_t1.font.color.rgb = secondary_color
    p1.add_run(
        "ColdChain is an enterprise-grade IoT cold-storage monitoring, cryptographic audit, and predictive intelligence system "
        "engineered for sensitive biological vaccines (COVID-19 mRNA, Polio, Pentavalent) and medicines (Insulin). "
        "Unlike conventional data loggers that passively record spoilage after products are ruined, ColdChain features proactive thermal forecasting, "
        "hardware fail-safes, biochemical heat-exposure budget modeling, and cryptographic tamper-evident audit chains."
    )

    # 1.2 Problem Statement
    p2 = doc.add_paragraph()
    p2.paragraph_format.space_after = Pt(6)
    p2.paragraph_format.line_spacing = 1.15
    r_t2 = p2.add_run("Problem Statement & Global Need: ")
    r_t2.font.bold = True
    r_t2.font.color.rgb = secondary_color
    p2.add_run(
        "According to the World Health Organization (WHO), over 50% of temperature-sensitive vaccines and biological medicines are wasted "
        "globally each year due to thermal cold-chain failures (freezing below 2°C or overheating above 8°C). "
        "Current solutions face three fundamental failures:"
    )

    bullet_points = [
        ("Passive Spoilage Discovery: ", "Traditional USB/paper loggers only notify supervisors after vaccines are already spoiled. Zero real-time alarming means damage occurs silently."),
        ("Binary Threshold Blindness: ", "Standard monitors treat 8.1°C and 15°C identically. In reality, biochemical denaturation accelerates exponentially; 13°C ruins vaccine potency more than twice as fast as 9°C."),
        ("Centralized Tampering Risk: ", "Logbooks and standard databases can be altered or deleted to conceal compliance failures, risking patient safety."),
        ("Unannounced Compressor Fatigue: ", "Mechanical compressors degrade over time without warning, leading to catastrophic sudden cooler failure.")
    ]
    for b_title, b_desc in bullet_points:
        p_bp = doc.add_paragraph(style='List Bullet')
        p_bp.paragraph_format.space_after = Pt(4)
        p_bp.paragraph_format.line_spacing = 1.15
        r_b_title = p_bp.add_run(b_title)
        r_b_title.font.bold = True
        r_b_title.font.color.rgb = text_color
        p_bp.add_run(b_desc)

    # 1.3 Solution & Concept
    p3 = doc.add_paragraph()
    p3.paragraph_format.space_before = Pt(6)
    p3.paragraph_format.space_after = Pt(6)
    p3.paragraph_format.line_spacing = 1.15
    r_t3 = p3.add_run("The ColdChain Four-Pillar Concept: ")
    r_t3.font.bold = True
    r_t3.font.color.rgb = secondary_color
    p3.add_run(
        "To eliminate vaccine wastage, ColdChain integrates four autonomous protection layers:"
    )

    pillars = [
        ("Dual-Chamber IoT Node: ", "One single ESP32 manages two refrigerated chambers independently with hardware-level compressor delay guards, unsealed door buzzers, and a 30+ minute circular offline buffer."),
        ("Biochemical Heat-Exposure Budget: ", "Tracks a continuous 60-minute lifetime allowance above 8°C, with a 2x double penalty above 12°C. Automatically transitions batches to 'At Risk' (< 20%) and 'Discard' (0%) with hardware Red LED latching."),
        ("Cryptographic Trust & SHA-256 Ledger: ", "Device telemetry is authenticated via HMAC-SHA256 and monotonic nonces. Critical operations (moves, supervisor overrides, syncs) are locked in an immutable SHA-256 tamper-evident hash chain."),
        ("Predictive AI & 1-Click Relocation: ", "Machine Learning forecasts chamber temperatures 30 minutes ahead and scores compressor mechanical health (0–100). Imminent breaches trigger an automated, capacity-aware 1-Click Relocation action for pharmacists.")
    ]
    for p_title, p_desc in pillars:
        p_pil = doc.add_paragraph(style='List Bullet')
        p_pil.paragraph_format.space_after = Pt(4)
        p_pil.paragraph_format.line_spacing = 1.15
        r_pt = p_pil.add_run(p_title)
        r_pt.font.bold = True
        r_pt.font.color.rgb = primary_color
        p_pil.add_run(p_desc)

    # System Architecture Image
    arch_path = os.path.abspath("bubt hechathon/system architeture.jpg")
    if os.path.exists(arch_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(10)
        p_img.paragraph_format.space_after = Pt(4)
        doc.add_picture(arch_path, width=Inches(5.8))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(20)
        r_cap = p_cap.add_run("Figure 1: ColdChain End-to-End System Architecture & Dataflow")
        r_cap.font.size = Pt(9)
        r_cap.font.italic = True
        r_cap.font.color.rgb = gray_color

    # =========================================================================
    # SERIAL 2: Presentation Slides (PDF/PPT)
    # =========================================================================
    h2 = doc.add_heading(level=1)
    r_h2 = h2.add_run("2. Presentation Slides (PDF/PPT)")
    r_h2.font.color.rgb = primary_color
    r_h2.font.size = Pt(16)
    r_h2.font.bold = True

    p_slide = doc.add_paragraph()
    p_slide.paragraph_format.space_after = Pt(6)
    p_slide.paragraph_format.line_spacing = 1.15
    p_slide.add_run(
        "A complete, professional 14-slide widescreen (16:9) presentation deck has been designed and submitted. "
        "It outlines the complete engineering lifecycle from problem statement to empirical model evaluation."
    )

    t_slide = doc.add_table(rows=3, cols=2)
    t_slide.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_slide.autofit = False
    
    s_headers = ["Presentation Format / Item", "File Name & Access Location"]
    s_hdr_cells = t_slide.rows[0].cells
    for i, h in enumerate(s_headers):
        s_hdr_cells[i].text = h
        set_cell_background(s_hdr_cells[i], "1E3A8A")
        set_cell_margins(s_hdr_cells[i], top=100, bottom=100, left=150, right=150)
        p = s_hdr_cells[i].paragraphs[0]
        for r in p.runs:
            r.font.bold = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(255, 255, 255)

    s_data = [
        ("PowerPoint Presentation (16:9)", "ColdChain_Techathon.pptx (Attached in Classroom submission)"),
        ("Slide Highlights Included", "• Dual-Chamber ESP32 Architecture • Heat Budget (1x/2x, Latch)\n• HMAC-SHA256 & Nonce Replay • SHA-256 Tamper-Evident Ledger\n• AI 30-Min Forecast (93.4% Prec, 0.914°C MAE) • 1-Click Relocation")
    ]
    s_widths = [Inches(2.5), Inches(4.2)]
    for r_idx, r_val in enumerate(s_data):
        cells = t_slide.rows[r_idx + 1].cells
        for c_idx, val in enumerate(r_val):
            cells[c_idx].text = val
            set_cell_background(cells[c_idx], "F8FAFC" if r_idx % 2 == 0 else "FFFFFF")
            set_cell_margins(cells[c_idx], top=80, bottom=80, left=120, right=120)
            p = cells[c_idx].paragraphs[0]
            for r in p.runs:
                r.font.size = Pt(9)
                r.font.color.rgb = text_color
                if c_idx == 0:
                    r.font.bold = True

    for row in t_slide.rows:
        for idx, width in enumerate(s_widths):
            row.cells[idx].width = width

    doc.add_paragraph().paragraph_format.space_after = Pt(15)

    # =========================================================================
    # SERIAL 3: Maximum 3-Minute Project Pitch / Demo Video (MP4)
    # =========================================================================
    h3 = doc.add_heading(level=1)
    r_h3 = h3.add_run("3. Maximum 3-Minute Project Pitch / Demo Video (MP4)")
    r_h3.font.color.rgb = primary_color
    r_h3.font.size = Pt(16)
    r_h3.font.bold = True

    p_vid = doc.add_paragraph()
    p_vid.paragraph_format.space_after = Pt(8)
    p_vid.paragraph_format.line_spacing = 1.15
    p_vid.add_run(
        "A concise 3-minute video demonstration has been recorded covering live hardware telemetry, "
        "heat-exposure budget degradation, proactive AI relocation, and public QR code verification."
    )

    t_vid = doc.add_table(rows=3, cols=2)
    t_vid.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_vid.autofit = False

    v_headers = ["Video Attribute", "Details & Direct Access Link"]
    v_hdr_cells = t_vid.rows[0].cells
    for i, h in enumerate(v_headers):
        v_hdr_cells[i].text = h
        set_cell_background(v_hdr_cells[i], "0E7490")
        set_cell_margins(v_hdr_cells[i], top=100, bottom=100, left=150, right=150)
        p = v_hdr_cells[i].paragraphs[0]
        for r in p.runs:
            r.font.bold = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(255, 255, 255)

    v_data = [
        ("Video Demo Direct Link\n(Google Drive / YouTube)", "[PASTE YOUR VIDEO LINK HERE]\n(e.g., https://drive.google.com/file/d/YOUR_VIDEO_ID/view?usp=sharing)"),
        ("Video Breakdown Timeline\n(Exactly 2:50 - 3:00 Mins)", "• 0:00 - 0:35: Cold-Chain Problem & 4-Pillar System Overview\n• 0:35 - 1:20: ESP32 Hardware Demo (OLED, 60s Comp Guard, Door Buzzer)\n• 1:20 - 2:05: Live Dashboard & Heat Budget (1x/2x rate, 0% Red LED Latch)\n• 2:05 - 2:35: AI 30-Min Prediction, 1-Click Relocation & SHA-256 Ledger Verify\n• 2:35 - 3:00: Public Smartphone QR Code Scanning & Conclusion")
    ]
    v_widths = [Inches(2.5), Inches(4.2)]
    for r_idx, r_val in enumerate(v_data):
        cells = t_vid.rows[r_idx + 1].cells
        for c_idx, val in enumerate(r_val):
            cells[c_idx].text = val
            set_cell_background(cells[c_idx], "F0FDFA" if r_idx % 2 == 0 else "FFFFFF")
            set_cell_margins(cells[c_idx], top=80, bottom=80, left=120, right=120)
            p = cells[c_idx].paragraphs[0]
            for r in p.runs:
                r.font.size = Pt(9)
                r.font.color.rgb = text_color
                if c_idx == 0:
                    r.font.bold = True
                elif "PASTE" in val:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(2, 132, 199)

    for row in t_vid.rows:
        for idx, width in enumerate(v_widths):
            row.cells[idx].width = width

    doc.add_paragraph().paragraph_format.space_after = Pt(15)

    # =========================================================================
    # SERIAL 4: Hardware & Implementation Details
    # =========================================================================
    h4 = doc.add_heading(level=1)
    r_h4 = h4.add_run("4. Hardware & Implementation Details")
    r_h4.font.color.rgb = primary_color
    r_h4.font.size = Pt(16)
    r_h4.font.bold = True

    p_hw = doc.add_paragraph()
    p_hw.paragraph_format.space_after = Pt(6)
    p_hw.paragraph_format.line_spacing = 1.15
    p_hw.add_run(
        "ColdChain utilizes a single dual-core ESP32 to monitor and actuate two separate refrigerated chambers simultaneously. "
        "The complete hardware pin mapping and fail-safe logic are detailed below:"
    )

    # Pinout Table
    t_hw = doc.add_table(rows=12, cols=4)
    t_hw.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_hw.autofit = False

    hw_headers = ["Subsystem", "Peripheral Component", "ESP32 Pin", "Operational Description & Safety Logic"]
    hw_hdr_cells = t_hw.rows[0].cells
    for i, h in enumerate(hw_headers):
        hw_hdr_cells[i].text = h
        set_cell_background(hw_hdr_cells[i], "1E3A8A")
        set_cell_margins(hw_hdr_cells[i], top=100, bottom=100, left=120, right=120)
        p = hw_hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.bold = True
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(255, 255, 255)

    hw_data = [
        ("Fridge 1 (Cooler A)", "NTC Temperature Sensor", "GPIO 34 (ADC1)", "10k NTC thermistor (B=3950), Steinhart-Hart equation"),
        ("Fridge 1 (Cooler A)", "Door Switch", "GPIO 15 (Input)", "Active HIGH on door open, triggers instant MQTT report"),
        ("Fridge 1 (Cooler A)", "Compressor Relay", "GPIO 18 (Output)", "ON >= 7.0°C, OFF <= 3.0°C, mandatory 60s min off-delay"),
        ("Fridge 1 (Cooler A)", "Red Alert LED", "GPIO 19 (Output)", "Lights on > 8.0°C; Latches ON permanently on 0% Discard"),
        ("Fridge 1 (Cooler A)", "Dedicated Buzzer", "GPIO 4 (Output)", "Pulsing audible alert when door > 60s continuously open"),
        ("Fridge 2 (Cooler B)", "NTC Temperature Sensor", "GPIO 35 (ADC1)", "10k NTC thermistor (B=3950), Steinhart-Hart equation"),
        ("Fridge 2 (Cooler B)", "Door Switch", "GPIO 13 (Input)", "Active HIGH on door open, triggers instant MQTT report"),
        ("Fridge 2 (Cooler B)", "Compressor Relay", "GPIO 25 (Output)", "ON >= 7.0°C, OFF <= 3.0°C, mandatory 60s min off-delay"),
        ("Fridge 2 (Cooler B)", "Red Alert LED", "GPIO 26 (Output)", "Lights on > 8.0°C; Latches ON permanently on 0% Discard"),
        ("Fridge 2 (Cooler B)", "Dedicated Buzzer", "GPIO 27 (Output)", "Pulsing audible alert when door > 60s continuously open"),
        ("Shared Display & Power", "I2C OLED Display (SSD1306)", "GPIO 21 (SDA)\nGPIO 22 (SCL)", "128x64 display: Live Temp, Comp, Door, Batt & Safe/Warn/Breach")
    ]
    hw_widths = [Inches(1.5), Inches(1.8), Inches(1.1), Inches(2.3)]
    for r_idx, r_val in enumerate(hw_data):
        cells = t_hw.rows[r_idx + 1].cells
        for c_idx, val in enumerate(r_val):
            cells[c_idx].text = val
            set_cell_background(cells[c_idx], "F8FAFC" if r_idx % 2 == 0 else "FFFFFF")
            set_cell_margins(cells[c_idx], top=70, bottom=70, left=100, right=100)
            p = cells[c_idx].paragraphs[0]
            if c_idx == 2:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.size = Pt(8.5)
                r.font.color.rgb = text_color
                if c_idx == 0:
                    r.font.bold = True

    for row in t_hw.rows:
        for idx, width in enumerate(hw_widths):
            row.cells[idx].width = width

    # Hardware Guards
    p_hg = doc.add_paragraph()
    p_hg.paragraph_format.space_before = Pt(8)
    p_hg.paragraph_format.space_after = Pt(4)
    r_thg = p_hg.add_run("Key Hardware Fail-Safe Guards: ")
    r_thg.font.bold = True
    r_thg.font.color.rgb = secondary_color

    hguards = [
        ("Compressor Protection Delay: ", "Enforces a mandatory 60-second minimum off-time before restarting to prevent high head-pressure motor damage."),
        ("Physical Red LED Discard Latch: ", "When a vaccine reaches 0% budget, the hardware Red LED stays permanently latched ON until cleared via an HMAC-signed supervisor override (CLEAR_RED_LED_LATCH)."),
        ("Audible Door Alarm: ", "Dedicated buzzers pulse loudly if doors remain open > 60 seconds, preventing unattended thermal loss."),
        ("30+ Minute Circular Offline Buffer: ", "Caches telemetry in circular memory during Wi-Fi disconnects and flushes sequentially upon reconnection with zero duplicates.")
    ]
    for hg_title, hg_desc in hguards:
        p_hgb = doc.add_paragraph(style='List Bullet')
        p_hgb.paragraph_format.space_after = Pt(3)
        p_hgb.paragraph_format.line_spacing = 1.15
        r_hb = p_hgb.add_run(hg_title)
        r_hb.font.bold = True
        r_hb.font.color.rgb = text_color
        p_hgb.add_run(hg_desc)

    doc.add_paragraph().paragraph_format.space_after = Pt(15)

    # =========================================================================
    # SERIAL 5: Website / Software Demo Link
    # =========================================================================
    h5 = doc.add_heading(level=1)
    r_h5 = h5.add_run("5. Website / Software Demo Link")
    r_h5.font.color.rgb = primary_color
    r_h5.font.size = Pt(16)
    r_h5.font.bold = True

    p_demo = doc.add_paragraph()
    p_demo.paragraph_format.space_after = Pt(6)
    p_demo.paragraph_format.line_spacing = 1.15
    p_demo.add_run(
        "All software modules, live hardware simulations, and verification tools are live and testable via the links below:"
    )

    t_demo = doc.add_table(rows=5, cols=3)
    t_demo.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_demo.autofit = False

    d_headers = ["Software System / Component", "Live Access URL / Repository Location", "Testing & Verification Instructions"]
    d_hdr_cells = t_demo.rows[0].cells
    for i, h in enumerate(d_headers):
        d_hdr_cells[i].text = h
        set_cell_background(d_hdr_cells[i], "0E7490")
        set_cell_margins(d_hdr_cells[i], top=100, bottom=100, left=120, right=120)
        p = d_hdr_cells[i].paragraphs[0]
        for r in p.runs:
            r.font.bold = True
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(255, 255, 255)

    d_data = [
        ("Wokwi Online Hardware Simulation", "https://wokwi.com/projects/479836419904773121", "Interactive hardware simulator: test dual NTC sliders, door switches, relays, buzzers & live OLED display."),
        ("Live Web Dashboard & REST API", "http://localhost:5000\n(Or Deployed Cloud Domain)", "Real-time dual cooler cards, heat-exposure budget bars, pharmacist batch registration & 1-Click relocation."),
        ("Public Scannable QR Verification", "http://localhost:5000/?tab=publicQr&batchId=BATCH-COV-001", "Smartphone camera scannable QR verification: checks vaccine viability and heat exposure without login."),
        ("Cryptographic Ledger Integrity", "Web UI -> 'Tamper Logs & Integrity'", "Click 'Verify Integrity' to recalculate SHA-256 genesis hash chain across all audit logs in real time.")
    ]
    d_widths = [Inches(1.8), Inches(2.6), Inches(2.3)]
    for r_idx, r_val in enumerate(d_data):
        cells = t_demo.rows[r_idx + 1].cells
        for c_idx, val in enumerate(r_val):
            cells[c_idx].text = val
            set_cell_background(cells[c_idx], "F0FDFA" if r_idx % 2 == 0 else "FFFFFF")
            set_cell_margins(cells[c_idx], top=80, bottom=80, left=100, right=100)
            p = cells[c_idx].paragraphs[0]
            for r in p.runs:
                r.font.size = Pt(8.5)
                r.font.color.rgb = text_color
                if c_idx == 0:
                    r.font.bold = True
                elif c_idx == 1 and "http" in val:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(2, 132, 199)

    for row in t_demo.rows:
        for idx, width in enumerate(d_widths):
            row.cells[idx].width = width

    # Judge Credentials
    p_cred = doc.add_paragraph()
    p_cred.paragraph_format.space_before = Pt(10)
    p_cred.paragraph_format.space_after = Pt(4)
    r_tc = p_cred.add_run("Test User Accounts for Judges: ")
    r_tc.font.bold = True
    r_tc.font.color.rgb = secondary_color

    creds = [
        ("Admin: ", "Username: admin | Password: admin123 (Full system authority + Discard Red LED latch supervisor override)."),
        ("Pharmacist: ", "Username: pharmacist | Password: pharma123 (Batch registration, cooler moves, and 1-Click Proactive Relocation)."),
        ("Inspector: ", "Username: inspector | Password: inspect123 (Audit view, live dashboard, and 1-Click Verify Integrity).")
    ]
    for c_title, c_desc in creds:
        p_c = doc.add_paragraph(style='List Bullet')
        p_c.paragraph_format.space_after = Pt(3)
        p_c.paragraph_format.line_spacing = 1.15
        r_cb = p_c.add_run(c_title)
        r_cb.font.bold = True
        r_cb.font.color.rgb = text_color
        p_c.add_run(c_desc)

    # Save
    out_path = os.path.abspath("ColdChain_Concept_Submission.docx")
    doc.save(out_path)
    print(f"Document successfully created at: {out_path}")

if __name__ == "__main__":
    generate_strict_serial_document()

