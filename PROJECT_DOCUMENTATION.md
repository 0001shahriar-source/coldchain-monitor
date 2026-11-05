# ColdChain — Vaccine & Medicine Storage Monitor
## BUBT Techathon 2026 — Project Documentation & Concept Submission Report

---

### Executive Overview & Metadata

* **Track / Category:** IoT, Embedded Systems, Full-Stack & Applied AI
* **Project Name:** ColdChain — Smart Dual-Chamber Vaccine & Medicine Storage Monitor
* **Core Technologies:** ESP32 (C/C++), MQTT 3.1.1, Node.js / Express, WebSockets, Python (`scikit-learn`), HMAC-SHA256, SHA-256 Ledger
* **Wokwi Simulation:** Fully unified dual-chamber controller (`firmware/wokwi_main.ino`)
* **Presentation Slides:** 14 Slides widescreen deck (`ColdChain_Techathon.pptx`)

---

## 1. Project Overview & Concept

### 1.1 Problem Statement & Background
According to the World Health Organization (WHO), over **50% of temperature-sensitive vaccines and biological medicines** are wasted globally each year due to cold-chain failures (freezing below $2^\circ\text{C}$ or overheating above $8^\circ\text{C}$).
Traditional cold-chain monitors suffer from critical systemic flaws:
1. **Passive / Post-Mortem Logging:** Traditional USB loggers only reveal spoilage *after* vaccines are already ruined, with zero early intervention.
2. **Binary Threshold Blindness:** Fixed temperature alerts ignore biochemical cumulative thermal stress. Exposing a vaccine to $13^\circ\text{C}$ degrades it twice as fast as $9^\circ\text{C}$.
3. **Audit Vulnerability:** Centralized databases are susceptible to accidental data overwrites or intentional falsification of compliance records.
4. **Mechanical Unawareness:** Power loss and compressor mechanical degradation often strike without warning.

### 1.2 The ColdChain Solution (Four Strategic Pillars)
ColdChain delivers a comprehensive, fail-safe ecosystem designed for medical cold storage:
* **Resilient Dual-Chamber IoT Node:** A single ESP32 independently governs two refrigerated chambers with hardware fail-safes (60s minimum compressor off-guard, 60s unsealed door buzzers, and local offline circular flash memory).
* **Biochemical Heat-Exposure Budget:** A continuous 60-minute lifetime allowance above $8^\circ\text{C}$, penalizing severe excursions ($> 12^\circ\text{C}$) at a double rate ($2\times$). Batches transition automatically to *At Risk* ($< 20\%$) and *Discard* ($0\%$) with persistent hardware Red LED latching.
* **Cryptographic Trust & Auditability:** Every telemetry packet is authenticated via device-specific **HMAC-SHA256** and monotonic replay protection. Every inventory transition, supervisor override, and offline sync is appended to an immutable **SHA-256 Tamper-Evident Hash Chain**.
* **Proactive AI Forecasting & 1-Click Relocation:** A Gradient Boosting Regressor forecasts temperatures **30 minutes ahead** and monitors compressor mechanical health (0–100 score). Imminent breaches trigger an automated, capacity-aware **1-Click Relocation** workflow for pharmacists.

```
+-----------------------------------------------------------------------------------+
|                           COLDCHAIN SYSTEM ARCHITECTURE                           |
+-----------------------------------------------------------------------------------+
|  [ESP32 Hardware Node]                                                            |
|  - Fridge 1: NTC (GPIO 34), Door (GPIO 15), Relay (GPIO 18), LED (19), Buzz (4)   |
|  - Fridge 2: NTC (GPIO 35), Door (GPIO 13), Relay (GPIO 25), LED (26), Buzz (27)  |
|  - OLED Display: Live Temp, Comp State, Power & Safe/Warning/Breach Badges        |
|  - Security: HMAC-SHA256 Signed Packets + Monotonic Nonce                         |
|  - Storage: Circular Buffer (Offline Mode >= 30 mins)                             |
+------------------------------------------+----------------------------------------+
                                           | MQTT 3.1.1 (broker.hivemq.com)
                                           v
+-----------------------------------------------------------------------------------+
|  [Central Enterprise Server & Backend]                                            |
|  - Telemetry Ingestion with Sequential Mutex (Zero Race Condition / Overwrites)    |
|  - Cryptographic Verifier (HMAC-SHA256, Anti-Replay Guard, Monotonic Nonces)     |
|  - Heat-Exposure Engine: 60m Budget, 1x/2x Penalty, 0% Discard State             |
|  - SHA-256 Tamper-Evident Hash Chain (Genesis to Current Ledger)                 |
|  - RBAC Security (Admin, Pharmacist, Inspector via JWT & bcrypt)                 |
|  - Downlink Command Dispatcher (Signed CLEAR_RED_LED_LATCH via MQTT)             |
+-------------------+-----------------------------------+---------------------------+
                    | WebSocket / REST                  | Child Process Pipeline
                    v                                   v
+-----------------------------------+   +-------------------------------------------+
|  [Full-Stack Web Interface]       |   |  [AI Forecasting & Health Engine]         |
|  - Live Cooler Telemetry Cards    |   |  - 30-Minute Temperature Prediction       |
|  - Batch Heat Budget Progress     |   |  - Rolling Feature Extraction (dT/dt)     |
|  - Pharmacist Batch Registration  |   |  - Compressor Health Scoring (0-100)      |
|  - 1-Click Tamper Verification    |   |  - Capacity-Aware Relocation Engine       |
|  - Public Scannable QR Codes      |   +-------------------------------------------+
+-----------------------------------+
```

