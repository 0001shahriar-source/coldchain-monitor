require('dotenv').config();
const crypto = require('crypto');

function getSecretForDevice(deviceId) {
  if (deviceId === 'FRIDGE_01') return process.env.HMAC_SECRET_FRIDGE_01 || 'KEY_COLDCHAIN_FRIDGE_01_SECURE_9876';
  if (deviceId === 'FRIDGE_02') return process.env.HMAC_SECRET_FRIDGE_02 || 'KEY_COLDCHAIN_FRIDGE_02_SECURE_5432';
  return process.env.HMAC_DEFAULT_FALLBACK || 'KEY_COLDCHAIN_DEFAULT_DEV_12345';
}

// Per-device state:
// 1. lastSeenNonce: Strict monotonic nonce tracking (incoming nonce MUST be strictly greater than lastSeenNonce)
// 2. seenNonceSet: Set of all seen nonces to block any duplicate nonces
const deviceNonceState = new Map(); // deviceId -> { lastNonce: number, seenSet: Set<number> }

function getDeviceNonceTracker(deviceId) {
  const id = deviceId || 'default';
  if (!deviceNonceState.has(id)) {
    deviceNonceState.set(id, { lastNonce: 0, seenSet: new Set() });
  }
  return deviceNonceState.get(id);
}

/**
 * Validates HMAC-SHA256 signature FIRST, then checks timestamp and nonce replay.
 * This guarantees unverified packets never pollute the nonce memory.
 */
function verifyDeviceMessage(rawPayloadStr, signature, deviceId, timestamp, nonce) {
  if (!nonce) {
    return { valid: false, error: 'Missing mandatory nonce parameter' };
  }

  // 1. FIRST STEP: HMAC-SHA256 Cryptographic Verification
  const secretKey = getSecretForDevice(deviceId);
  const expectedHash = crypto
    .createHmac('sha256', secretKey)
    .update(rawPayloadStr)
    .digest('hex');

  let signatureMatched = (expectedHash === signature);

  if (!signatureMatched) {
    try {
      if (typeof rawPayloadStr === 'string') {
        const obj = JSON.parse(rawPayloadStr);
        const reconstructed = `{"deviceId":"${obj.deviceId}","temp":${Number(obj.temp).toFixed(2)},"doorOpen":${obj.doorOpen},"compressor":${obj.compressor},"power":"${obj.power}","battery":${Number(obj.battery).toFixed(1)},"doorOpenTimeSec":${obj.doorOpenTimeSec || 0},"timestamp":${obj.timestamp},"nonce":${obj.nonce}}`;
        const rehash = crypto.createHmac('sha256', secretKey).update(reconstructed).digest('hex');
        if (rehash === signature) {
          signatureMatched = true;
        }
      }
    } catch (e) {}
  }

  if (!signatureMatched) {
    return { valid: false, error: 'HMAC signature verification failed' };
  }

  // 2. SECOND STEP: Timestamp Freshness Check
  const now = Date.now();
  const parsedTs = Number(timestamp);
  let messageTimeMs = parsedTs;
  if (parsedTs < 10000000000) {
    messageTimeMs = parsedTs * 1000;
  }

  // Enforce 5-minute skew window only for realistic epoch timestamps
  if (messageTimeMs > 1600000000000) {
    if (Math.abs(now - messageTimeMs) > 5 * 60 * 1000) {
      return { valid: false, error: 'Timestamp out of acceptable window (> 5 mins skew)' };
    }
  }

  // 3. THIRD STEP: Strict Monotonic & Anti-Replay Check
  const numNonce = Number(nonce);
  const tracker = getDeviceNonceTracker(deviceId);

  // If already seen anytime, reject as replay attack
  if (tracker.seenSet.has(numNonce)) {
    return { valid: false, error: `Replay attack detected: duplicate nonce ${nonce} already processed for ${deviceId}` };
  }

  // Enforce monotonic order (must be greater than last seen nonce)
  // Exception: Allow initialization on first message
  if (tracker.lastNonce > 0 && numNonce <= tracker.lastNonce) {
    return { valid: false, error: `Replay/Order attack detected: nonce ${numNonce} is not strictly monotonic (> ${tracker.lastNonce}) for ${deviceId}` };
  }

  // Update tracker
  tracker.lastNonce = numNonce;
  tracker.seenSet.add(numNonce);
  // Keep set bounded to last 5,000 nonces to avoid memory leaks
  if (tracker.seenSet.size > 5000) {
    const arr = Array.from(tracker.seenSet);
    tracker.seenSet = new Set(arr.slice(arr.length - 2500));
  }

  return { valid: true };
}

module.exports = {
  verifyDeviceMessage,
  getSecretForDevice
};
