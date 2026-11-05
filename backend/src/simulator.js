const crypto = require('crypto');
const http = require('http');

const SECRET_KEY = "SUPER_SECRET_HMAC_KEY_12345";
const SERVER_URL = "http://localhost:5000/api/telemetry/report";

let fridge1 = {
  deviceId: "FRIDGE_01",
  temp: 4.5,
  doorOpen: false,
  compressor: false,
  power: "AC",
  battery: 100,
  doorOpenSeconds: 0
};

let fridge2 = {
  deviceId: "FRIDGE_02",
  temp: 6.8,
  doorOpen: false,
  compressor: true,
  power: "AC",
  battery: 98,
  doorOpenSeconds: 0
};

let nonce = 1000;

function sendTelemetry(state) {
  nonce++;
  const payload = {
    deviceId: state.deviceId,
    temp: Number(state.temp.toFixed(2)),
    doorOpen: state.doorOpen,
    compressor: state.compressor,
    power: state.power,
    battery: state.battery,
    timestamp: Date.now(),
    nonce: nonce,
    doorOpenTimeSec: state.doorOpenSeconds
  };

  const raw = JSON.stringify(payload);
  const signature = crypto.createHmac('sha256', SECRET_KEY).update(raw).digest('hex');

  const postData = JSON.stringify({
    data: payload,
    signature: signature
  });

  const req = http.request(SERVER_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData)
    }
  }, (res) => {
    // success
  });

  req.on('error', (e) => {
    // console.error(`Error sending telemetry: ${e.message}`);
  });

  req.write(postData);
  req.end();
}

// Simulation loop (runs every 5 seconds)
setInterval(() => {
  // Fridge 1 logic: ON at 7C, OFF at 3C
  if (fridge1.compressor) {
    fridge1.temp -= 0.3;
    if (fridge1.temp <= 3.0) fridge1.compressor = false;
  } else {
    fridge1.temp += 0.2;
    if (fridge1.temp >= 7.0) fridge1.compressor = true;
  }

  // Fridge 2 slight drift
  if (fridge2.compressor) {
    fridge2.temp -= 0.25;
    if (fridge2.temp <= 3.0) fridge2.compressor = false;
  } else {
    fridge2.temp += 0.3;
    if (fridge2.temp >= 7.0) fridge2.compressor = true;
  }

  sendTelemetry(fridge1);
  sendTelemetry(fridge2);
}, 5000);

console.log("ESP32 IoT Node Simulator running... Sending telemetry every 5s.");