---

## 2. Hardware Implementation & Fail-Safe Details

### 2.1 Microcontroller & Pin Mapping
A single ESP32 microcontroller manages both refrigerated chambers concurrently without resource contention:

| Subsystem | Component / Function | GPIO Pin | Operational Specification |
| :--- | :--- | :--- | :--- |
| **Fridge 1** | Analog NTC Temperature Probe | `GPIO 34` | Steinhart-Hart equation ($\beta = 3950$), 12-bit ADC |
| **Fridge 1** | Door Contact Switch | `GPIO 15` | Digital Input, Instant MQTT report on state change |
| **Fridge 1** | Compressor Relay | `GPIO 18` | Auto-ON $\ge 7^\circ\text{C}$, Auto-OFF $\le 3^\circ\text{C}$ |
| **Fridge 1** | Breach Red Alert LED | `GPIO 19` | Lights on breach; Latches permanently on $0\%$ Discard |
| **Fridge 1** | Door Alarm Buzzer | `GPIO 4` | Sounds oscillating alert when door $> 60\text{s}$ unsealed |
| **Fridge 2** | Analog NTC Temperature Probe | `GPIO 35` | Steinhart-Hart equation ($\beta = 3950$), 12-bit ADC |
| **Fridge 2** | Door Contact Switch | `GPIO 13` | Digital Input, Instant MQTT report on state change |
| **Fridge 2** | Compressor Relay | `GPIO 25` | Auto-ON $\ge 7^\circ\text{C}$, Auto-OFF $\le 3^\circ\text{C}$ |
| **Fridge 2** | Breach Red Alert LED | `GPIO 26` | Lights on breach; Latches permanently on $0\%$ Discard |
| **Fridge 2** | Door Alarm Buzzer | `GPIO 27` | Sounds oscillating alert when door $> 60\text{s}$ unsealed |
| **Display** | I2C OLED Display (SSD1306) | `SDA: 21, SCL: 22` | $128\times64$ resolution, direct bitmapped driver |
| **Power** | AC / Battery Fail Simulator | `GPIO 23` | Active LOW drops to $75\%$ battery reserve |

### 2.2 Built-In Fail-Safe Mechanisms
1. **Compressor Thermal Protection Guard:** Shuts down cooling at $\le 3^\circ\text{C}$ and enforces a mandatory **60-second minimum off-delay** before restarting, protecting the motor against high head-pressure damage.
2. **Audible Door Breach Alarm:** If either door is left unsealed for $> 60$ seconds, the dedicated piezo buzzer pulses continuously until closed.
3. **Hardware Red LED Latch:** When a batch's cumulative heat budget hits $0\%$, the hardware Red LED is latched ON. It cannot be cleared locally; it strictly requires a cryptographically signed supervisor command (`CLEAR_RED_LED_LATCH`) from the cloud.
4. **Resilient Offline FIFO Buffer:** During Wi-Fi or broker downtime, readings are saved to circular memory. Upon reconnecting, the buffer flushes in exact chronological order without duplicates.

---

## 3. Software Architecture & Security Implementation

### 3.1 Device Authentication & Replay Attack Defense
* **HMAC-SHA256 Signatures:** Every telemetry envelope is signed using a secret device key (`KEY_COLDCHAIN_FRIDGE_01_SECURE_9876`).
* **Strict Monotonic Nonces:** The server enforces $N_{\text{received}} > N_{\text{last}}$ per device. Any packet with an old, duplicate, or replayed nonce is rejected and logged to the security audit trail.
* **Signed Downlink Commands:** Commands dispatched to devices (e.g. clearing the red LED latch) are also signed with HMAC-SHA256, preventing unauthorized actors on public brokers from injecting rogue overrides.

### 3.2 Heat-Exposure Budget Engine
Instead of basic threshold alerts, ColdChain implements a biochemical degradation model:
$$\text{Effective Degradation} = \Delta t \times \begin{cases} 1.0 & \text{if } 8^\circ\text{C} < T \le 12^\circ\text{C} \\ 2.0 & \text{if } T > 12^\circ\text{C} \end{cases}$$
* **Remaining Budget $< 20\%$:** Status escalates to **At Risk**.
* **Remaining Budget $\le 0\%$:** Status switches irreversibly to **Discard**, logging a `BATCH_DISCARDED` cryptographic audit record.

