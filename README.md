# ColdChain — Vaccine & Medicine Storage Monitor (BUBT Techathon)

A complete IoT Cold-Chain Monitoring System, Cryptographic Ledger, Full-Stack Web Application, and AI Prediction Engine developed according to the competition specification.

---

## 📊 System Architecture, Methodology & Decision Flow

### 1. System Architecture
![System Architecture](bubt%20hechathon/system%20architeture.jpg)

### 2. Five-Stage Methodology
![Methodology](bubt%20hechathon/methodology.jpg)

### 3. Decision Logic Flowchart
![Flowchart](bubt%20hechathon/flow_chart.jpg)

---

## 🚀 System Architecture & Completed Deliverables

### 1. ESP32 Hardware Firmware (`firmware/wokwi_main.ino`)
* **Dual-Chamber Controller:** Single ESP32 managing Cooler A (Fridge 1) and Cooler B (Fridge 2) simultaneously.
* **Sensors & Actuators:** Dual NTC temperature sensors, independent door switches, dual compressor relays, red alert LEDs, and independent buzzers.
* **OLED Screen:** Live temperatures, Safe / Warning / Breach indicators, compressor status, and power state.
* **Compressor Controller:** Auto-starts at $\ge 7^\circ\text{C}$, shuts off at $\le 3^\circ\text{C}$ with a mandatory **60-second minimum off-time** compressor protection guard.
* **Security:** Every packet is cryptographically signed with **HMAC-SHA256**, strict monotonic nonces, and timestamp validation. Downlink commands from server are also HMAC signed.
* **Offline Resilience:** Local circular storage buffer buffering over 30+ minutes of telemetry during network drops, re-syncing without duplicates upon reconnect.
* **Hardware Red LED Latch:** Latches ON permanently when batch reaches 0% (Discard), remaining active until cleared via authenticated Admin supervisor override.
* **Door Alarm:** Hardware buzzer alert when door is left unsealed for $> 60$ seconds.

### 2. Heat-Exposure Budget Engine (`backend/src/heatBudget.js`)
* Strict 60-minute lifetime allowance for temperatures $> 8^\circ\text{C}$.
* **Double penalty rate** applied for temperatures $> 12^\circ\text{C}$.
* Automatic transition:
  * Budget $< 20\% \implies$ `At Risk`
  * Budget $\le 0\% \implies$ `Discard` with persistent Red LED hardware latch, requiring an authenticated Admin supervisor override to clear.

### 3. Full-Stack Web Application & REST API (`backend/` & `frontend/`)
* **Role-Based Access Control:** Secure JWT authentication with **Admin**, **Pharmacist**, and **Inspector** roles enforced on endpoints.
* **Interactive Dashboard:** Live real-time stream of temperatures, door states, compressor duty, battery levels, and batch life bars.
* **Inventory Control:** Complete batch transfer between coolers with audit logging.
* **Public QR Code Viability Check:** No login required; scan QR code or search batch ID to view live viability, degradation minutes, and expiration.
* **Tamper-Evident Hash Chain:** Cryptographic SHA-256 block ledger with live **"Verify Integrity"** verification in 1 click.

### 4. AI Breach Prediction & Proactive Relocation (`ai_service/` & `backend/`)
* Forecasts cooler temperature **30 minutes ahead**.
* Calculates a **0–100 Compressor Health Score** based on thermal extraction gradients.
* Proactively identifies breach conditions and generates **1-Click Relocation Actions** for Pharmacists.
* Includes documentation report at [`ai_service/AI_REPORT.md`](file:///e:/BUBT%20Techathon/ai_service/AI_REPORT.md).

---

## 💻 How to Run the System

### 1. Start the Server & Web Dashboard
Run the start script or run with node:
```bash
# Option 1:
.\start_server.bat

# Option 2:
cd backend
npm start
```
Then open your browser:
```
http://localhost:5000
```

### 2. Available User Accounts:
* **Admin:** `admin` / `admin123` (Full permissions + Reset Discard latch)
* **Pharmacist:** `pharmacist` / `pharma123` (Inventory control + 1-Click Relocation)
* **Inspector:** `inspector` / `inspect123` (Audit & inspection access)

### 3. Public QR Verification:
* Visit `http://localhost:5000`, switch to **"Public QR Check"** tab, or open endpoint:
  ```
  http://localhost:5000/api/public/batch/BATCH-COV-001
  ```

