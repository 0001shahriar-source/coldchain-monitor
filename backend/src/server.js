require('dotenv').config();
const express = require('express');
const http = require('http');
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');
const { WebSocketServer } = require('ws');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const QRCode = require('qrcode');
const mqtt = require('mqtt');

const { readDb, writeDb, appendTamperEvidentLog, verifyAuditLogIntegrity } = require('./db');
const { JWT_SECRET, authenticateToken, requireRole } = require('./auth');
const { verifyDeviceMessage } = require('./security');
const { updateHeatExposure } = require('./heatBudget');
const { dispatchIncidentAlert } = require('./notifications');

const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' }));

app.use(express.static(path.join(__dirname, '../../frontend/public')));
app.use('/src', express.static(path.join(__dirname, '../../frontend/src')));

const server = http.createServer(app);
const wss = new WebSocketServer({ server });

function broadcast(data) {
  const msg = JSON.stringify(data);
  wss.clients.forEach(client => {
    if (client.readyState === 1) {
      client.send(msg);
    }
  });
}

// ---------------- LOCAL NETWORK IP DISCOVERY (FOR SCANNABLE QR) ----------------
function getLocalNetworkIp() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }
  return 'localhost';
}

// ---------------- AI REAL INFERENCE (WITH ROLLING TELEMETRY FEATURES) ----------------
function computeRollingFeatures(db, deviceId) {
  const logs = db.telemetryLogs.filter(l => l.deviceId === deviceId);
  if (logs.length < 2) {
    return { temp_diff_1m: 0.0, temp_diff_5m: 0.0, door_open_rolling_5m: 0.0, compressor_duty_15m: 0.5 };
  }
  
  const current = logs[logs.length - 1];
  const currentTime = new Date(current.timestamp).getTime();
  
  // 1-min ago (within 60-90s)
  const log1m = logs.find(l => (currentTime - new Date(l.timestamp).getTime()) >= 60000);
  const temp_diff_1m = log1m ? Number((current.temp - log1m.temp).toFixed(3)) : 0.0;
  
  // 5-min window
  const logs5m = logs.filter(l => (currentTime - new Date(l.timestamp).getTime()) <= 300000);
  const log5m = logs.find(l => (currentTime - new Date(l.timestamp).getTime()) >= 300000);
  const temp_diff_5m = log5m ? Number((current.temp - log5m.temp).toFixed(3)) : 0.0;
  const doorOpenCount5m = logs5m.filter(l => l.doorOpen).length;
  const door_open_rolling_5m = logs5m.length > 0 ? Number((doorOpenCount5m / logs5m.length).toFixed(3)) : 0.0;
  
  // 15-min compressor duty
  const logs15m = logs.filter(l => (currentTime - new Date(l.timestamp).getTime()) <= 900000);
  const compOnCount15m = logs15m.filter(l => l.compressor).length;
  const compressor_duty_15m = logs15m.length > 0 ? Number((compOnCount15m / logs15m.length).toFixed(3)) : 0.5;

  return { temp_diff_1m, temp_diff_5m, door_open_rolling_5m, compressor_duty_15m };
}

function predictFutureTempML(temp, doorOpen, compressor, rolling, ambient = 25.0) {
  return new Promise((resolve) => {
    try {
      const cliPath = path.join(__dirname, '../../ai_service/predict_cli.py');
      const pyCmd = process.platform === 'win32' ? 'python' : 'python3';
      const py = spawn(pyCmd, [cliPath]);
      const payload = JSON.stringify({
        temp,
        doorOpen,
        compressor,
        ambient,
        ...rolling
      });
      
      let outData = '';
      py.stdout.on('data', d => { outData += d.toString(); });
      py.stderr.on('data', () => {});
      
      py.on('close', () => {
        try {
          const res = JSON.parse(outData);
          if (res.success && typeof res.predicted_temp === 'number') {
            return resolve(res.predicted_temp);
          }
        } catch (e) {}
        const fallback = Number((temp + (doorOpen ? 2.8 : 0.5) - (compressor ? 0.9 : 0)).toFixed(2));
        resolve(fallback);
      });

      py.stdin.write(payload);
      py.stdin.end();
    } catch (e) {
      resolve(Number((temp + 0.5).toFixed(2)));
    }
  });
}

function calculateCompressorHealthScore(coolingRates) {
  if (!coolingRates || coolingRates.length === 0) return 92;
  const avg = coolingRates.reduce((a, b) => a + b, 0) / coolingRates.length;
  const score = Math.max(0, Math.min(100, Math.round(((avg - 0.02) / (0.10 - 0.02)) * 100)));
  return score;
}