### 3.3 Cryptographic Tamper-Evident Hash Chain
Every critical operation is recorded in an immutable ledger:
$$\text{Hash}_i = \text{SHA-256}\Big(\text{Hash}_{i-1} \,\|\, \text{Action} \,\|\, \text{Details} \,\|\, \text{Actor} \,\|\, \text{Timestamp}\Big)$$
The Web UI provides a **1-Click "Verify Integrity"** button that re-calculates the complete chain from the genesis block (`GENESIS_COLDCHAIN_ROOT_HASH`). Any alteration or truncation is immediately flagged with the exact tampered index.

### 3.4 Role-Based Access Control (RBAC)
* **Admin:** Full system permissions + Discard Latch Reset override.
* **Pharmacist:** Inventory management, Batch registration, and 1-Click Proactive Relocation execution.
* **Inspector:** Read-only access to live telemetry, audit ledger, and integrity verification tools.

---

## 4. Machine Learning & Predictive Relocation

### 4.1 Thermodynamic Physics Simulation & Model Training
The model was trained on an 8,640-step (24 hours at 10s intervals) thermodynamic simulation incorporating realistic hysteresis ($3^\circ\text{C}-7^\circ\text{C}$), conduction leakage, user door openings, and simulated power outages.

* **Algorithm:** Gradient Boosting Regressor (`n_estimators=150`, `max_depth=5`, `learning_rate=0.06`).
* **Features Extracted:** Instantaneous temperature, door state, compressor state, ambient temperature, $1\text{m}$ / $5\text{m}$ / $15\text{m}$ temperature deltas ($dT/dt$), rolling door opening ratios, and $15\text{m}$ compressor duty cycle.
* **Empirical Validation (80/20 Chronological Split):**
  * **Mean Absolute Error (MAE):** **$0.914^\circ\text{C}$** across a 30-minute horizon.
  * **Coefficient of Determination ($R^2$):** **$0.683$**.
  * **Breach Precision ($> 8^\circ\text{C}$):** **$93.4\%$**.
  * **Breach Recall ($> 8^\circ\text{C}$):** **$73.9\%$**.

### 4.2 Compressor Degradation Health Scoring
Mechanical cooling efficiency is tracked deterministically:
$$\text{Health Score} = \text{clip}\left(\frac{\overline{\Delta T_{\text{cool}}} - 0.02}{0.10 - 0.02} \times 100,\, 0,\, 100\right)$$
Units scoring below 50 are automatically marked for proactive relocation.

### 4.3 Automated 1-Click Relocation Engine
When an imminent breach is forecast, ColdChain calculates viable destinations by checking:
1. Destination cooler predicted temperature $\le 6.0^\circ\text{C}$ and health score $\ge 70$.
2. Destination capacity constraints (maximum batches per cooler).
3. Prioritizes batches with the lowest remaining budget ($< 20\%$ first).
Pharmacists can execute the move in **1 click**, instantly updating device routing and logging the transfer to the SHA-256 chain.

---

## 5. Submission Links & Deliverables Directory

| Deliverable | Location / Link | Description |
| :--- | :--- | :--- |
| **Presentation Deck** | [`ColdChain_Techathon.pptx`](file:///e:/BUBT%20Techathon/ColdChain_Techathon.pptx) | Complete 14-slide widescreen presentation deck |
| **Firmware Code** | [`firmware/wokwi_main.ino`](file:///e:/BUBT%20Techathon/firmware/wokwi_main.ino) | Unified dual-fridge ESP32 firmware with OLED, HMAC & Latch |
| **Circuit Diagram** | [`firmware/diagram.json`](file:///e:/BUBT%20Techathon/firmware/diagram.json) | Complete dual-fridge Wokwi wiring and component schema |
| **Web Dashboard** | `http://localhost:5000` | Full-stack interface (RBAC, Hash Chain, Public QR) |
| **AI Model & Metrics** | [`ai_service/`](file:///e:/BUBT%20Techathon/ai_service/) | `predict.py`, `predict_cli.py`, `model_metrics.json`, `AI_REPORT.md` |
| **GitHub Repository** | `https://github.com/0001shahriar-source/coldchain-monitor` | Complete production source code (Backend, Frontend, Firmware, AI) |
| **Wokwi Online Demo Link** | `https://wokwi.com/projects/479836419904773121` | Interactive dual-chamber hardware simulation with OLED, NTCs & buzzers |
| **Demo Pitch Video (MP4)** | `https://drive.google.com/` *(Paste your Drive/YouTube link)* | 3-Minute walkthrough of hardware, software & AI |

---

## 6. How to Run the System for Evaluation

1. **Install Dependencies & Start Backend:**
   ```powershell
   cd backend
   npm install
   npm start
   ```
   Open browser at: `http://localhost:5000`

2. **Simulate Hardware on Wokwi:**
   - Open Wokwi ESP32 Simulator.
   - Load `firmware/diagram.json` and `firmware/wokwi_main.ino`.
   - Click **Start Simulation**. Both coolers will connect to Wi-Fi and stream signed telemetry over MQTT.

3. **Verify Public QR Code:**
   - Visit `http://localhost:5000/?tab=publicQr&batchId=BATCH-COV-001` to test the public patient/inspector verification view without login.

