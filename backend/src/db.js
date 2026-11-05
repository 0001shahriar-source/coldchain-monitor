const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const bcrypt = require('bcryptjs');

const DATA_FILE = path.join(__dirname, '../data/database.json');

const INITIAL_DATA = {
  users: [
    {
      id: "u1",
      username: "admin",
      passwordHash: bcrypt.hashSync("admin123", 10),
      role: "Admin"
    },
    {
      id: "u2",
      username: "pharmacist",
      passwordHash: bcrypt.hashSync("pharma123", 10),
      role: "Pharmacist"
    },
    {
      id: "u3",
      username: "inspector",
      passwordHash: bcrypt.hashSync("inspect123", 10),
      role: "Inspector"
    }
  ],
  fridges: [
    {
      id: "FRIDGE_01",
      name: "Main Vaccine Cooler A",
      temp: 4.2,
      doorOpen: false,
      compressor: false,
      power: "AC",
      battery: 100,
      lastSeen: new Date().toISOString(),
      healthScore: 94,
      predictedTemp: 4.8,
      capacity: 10,
      recentCoolingRates: [0.09, 0.085, 0.092]
    },
    {
      id: "FRIDGE_02",
      name: "Secondary Medicine Cooler B",
      temp: 5.1,
      doorOpen: false,
      compressor: true,
      power: "AC",
      battery: 98,
      lastSeen: new Date().toISOString(),
      healthScore: 88,
      predictedTemp: 5.4,
      capacity: 10,
      recentCoolingRates: [0.08, 0.078, 0.082]
    }
  ],
  batches: [
    {
      id: "BATCH-COV-001",
      name: "COVID-19 mRNA Vaccine",
      fridgeId: "FRIDGE_01",
      totalBudgetMinutes: 60,
      exposureMinutes: 8.5,
      expiryDate: "2027-04-15",
      discarded: false,
      adminReset: false,
      createdAt: new Date().toISOString()
    },
    {
      id: "BATCH-INS-002",
      name: "Human Regular Insulin",
      fridgeId: "FRIDGE_01",
      totalBudgetMinutes: 60,
      exposureMinutes: 14.0,
      expiryDate: "2026-12-30",
      discarded: false,
      adminReset: false,
      createdAt: new Date().toISOString()
    },
    {
      id: "BATCH-POL-003",
      name: "Oral Polio Vaccine (OPV)",
      fridgeId: "FRIDGE_02",
      totalBudgetMinutes: 60,
      exposureMinutes: 4.0,
      expiryDate: "2027-08-20",
      discarded: false,
      adminReset: false,
      createdAt: new Date().toISOString()
    }
  ],
  telemetryLogs: [], // Persistent historical readings for AI & audits
  auditLogs: [], // Hash chain tamper-evident logs
  alerts: []
};

let inMemoryDbCache = null;

function readDb() {
  if (inMemoryDbCache) {
    return inMemoryDbCache;
  }
  if (!fs.existsSync(DATA_FILE)) {
    inMemoryDbCache = JSON.parse(JSON.stringify(INITIAL_DATA));
    fs.writeFileSync(DATA_FILE, JSON.stringify(inMemoryDbCache, null, 2));
    return inMemoryDbCache;
  }
  try {
    const raw = fs.readFileSync(DATA_FILE, 'utf-8');
    inMemoryDbCache = JSON.parse(raw);
    return inMemoryDbCache;
  } catch (err) {
    console.error("Critical: Failed to parse database.json, retaining memory cache or creating backup instead of wiping!");
    if (inMemoryDbCache) return inMemoryDbCache;
    return JSON.parse(JSON.stringify(INITIAL_DATA));
  }
}

function writeDb(data) {
  inMemoryDbCache = data;
  const tempPath = `${DATA_FILE}.tmp`;
  try {
    fs.writeFileSync(tempPath, JSON.stringify(data, null, 2));
    fs.renameSync(tempPath, DATA_FILE);
  } catch (e) {
    fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
  }
}

// Tamper-Evident Hash Chain Appender
function appendTamperEvidentLog(action, details, actor = "system") {
  const db = readDb();
  const lastLog = db.auditLogs.length > 0 ? db.auditLogs[db.auditLogs.length - 1] : null;
  const prevHash = lastLog ? lastLog.hash : "GENESIS_COLDCHAIN_ROOT_HASH";
  const timestamp = new Date().toISOString();

  const recordPayload = JSON.stringify({
    prevHash,
    action,
    details,
    actor,
    timestamp
  });

  const hash = crypto.createHash('sha256').update(recordPayload).digest('hex');

  const newEntry = {
    index: db.auditLogs.length + 1,
    prevHash,
    action,
    details,
    actor,
    timestamp,
    hash
  };

  db.auditLogs.push(newEntry);
  writeDb(db);
  return newEntry;
}

// Verify Hash Chain Integrity
function verifyAuditLogIntegrity() {
  const db = readDb();
  let expectedPrevHash = "GENESIS_COLDCHAIN_ROOT_HASH";

  for (let i = 0; i < db.auditLogs.length; i++) {
    const entry = db.auditLogs[i];
    if (entry.prevHash !== expectedPrevHash) {
      return {
        valid: false,
        tamperedIndex: i + 1,
        reason: `Previous hash mismatch at index ${i + 1}. Expected: ${expectedPrevHash}, Found: ${entry.prevHash}`
      };
    }

    const payload = JSON.stringify({
      prevHash: entry.prevHash,
      action: entry.action,
      details: entry.details,
      actor: entry.actor,
      timestamp: entry.timestamp
    });

    const calculatedHash = crypto.createHash('sha256').update(payload).digest('hex');
    if (calculatedHash !== entry.hash) {
      return {
        valid: false,
        tamperedIndex: i + 1,
        reason: `Hash tampered at index ${i + 1}. Expected: ${calculatedHash}, Found: ${entry.hash}`
      };
    }

    expectedPrevHash = entry.hash;
  }

  return { valid: true, totalRecords: db.auditLogs.length };
}

module.exports = {
  INITIAL_DATA,
  readDb,
  writeDb,
  appendTamperEvidentLog,
  verifyAuditLogIntegrity
};