// ---------------- MQTT CLIENT & DOWNLINK DISPATCH ----------------
const MQTT_BROKER = process.env.MQTT_BROKER_URL || 'mqtt://broker.hivemq.com:1883';
const mqttClient = mqtt.connect(MQTT_BROKER);

// In-memory mutex/queue to serialize telemetry and database transactions
let dbMutexPromise = Promise.resolve();
function withDbMutex(fn) {
  const next = dbMutexPromise.then(fn, fn);
  dbMutexPromise = next;
  return next;
}

// MQTT Downlink Command Publisher with HMAC-SHA256 signature
function sendSignedDeviceCommand(topic, payloadObj) {
  const rawPayload = JSON.stringify(payloadObj);
  const secretKey = process.env.HMAC_SECRET_FRIDGE_01 || 'KEY_COLDCHAIN_FRIDGE_01_SECURE_9876';
  const signature = crypto.createHmac('sha256', secretKey).update(rawPayload).digest('hex');
  const signedEnvelope = JSON.stringify({
    data: payloadObj,
    signature: signature
  });
  mqttClient.publish(topic, signedEnvelope);
  console.log(`[MQTT Command] Published signed command to ${topic}:`, payloadObj.command);
}

mqttClient.on('connect', () => {
  console.log(`[MQTT Bridge] Connected to ${MQTT_BROKER}`);
  mqttClient.subscribe('coldchain/+/telemetry', (err) => {
    if (!err) console.log('[MQTT Bridge] Subscribed to coldchain/+/telemetry');
  });
});

mqttClient.on('message', async (topic, message) => {
  try {
    const parsed = JSON.parse(message.toString());
    const { data, signature } = parsed;
    if (!data || !signature) return;

    await processTelemetryPacket(data, signature, 'mqtt');
  } catch (err) {
    console.error('[MQTT Bridge] Parse Error:', err.message);
  }
});

