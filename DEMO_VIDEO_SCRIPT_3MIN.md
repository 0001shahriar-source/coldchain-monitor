# 3-Minute ColdChain Pitch & Video Demo Script
## Target Duration: Exactly 2:45 – 3:00 Minutes (MP4 Video for Google Classroom)

---

### Video Setup Guide:
* **Tool:** Use OBS Studio, Loom, or Windows Game Bar (`Win + G`) to record screen + microphone.
* **Tabs to keep open before recording:**
  1. Browser Tab 1: **Wokwi Simulation** (with `firmware/wokwi_main.ino` running).
  2. Browser Tab 2: **ColdChain Web App** (`http://localhost:5000`).
  3. Browser Tab 3: **Public QR Check Tab** (`http://localhost:5000/?tab=publicQr&batchId=BATCH-COV-001`).

---

### [0:00 – 0:35] Part 1: Problem Statement & ColdChain Vision
* **Screen:** Show Slide 1 or the ColdChain Web Dashboard header.
* **Voiceover:**
  > "Assalamu Alaikum. Over 50% of temperature-sensitive vaccines and life-saving biological medicines are wasted globally each year due to cold-chain failures.
  > Traditional monitors are passive—they only tell you that a vaccine was ruined *after* it has already happened.
  > To solve this, we built **ColdChain**—an intelligent, fail-safe IoT ecosystem combining dual-chamber ESP32 hardware, biochemical heat-exposure budgets, cryptographic auditability, and proactive AI breach forecasting."

---

### [0:35 – 1:25] Part 2: Dual-Chamber ESP32 Hardware & Fail-Safes (Wokwi)
* **Screen:** Switch to Wokwi Simulator tab.
* **Action:**
  1. Point to OLED displaying `F1: 4.2C [SAFE]` and `F2: 5.1C [SAFE]`.
  2. Toggle Door Switch 1 open (point out door state changes immediately).
  3. Increase NTC Temp slider above $7^\circ\text{C}$ $\rightarrow$ show Compressor Relay clicking ON.
  4. Lower Temp slider below $3^\circ\text{C}$ $\rightarrow$ show Compressor Relay shutting OFF with the 60s minimum off-delay protection.
* **Voiceover:**
  > "Here in our Wokwi simulation, a single ESP32 independently governs two medical coolers.
  > The OLED display shows live temperatures, compressor states, and Safe/Warning/Breach indicators.
  > Notice our hardware fail-safes: The compressor engages automatically at 7°C and shuts off at 3°C, strictly guarded by a 60-second minimum off-time to prevent motor damage.
  > If a door is left unsealed for more than 60 seconds, a dedicated buzzer sounds an instant audible alarm.
  > Every single telemetry packet is signed with HMAC-SHA256 and verified with monotonic nonces to prevent replay attacks.
  > Furthermore, if network connection drops, the device buffers over 30 minutes of readings in circular memory and auto-syncs without duplicates upon reconnection."

---

### [1:25 – 2:10] Part 3: Web Dashboard & Heat-Exposure Budget
* **Screen:** Switch to Web Dashboard (`http://localhost:5000`).
* **Action:**
  1. Show live Cooler A and Cooler B cards updating instantly over WebSockets.
  2. Scroll down to Batch Heat-Exposure Progress bars.
  3. Point out the $1\times$ rate for $>8^\circ\text{C}$ and $2\times$ double penalty rate for $>12^\circ\text{C}$.
  4. Highlight a batch transitioning to *At Risk* ($< 20\%$) and *Discard* ($0\%$) where the hardware Red LED latches permanently until an Admin supervisor override clears it.
* **Voiceover:**
  > "Switching to our web application, telemetry streams in real time via WebSockets.
  > Rather than using crude binary alerts, our system calculates continuous biochemical heat exposure. Batches have a strict 60-minute lifetime allowance above 8°C, with a 2x double penalty above 12°C.
  > When budget falls below 20%, it is flagged as 'At Risk'. At 0%, it enters an irreversible 'Discard' state, latching the physical hardware Red LED ON until an authenticated Admin supervisor reviews and resets it."

---

### [2:10 – 2:40] Part 4: AI Breach Prediction & 1-Click Relocation
* **Screen:** Switch to "AI Forecasting" tab on the Web Dashboard.
* **Action:**
  1. Show 30-minute ahead temperature predictions and Compressor Health Scores (0–100).
  2. Point out the AI Alert Banner recommending a batch transfer.
  3. Click the **"1-Click Confirm Relocation"** button $\rightarrow$ show instant transfer.
  4. Switch to "Security Audit" tab and click **"Verify Integrity"** $\rightarrow$ show green verified banner across the SHA-256 chain.
* **Voiceover:**
  > "Under our AI tab, our Gradient Boosting model forecasts cooler temperatures 30 minutes in advance and computes a mechanical compressor health score from 0 to 100 based on cooling gradients.
  > When an imminent breach is forecast, the system autonomously identifies safe destination fridges with spare capacity and presents a 1-Click Relocation action for pharmacists.
  > Every move, batch registration, and override is cryptographically committed to an immutable SHA-256 tamper-evident hash chain, verifiable in one click."

---

### [2:40 – 3:00] Part 5: Public QR Verification & Conclusion
* **Screen:** Switch to "Public QR Check" tab (`?tab=publicQr&batchId=BATCH-COV-001`).
* **Action:**
  1. Show the scannable QR Code and live viability report without requiring any login.
* **Voiceover:**
  > "Finally, any patient or field inspector can scan the batch's dynamic QR code with a smartphone to verify real-time viability, thermal exposure, and expiry date without logging in.
  > ColdChain bridges hardware safety, biochemical integrity, and predictive intelligence into a single production-ready solution.
  > Thank you!"