// Central Telemetry Processor wrapped with In-Memory Mutex to prevent race conditions
async function processTelemetryPacket(data, signature, source = 'http') {
  return withDbMutex(async () => {
    const rawString = typeof data === 'string' ? data : JSON.stringify(data);
    const payload = typeof data === 'string' ? JSON.parse(data) : data;
    const deviceId = payload.deviceId || 'FRIDGE_01';

    // 1. Cryptographic Verification
    const sec = verifyDeviceMessage(rawString, signature, deviceId, payload.timestamp, payload.nonce);
    if (!sec.valid) {
      appendTamperEvidentLog('SECURITY_REJECT', `Rejected message for ${deviceId}: ${sec.error}`, deviceId);
      return { success: false, error: sec.error, status: 403 };
    }

    // 2. Load Single Shared DB Instance
    const db = readDb();
    let fridge = db.fridges.find(f => f.id === deviceId);
    if (!fridge) {
      fridge = {
        id: deviceId,
        name: deviceId === 'FRIDGE_01' ? 'Main Vaccine Cooler A' : `Secondary Medicine Cooler ${deviceId}`,
        temp: payload.temp,
        doorOpen: payload.doorOpen,
        compressor: payload.compressor,
        power: payload.power,
        battery: payload.battery,
        lastSeen: new Date().toISOString(),
        healthScore: 92,
        predictedTemp: payload.temp,
        capacity: 10,
        recentCoolingRates: [0.088, 0.091],
        lastCompTemp: payload.temp,
        lastCompTime: Date.now()
      };
      db.fridges.push(fridge);
    } else {
      if (payload.compressor && fridge.lastCompTime) {
        const elapsedMinutes = (Date.now() - fridge.lastCompTime) / 60000;
        if (elapsedMinutes >= 0.1 && fridge.temp > payload.temp) {
          const rate = (fridge.temp - payload.temp) / elapsedMinutes;
          if (!fridge.recentCoolingRates) fridge.recentCoolingRates = [];
          fridge.recentCoolingRates.push(Number(rate.toFixed(3)));
          if (fridge.recentCoolingRates.length > 8) fridge.recentCoolingRates.shift();
          fridge.healthScore = calculateCompressorHealthScore(fridge.recentCoolingRates);
        }
      }
      fridge.lastCompTime = Date.now();
      fridge.temp = payload.temp;
      fridge.doorOpen = payload.doorOpen;
      fridge.compressor = payload.compressor;
      fridge.power = payload.power;
      fridge.battery = payload.battery;
      fridge.lastSeen = new Date().toISOString();
    }

    // 3. Compute Real Historical Rolling Features
    const rolling = computeRollingFeatures(db, fridge.id);
    const predicted = await predictFutureTempML(fridge.temp, fridge.doorOpen, fridge.compressor, rolling);
    fridge.predictedTemp = predicted;

    // 4. Update Heat Exposure (5s = 5/60 min)
    updateHeatExposure(db, fridge.id, fridge.temp, 5 / 60);

    // Check if any batch in this fridge is discarded (0% budget left)
    const hasDiscardedBatch = db.batches.some(b => b.fridgeId === fridge.id && b.discarded);
    if (hasDiscardedBatch) {
      // Send signed MQTT downlink command to latch hardware Red LED on the device
      sendSignedDeviceCommand('coldchain/commands', {
        command: 'SET_RED_LED_LATCH',
        targetFridge: fridge.id,
        timestamp: Date.now()
      });
    }

    // 5. Store historical telemetry reading
    db.telemetryLogs.push({
      deviceId: fridge.id,
      temp: fridge.temp,
      doorOpen: fridge.doorOpen,
      compressor: fridge.compressor,
      power: fridge.power,
      predictedTemp: fridge.predictedTemp,
      timestamp: new Date().toISOString()
    });
    if (db.telemetryLogs.length > 5000) {
      db.telemetryLogs.splice(0, 1000);
    }

    // 6. Alert on Door Open > 60s
    if (payload.doorOpenTimeSec > 60) {
      const alertId = `${fridge.id}_door_${Math.floor(Date.now() / 60000)}`;
      const alreadyAlerted = db.alerts.some(a => a.id === alertId);
      if (!alreadyAlerted) {
        const alertMsg = `Door on ${fridge.name} (${fridge.id}) has been open for > 60 seconds! Current Temp: ${fridge.temp}°C.`;
        db.alerts.push({
          id: alertId,
          type: 'DOOR_ALARM',
          message: alertMsg,
          timestamp: new Date().toISOString()
        });
        dispatchIncidentAlert(`Door Breach: ${fridge.name}`, alertMsg);
      }
    }

    writeDb(db);
    broadcast({ type: 'TELEMETRY_UPDATE', fridge, fridges: db.fridges });
    return { success: true };
  });
}

// ---------------- AUTHENTICATION ----------------
app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body;
  const db = readDb();
  const user = db.users.find(u => u.username === username);

  if (!user || !bcrypt.compareSync(password, user.passwordHash)) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  const token = jwt.sign(
    { id: user.id, username: user.username, role: user.role },
    JWT_SECRET,
    { expiresIn: '12h' }
  );

  appendTamperEvidentLog('USER_LOGIN', `User ${username} logged in as ${user.role}`, username);
  res.json({ token, role: user.role, username: user.username });
});

// ---------------- PUBLIC QR CHECK (LIVE SCANNABLE URL LINK) ----------------
app.get('/api/public/batch/:batchId', async (req, res) => {
  const { batchId } = req.params;
  const db = readDb();
  const batch = db.batches.find(b => b.id === batchId);

  if (!batch) {
    return res.status(404).json({ error: 'Batch not found' });
  }

  const remaining = Math.max(0, batch.totalBudgetMinutes - batch.exposureMinutes);
  const remainingPct = (remaining / batch.totalBudgetMinutes) * 100;
  let status = 'Safe';
  
  // Check calendar expiration
  const isExpired = batch.expiryDate && new Date(batch.expiryDate) < new Date();
  if (isExpired) {
    status = 'Expired';
  } else if (batch.discarded || remaining <= 0) {
    status = 'Discard';
  } else if (remainingPct < 20) {
    status = 'At Risk';
  }

  // Construct real scannable HTTP URL for smartphone camera scanning
  const host = req.get('host') || `${getLocalNetworkIp()}:${PORT}`;
  const verificationUrl = `http://${host}/?tab=publicQr&batchId=${batch.id}`;

  const qrDataUrl = await QRCode.toDataURL(verificationUrl, {
    errorCorrectionLevel: 'H',
    margin: 2,
    width: 250
  });

  res.json({
    id: batch.id,
    name: batch.name,
    fridgeId: batch.fridgeId,
    status,
    remainingBudgetMinutes: Number(remaining.toFixed(2)),
    exposureMinutes: Number(batch.exposureMinutes.toFixed(2)),
    expiryDate: batch.expiryDate,
    verificationUrl,
    qrCode: qrDataUrl
  });
});

// ---------------- DASHBOARD & TELEMETRY ----------------
app.get('/api/dashboard', authenticateToken, (req, res) => {
  const db = readDb();
  const batches = db.batches.map(b => {
    const remaining = Math.max(0, b.totalBudgetMinutes - b.exposureMinutes);
    const pct = (remaining / b.totalBudgetMinutes) * 100;
    let status = 'Safe';
    if (b.discarded || remaining <= 0) status = 'Discard';
    else if (pct < 20) status = 'At Risk';
    return {
      ...b,
      remainingMinutes: Number(remaining.toFixed(2)),
      remainingPct: Number(pct.toFixed(1)),
      status
    };
  });

  res.json({
    fridges: db.fridges,
    batches,
    alerts: db.alerts.slice(-10).reverse()
  });
});

app.post('/api/telemetry/report', async (req, res) => {
  const { data, signature } = req.body;
  if (!data || !signature) {
    return res.status(400).json({ error: 'Missing data or HMAC signature' });
  }

  const result = await processTelemetryPacket(data, signature, 'http');
  if (!result.success) {
    return res.status(result.status || 400).json({ error: result.error });
  }
  res.json({ success: true });
});

// ---------------- OFFLINE SYNC (PROTECTED BY HMAC - ZERO JWT BLOCKER) ----------------
app.post('/api/telemetry/sync-offline', (req, res) => {
  const { logs } = req.body;
  if (!Array.isArray(logs)) {
    return res.status(400).json({ error: 'Logs array expected' });
  }

  const db = readDb();
  let accepted = 0;
  let rejected = 0;

  const verifiedItems = [];
  for (const item of logs) {
    if (!item.data || !item.signature) {
      rejected++;
      continue;
    }
    const rawString = typeof item.data === 'string' ? item.data : JSON.stringify(item.data);
    const payload = typeof item.data === 'string' ? JSON.parse(item.data) : item.data;
    
    // Authenticate via device cryptographic HMAC
    const sec = verifyDeviceMessage(rawString, item.signature, payload.deviceId, payload.timestamp, payload.nonce);
    if (!sec.valid) {
      rejected++;
      continue;
    }
    verifiedItems.push(payload);
  }

  // Sort chronologically
  verifiedItems.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));

  for (const p of verifiedItems) {
    updateHeatExposure(db, p.deviceId, p.temp, 5 / 60);
    // Also update fridge current readings to latest state
    let f = db.fridges.find(item => item.id === p.deviceId);
    if (f) {
      f.temp = p.temp;
      f.doorOpen = p.doorOpen;
      f.compressor = p.compressor;
      f.power = p.power;
      f.battery = p.battery;
      f.lastSeen = new Date().toISOString();
    }
    accepted++;
  }

  writeDb(db);
  appendTamperEvidentLog('OFFLINE_SYNC', `Synced ${accepted} verified offline readings via device HMAC (Rejected: ${rejected})`, 'esp32_device');
  broadcast({ type: 'INVENTORY_UPDATE' });

  res.json({ success: true, processed: accepted, rejected });
});

// ---------------- INVENTORY MANAGEMENT ----------------
app.post('/api/inventory/batch', authenticateToken, requireRole(['Admin', 'Pharmacist']), (req, res) => {
  const { id, name, fridgeId, expiryDate } = req.body;
  if (!name || !fridgeId || !expiryDate) {
    return res.status(400).json({ error: 'Name, cooler, and expiry date are required' });
  }
  const db = readDb();

  const newBatch = {
    id: id || `BATCH-${Date.now().toString().slice(-4)}`,
    name,
    fridgeId,
    totalBudgetMinutes: 60, // Fixed 60-minute lifetime allowance according to competition specification
    exposureMinutes: 0,
    expiryDate,
    discarded: false,
    adminReset: false,
    createdAt: new Date().toISOString()
  };

  db.batches.push(newBatch);
  writeDb(db);
  appendTamperEvidentLog('BATCH_CREATE', `Added vaccine batch ${newBatch.id} to cooler ${fridgeId}`, req.user.username);
  broadcast({ type: 'INVENTORY_UPDATE' });

  res.json(newBatch);
});

app.post('/api/inventory/move', authenticateToken, requireRole(['Admin', 'Pharmacist']), (req, res) => {
  const { batchId, targetFridgeId } = req.body;
  const db = readDb();
  const batch = db.batches.find(b => b.id === batchId);

  if (!batch) return res.status(404).json({ error: 'Batch not found' });

  const targetFridge = db.fridges.find(f => f.id === targetFridgeId);
  if (!targetFridge) return res.status(404).json({ error: 'Target fridge not found' });

  const currentOccupancy = db.batches.filter(b => b.fridgeId === targetFridgeId).length;
  const maxCap = targetFridge.capacity || 10;
  if (currentOccupancy >= maxCap) {
    return res.status(400).json({ error: `Target cooler ${targetFridge.name} is at maximum capacity (${maxCap} batches)` });
  }

  const oldFridge = batch.fridgeId;
  batch.fridgeId = targetFridgeId;
  writeDb(db);

  appendTamperEvidentLog('BATCH_MOVE', `Moved batch ${batchId} from ${oldFridge} to ${targetFridgeId}`, req.user.username);
  broadcast({ type: 'INVENTORY_UPDATE' });

  res.json({ success: true, batch });
});

// Admin reset for discarded batch + MQTT Downlink Command to clear hardware Red LED latch
app.post('/api/inventory/reset-discard', authenticateToken, requireRole(['Admin']), (req, res) => {
  const { batchId } = req.body;
  const db = readDb();
  const batch = db.batches.find(b => b.id === batchId);

  if (!batch) return res.status(404).json({ error: 'Batch not found' });

  batch.adminReset = true;
  batch.discarded = false;
  batch.totalBudgetMinutes = 60;
  batch.exposureMinutes = 0;
  writeDb(db);

  // Send hardware downlink command via MQTT signed with HMAC
  sendSignedDeviceCommand('coldchain/commands', {
    command: 'CLEAR_RED_LED_LATCH',
    batchId: batchId,
    targetFridge: batch.fridgeId,
    timestamp: Date.now()
  });

  appendTamperEvidentLog('ADMIN_RESET', `Admin supervisor cleared discard latch on batch ${batchId}. Downlink dispatched.`, req.user.username);
  broadcast({ type: 'INVENTORY_UPDATE' });

  res.json({ success: true, batch });
});

// ---------------- TAMPER-EVIDENT LOGS & INTEGRITY ----------------
app.get('/api/logs/audit', authenticateToken, (req, res) => {
  const db = readDb();
  res.json(db.auditLogs);
});

app.get('/api/logs/verify-integrity', authenticateToken, (req, res) => {
  const result = verifyAuditLogIntegrity();
  res.json(result);
});

// ---------------- AI PREDICTION & RELOCATION ----------------
app.get('/api/ai/recommendations', authenticateToken, (req, res) => {
  const db = readDb();
  
  const unsafe = db.fridges.filter(f => (f.predictedTemp || f.temp) > 8.0 || (f.healthScore || 100) < 50);
  const safeCandidates = db.fridges.filter(f => (f.predictedTemp || f.temp) <= 6.0 && (f.healthScore || 100) >= 70);

  const recommendations = [];
  if (unsafe.length > 0 && safeCandidates.length > 0) {
    unsafe.forEach(uf => {
      const batchesInUnit = db.batches
        .filter(b => b.fridgeId === uf.id && !b.discarded)
        .sort((a, b) => (b.exposureMinutes / b.totalBudgetMinutes) - (a.exposureMinutes / a.totalBudgetMinutes));

      batchesInUnit.forEach(b => {
        const target = safeCandidates.find(sf => {
          const count = db.batches.filter(item => item.fridgeId === sf.id).length;
          return count < (sf.capacity || 10);
        });

        if (target) {
          recommendations.push({
            batchId: b.id,
            batchName: b.name,
            sourceFridgeId: uf.id,
            sourceFridgeName: uf.name,
            targetFridgeId: target.id,
            targetFridgeName: target.name,
            exposurePct: Number(((b.exposureMinutes / b.totalBudgetMinutes) * 100).toFixed(1)),
            reason: `30-Min AI Forecast Breach: ${uf.predictedTemp}°C (Compressor Health: ${uf.healthScore}%)`
          });
        }
      });
    });
  }

  res.json({
    predictions: db.fridges,
    recommendations
  });
});

const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  console.log(`ColdChain Enterprise Server listening on port ${PORT}`);
  console.log(`Public Verification URL Host: http://${getLocalNetworkIp()}:${PORT}`);
});
