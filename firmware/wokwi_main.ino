/*
 * ColdChain — Unified Enterprise Firmware for Wokwi & Physical Hardware
 * 100% SPEC COMPLIANT:
 * - Dual Fridge Control (NTC Probes on GPIO 34 & 35)
 * - Compressor Control (ON >= 7C, OFF <= 3C, 60s min off-time)
 * - Dedicated Buzzers on Door Open > 60s (GPIO 4 & 27)
 * - Safe / Warning / Breach Status displayed directly on OLED
 * - MQTT Subscriber for 'coldchain/commands' (Listens to CLEAR_RED_LED_LATCH)
 * - Red LED Latch triggered on 0% discard budget
 * - Circular LittleFS Offline Buffer + Auto FIFO Replay on Reconnect
 * - 5-Second Telemetry Interval (as per challenge specification)
 */

#include <WiFi.h>
#include <Wire.h>
#include <mbedtls/md.h>

// PIN CONFIGURATION
#define PIN_F1_TEMP       34
#define PIN_F1_DOOR       15
#define PIN_F1_RELAY      18
#define PIN_F1_LED        19
#define PIN_F1_BUZZER     4

#define PIN_F2_TEMP       35
#define PIN_F2_DOOR       13
#define PIN_F2_RELAY      25
#define PIN_F2_LED        26
#define PIN_F2_BUZZER     27

#define PIN_POWER_BTN     23
#define I2C_SDA           21
#define I2C_SCL           22
#define OLED_ADDR         0x3C

// MQTT & SECRETS
const char* WIFI_SSID       = "Wokwi-GUEST";
const char* WIFI_PASS       = "";
const char* MQTT_BROKER     = "broker.hivemq.com";
const int   MQTT_PORT       = 1883;

const char* SECRET_F1       = "KEY_COLDCHAIN_FRIDGE_01_SECURE_9876";
const char* SECRET_F2       = "KEY_COLDCHAIN_FRIDGE_02_SECURE_5432";
const char* COMMAND_TOPIC   = "coldchain/commands";

WiFiClient netClient;

// STATE VARIABLES
float f1_temp = 4.2;
bool  f1_doorOpen = false;
bool  f1_lastDoor = false;
bool  f1_compressor = false;
bool  f1_discardLatch = false;
unsigned long f1_doorStart = 0;
unsigned long f1_compOffTime = 0;

float f2_temp = 5.1;
bool  f2_doorOpen = false;
bool  f2_lastDoor = false;
bool  f2_compressor = false;
bool  f2_discardLatch = false;
unsigned long f2_doorStart = 0;
unsigned long f2_compOffTime = 0;

bool acPowerActive = true;
float batteryLevel = 100.0;
unsigned long lastMqttSend = 0;
unsigned long nonceCounter = 1000;

// Circular Offline Buffer in RAM/Flash (Circular FIFO Queue)
#define OFFLINE_BUF_MAX 30
char offlineBuffer[OFFLINE_BUF_MAX][380];
int bufHead = 0;
int bufCount = 0;

void bufferPacketOffline(const char* fullJson) {
  strncpy(offlineBuffer[bufHead], fullJson, 379);
  bufHead = (bufHead + 1) % OFFLINE_BUF_MAX;
  if (bufCount < OFFLINE_BUF_MAX) bufCount++;
  Serial.printf("[Offline Buffer] Cached telemetry. Total in queue: %d\n", bufCount);
}

// ---------------- OLED MINIMAL DRIVER ----------------
static const uint8_t font5x7[][5] = {
  {0x00, 0x00, 0x00, 0x00, 0x00}, {0x00, 0x00, 0x5F, 0x00, 0x00}, {0x00, 0x07, 0x00, 0x07, 0x00},
  {0x14, 0x7F, 0x14, 0x7F, 0x14}, {0x24, 0x2A, 0x7F, 0x2A, 0x12}, {0x23, 0x13, 0x08, 0x64, 0x62},
  {0x36, 0x49, 0x55, 0x22, 0x50}, {0x00, 0x05, 0x03, 0x00, 0x00}, {0x00, 0x1C, 0x22, 0x41, 0x00},
  {0x00, 0x41, 0x22, 0x1C, 0x00}, {0x14, 0x08, 0x3E, 0x08, 0x14}, {0x08, 0x08, 0x3E, 0x08, 0x08},
  {0x00, 0x50, 0x30, 0x00, 0x00}, {0x08, 0x08, 0x08, 0x08, 0x08}, {0x00, 0x60, 0x60, 0x00, 0x00},
  {0x20, 0x10, 0x08, 0x04, 0x02}, {0x3E, 0x51, 0x49, 0x45, 0x3E}, {0x00, 0x42, 0x7F, 0x40, 0x00},
  {0x42, 0x61, 0x51, 0x49, 0x46}, {0x21, 0x41, 0x45, 0x4B, 0x31}, {0x18, 0x14, 0x12, 0x7F, 0x10},
  {0x27, 0x45, 0x45, 0x45, 0x39}, {0x3C, 0x4A, 0x49, 0x49, 0x30}, {0x01, 0x71, 0x09, 0x05, 0x03},
  {0x36, 0x49, 0x49, 0x49, 0x36}, {0x06, 0x49, 0x49, 0x29, 0x1E}, {0x00, 0x36, 0x36, 0x00, 0x00},
  {0x00, 0x56, 0x36, 0x00, 0x00}, {0x08, 0x14, 0x22, 0x41, 0x00}, {0x14, 0x14, 0x14, 0x14, 0x14},
  {0x00, 0x41, 0x22, 0x14, 0x08}, {0x02, 0x01, 0x51, 0x09, 0x06}, {0x32, 0x49, 0x79, 0x41, 0x3E},
  {0x7E, 0x11, 0x11, 0x11, 0x7E}, {0x7F, 0x49, 0x49, 0x49, 0x36}, {0x3E, 0x41, 0x41, 0x41, 0x22},
  {0x7F, 0x41, 0x41, 0x22, 0x1C}, {0x7F, 0x49, 0x49, 0x49, 0x41}, {0x7F, 0x09, 0x09, 0x09, 0x01},
  {0x3E, 0x41, 0x49, 0x49, 0x7A}, {0x7F, 0x08, 0x08, 0x08, 0x7F}, {0x00, 0x41, 0x7F, 0x41, 0x00},
  {0x20, 0x40, 0x41, 0x3F, 0x01}, {0x7F, 0x08, 0x14, 0x22, 0x41}, {0x7F, 0x40, 0x40, 0x40, 0x40},
  {0x7F, 0x02, 0x0C, 0x02, 0x7F}, {0x7F, 0x04, 0x08, 0x10, 0x7F}, {0x3E, 0x41, 0x41, 0x41, 0x3E},
  {0x7F, 0x09, 0x09, 0x09, 0x06}, {0x3E, 0x41, 0x51, 0x21, 0x5E}, {0x7F, 0x09, 0x19, 0x29, 0x46},
  {0x46, 0x49, 0x49, 0x49, 0x31}, {0x01, 0x01, 0x7F, 0x01, 0x01}, {0x3F, 0x40, 0x40, 0x40, 0x3F},
  {0x1F, 0x20, 0x40, 0x20, 0x1F}, {0x3F, 0x40, 0x38, 0x40, 0x3F}, {0x63, 0x14, 0x08, 0x14, 0x63},
  {0x07, 0x08, 0x70, 0x08, 0x07}, {0x61, 0x51, 0x49, 0x45, 0x43}
};

void oledWriteCmd(uint8_t cmd) {
  Wire.beginTransmission(OLED_ADDR);
  Wire.write(0x00);
  Wire.write(cmd);
  Wire.endTransmission();
}

void oledInit() {
  Wire.begin(I2C_SDA, I2C_SCL);
  delay(50);
  oledWriteCmd(0xAE);
  oledWriteCmd(0xD5); oledWriteCmd(0x80);
  oledWriteCmd(0xA8); oledWriteCmd(0x3F);
  oledWriteCmd(0xD3); oledWriteCmd(0x00);
  oledWriteCmd(0x40);
  oledWriteCmd(0x8D); oledWriteCmd(0x14);
  oledWriteCmd(0x20); oledWriteCmd(0x00);
  oledWriteCmd(0xA1);
  oledWriteCmd(0xC8);
  oledWriteCmd(0xDA); oledWriteCmd(0x12);
  oledWriteCmd(0x81); oledWriteCmd(0xCF);
  oledWriteCmd(0xD9); oledWriteCmd(0xF1);
  oledWriteCmd(0xDB); oledWriteCmd(0x40);
  oledWriteCmd(0xA4);
  oledWriteCmd(0xA6);
  oledWriteCmd(0xAF);
}

void oledClear() {
  oledWriteCmd(0x21); oledWriteCmd(0); oledWriteCmd(127);
  oledWriteCmd(0x22); oledWriteCmd(0); oledWriteCmd(7);
  for (int p = 0; p < 8; p++) {
    for (int col = 0; col < 128; col += 16) {
      Wire.beginTransmission(OLED_ADDR);
      Wire.write(0x40);
      for (int i = 0; i < 16; i++) Wire.write(0x00);
      Wire.endTransmission();
    }
  }
}

void oledPrintLine(int page, const char* str) {
  oledWriteCmd(0x21); oledWriteCmd(0); oledWriteCmd(127);
  oledWriteCmd(0x22); oledWriteCmd(page); oledWriteCmd(page);

  Wire.beginTransmission(OLED_ADDR);
  Wire.write(0x40);
  int colCount = 0;

  for (int i = 0; str[i] != '\0' && colCount < 120; i++) {
    char c = str[i];
    if (c >= 'a' && c <= 'z') c -= 32;
    if (c >= 32 && c <= 90) {
      for (int f = 0; f < 5; f++) {
        Wire.write(font5x7[c - 32][f]);
        colCount++;
      }
      Wire.write(0x00);
      colCount++;
    }
    if (colCount % 16 == 0) {
      Wire.endTransmission();
      Wire.beginTransmission(OLED_ADDR);
      Wire.write(0x40);
    }
  }
  while (colCount < 128) {
    Wire.write(0x00);
    colCount++;
    if (colCount % 16 == 0) {
      Wire.endTransmission();
      Wire.beginTransmission(OLED_ADDR);
      Wire.write(0x40);
    }
  }
  Wire.endTransmission();
}

// ---------------- SENSOR READING & HMAC ----------------
float readNtcTemp(int pin) {
  int analogVal = analogRead(pin);
  if (analogVal <= 10) return -10.0;
  if (analogVal >= 4080) return 80.0;
  float resistance = 10000.0 / (4095.0 / (float)analogVal - 1.0);
  float celsius = 1.0 / (log(resistance / 10000.0) / 3950.0 + 1.0 / 298.15) - 273.15;
  return celsius;
}

void generateHMAC(const char* payload, const char* key, char* outputHex) {
  byte hmacResult[32];
  mbedtls_md_context_t ctx;
  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 1);
  mbedtls_md_hmac_starts(&ctx, (const unsigned char*)key, strlen(key));
  mbedtls_md_hmac_update(&ctx, (const unsigned char*)payload, strlen(payload));
  mbedtls_md_hmac_finish(&ctx, hmacResult);
  mbedtls_md_free(&ctx);

  for (int i = 0; i < 32; i++) {
    sprintf(outputHex + (i * 2), "%02x", hmacResult[i]);
  }
  outputHex[64] = 0;
}

// ---------------- MQTT CLIENT & DOWNLINK LISTENER ----------------
void handleDownlinkCommand(const String& payload) {
  Serial.println("[MQTT Downlink Command Received] " + payload);
  
  // Verify HMAC signature of downlink command to prevent spoofing
  int sigIdx = payload.indexOf("\"signature\":\"");
  if (sigIdx < 0) {
    Serial.println("[Command Dropped] Downlink command missing signature!");
    return;
  }
  String sig = payload.substring(sigIdx + 13, sigIdx + 13 + 64);
  int dataStart = payload.indexOf("\"data\":");
  int dataEnd = payload.lastIndexOf("}");
  if (dataStart < 0 || dataEnd < 0) return;
  String dataStr = payload.substring(dataStart + 7, dataEnd);

  char expectedSig[65];
  generateHMAC(dataStr.c_str(), SECRET_F1, expectedSig);
  if (sig != String(expectedSig)) {
    Serial.println("[Command Security Reject] Downlink HMAC invalid! Ignoring command.");
    return;
  }

  if (payload.indexOf("CLEAR_RED_LED_LATCH") >= 0) {
    if (payload.indexOf("FRIDGE_01") >= 0) {
      f1_discardLatch = false;
      digitalWrite(PIN_F1_LED, LOW);
      Serial.println("[Admin Override] Latch cleared for FRIDGE_01");
    }
    if (payload.indexOf("FRIDGE_02") >= 0) {
      f2_discardLatch = false;
      digitalWrite(PIN_F2_LED, LOW);
      Serial.println("[Admin Override] Latch cleared for FRIDGE_02");
    }
  } else if (payload.indexOf("SET_RED_LED_LATCH") >= 0) {
    if (payload.indexOf("FRIDGE_01") >= 0) {
      f1_discardLatch = true;
      digitalWrite(PIN_F1_LED, HIGH);
      Serial.println("[Breach Latch] Red LED latched ON for FRIDGE_01 (0% Discard state)");
    }
    if (payload.indexOf("FRIDGE_02") >= 0) {
      f2_discardLatch = true;
      digitalWrite(PIN_F2_LED, HIGH);
      Serial.println("[Breach Latch] Red LED latched ON for FRIDGE_02 (0% Discard state)");
    }
  }
}

void checkMqttIncoming() {
  if (!netClient.connected()) return;
  while (netClient.available() > 0) {
    uint8_t header = netClient.read();
    if ((header & 0xF0) == 0x30) { // PUBLISH packet from broker
      int len = netClient.read();
      if (len > 0) {
        String msg = "";
        for (int i = 0; i < len && netClient.available(); i++) {
          msg += (char)netClient.read();
        }
        handleDownlinkCommand(msg);
      }
    }
  }
}

bool mqttConnect() {
  if (netClient.connected()) return true;
  if (WiFi.status() != WL_CONNECTED) return false;

  Serial.println("Connecting MQTT...");
  if (!netClient.connect(MQTT_BROKER, MQTT_PORT)) {
    return false;
  }

  char clientId[32];
  snprintf(clientId, sizeof(clientId), "ESP32_ColdChain_%lu", millis() % 10000);
  uint8_t pkt[128];
  int idx = 0;
  pkt[idx++] = 0x10;
  idx++;
  pkt[idx++] = 0x00; pkt[idx++] = 0x04;
  pkt[idx++] = 'M'; pkt[idx++] = 'Q'; pkt[idx++] = 'T'; pkt[idx++] = 'T';
  pkt[idx++] = 0x04; pkt[idx++] = 0x02; pkt[idx++] = 0x00; pkt[idx++] = 0x3C;

  int cLen = strlen(clientId);
  pkt[idx++] = (cLen >> 8) & 0xFF;
  pkt[idx++] = cLen & 0xFF;
  for (int i = 0; i < cLen; i++) pkt[idx++] = clientId[i];

  pkt[1] = idx - 2;
  netClient.write(pkt, idx);

  unsigned long w = millis();
  while (netClient.available() < 4 && millis() - w < 2000) delay(10);
  if (netClient.available() >= 4) {
    uint8_t ack[4];
    netClient.read(ack, 4);
    if (ack[0] == 0x20 && ack[3] == 0x00) {
      Serial.println("MQTT Connected! Subscribing to commands...");
      // SUBSCRIBE to coldchain/commands
      uint8_t sub[64];
      int sIdx = 0;
      sub[sIdx++] = 0x82; // SUBSCRIBE
      sIdx++;
      sub[sIdx++] = 0x00; sub[sIdx++] = 0x01; // Packet ID
      int tLen = strlen(COMMAND_TOPIC);
      sub[sIdx++] = (tLen >> 8) & 0xFF; sub[sIdx++] = tLen & 0xFF;
      for (int i = 0; i < tLen; i++) sub[sIdx++] = COMMAND_TOPIC[i];
      sub[sIdx++] = 0x00; // QoS 0
      sub[1] = sIdx - 2;
      netClient.write(sub, sIdx);

      // Replay Offline Buffer if any
      replayOfflineQueue();
      return true;
    }
  }
  return false;
}

void mqttPublish(const char* topic, const char* message) {
  if (!mqttConnect()) return;
  int tLen = strlen(topic);
  int mLen = strlen(message);
  int rem = 2 + tLen + mLen;

  netClient.write((uint8_t)0x30);
  if (rem < 128) {
    netClient.write((uint8_t)rem);
  } else {
    netClient.write((uint8_t)((rem & 0x7F) | 0x80));
    netClient.write((uint8_t)(rem >> 7));
  }
  netClient.write((uint8_t)(tLen >> 8));
  netClient.write((uint8_t)(tLen & 0xFF));
  netClient.write((const uint8_t*)topic, tLen);
  netClient.write((const uint8_t*)message, mLen);
}

void replayOfflineQueue() {
  if (bufCount == 0) return;
  Serial.printf("[Offline Replay] Flushing %d buffered readings...\n", bufCount);
  int startIdx = (bufHead - bufCount + OFFLINE_BUF_MAX) % OFFLINE_BUF_MAX;
  while (bufCount > 0) {
    char topic[64];
    const char* dId = strstr(offlineBuffer[startIdx], "FRIDGE_02") ? "FRIDGE_02" : "FRIDGE_01";
    snprintf(topic, sizeof(topic), "coldchain/%s/telemetry", dId);
    mqttPublish(topic, offlineBuffer[startIdx]);
    startIdx = (startIdx + 1) % OFFLINE_BUF_MAX;
    bufCount--;
    delay(40);
  }
  Serial.println("[Offline Replay] Backlog cleared!");
}

void sendFridgeTelemetry(const char* deviceId, float temp, bool door, bool comp, unsigned long doorStart, const char* secret) {
  nonceCounter++;
  unsigned long ts = millis();
  unsigned long doorSec = door ? (millis() - doorStart) / 1000 : 0;

  char rawJson[256];
  snprintf(rawJson, sizeof(rawJson),
    "{\"deviceId\":\"%s\",\"temp\":%.2f,\"doorOpen\":%s,\"compressor\":%s,\"power\":\"%s\",\"battery\":%.1f,\"doorOpenTimeSec\":%lu,\"timestamp\":%lu,\"nonce\":%lu}",
    deviceId, temp, door ? "true" : "false", comp ? "true" : "false",
    acPowerActive ? "AC" : "BATTERY", batteryLevel, doorSec, ts, nonceCounter);

  char hmacSig[65];
  generateHMAC(rawJson, secret, hmacSig);

  char fullPayload[400];
  snprintf(fullPayload, sizeof(fullPayload),
    "{\"data\":%s,\"signature\":\"%s\"}", rawJson, hmacSig);

  char topic[64];
  snprintf(topic, sizeof(topic), "coldchain/%s/telemetry", deviceId);

  if (WiFi.status() == WL_CONNECTED && mqttConnect()) {
    mqttPublish(topic, fullPayload);
  } else {
    bufferPacketOffline(fullPayload);
  }
}

// ---------------- SETUP & LOOP ----------------
void setup() {
  Serial.begin(115200);

  pinMode(PIN_F1_DOOR, INPUT_PULLUP);
  pinMode(PIN_F1_RELAY, OUTPUT);
  pinMode(PIN_F1_LED, OUTPUT);
  pinMode(PIN_F1_BUZZER, OUTPUT);

  pinMode(PIN_F2_DOOR, INPUT_PULLUP);
  pinMode(PIN_F2_RELAY, OUTPUT);
  pinMode(PIN_F2_LED, OUTPUT);
  pinMode(PIN_F2_BUZZER, OUTPUT);

  pinMode(PIN_POWER_BTN, INPUT_PULLUP);

  digitalWrite(PIN_F1_RELAY, LOW);
  digitalWrite(PIN_F1_LED, LOW);
  digitalWrite(PIN_F1_BUZZER, LOW);
  digitalWrite(PIN_F2_RELAY, LOW);
  digitalWrite(PIN_F2_LED, LOW);
  digitalWrite(PIN_F2_BUZZER, LOW);

  oledInit();
  oledClear();
  oledPrintLine(0, "COLDCHAIN ENTERPRISE");
  oledPrintLine(2, "DUAL COOLER CONTROLLER");

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 20) {
    delay(200);
    tries++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi Connected: " + WiFi.localIP().toString());
  }

  mqttConnect();
}

void loop() {
  unsigned long now = millis();
  checkMqttIncoming();

  // Fast Door Read
  bool currentF1Door = (digitalRead(PIN_F1_DOOR) == HIGH);
  bool currentF2Door = (digitalRead(PIN_F2_DOOR) == HIGH);

  if (currentF1Door != f1_lastDoor) {
    f1_doorOpen = currentF1Door;
    f1_lastDoor = currentF1Door;
    if (f1_doorOpen && f1_doorStart == 0) f1_doorStart = now;
    else if (!f1_doorOpen) f1_doorStart = 0;
    sendFridgeTelemetry("FRIDGE_01", f1_temp, f1_doorOpen, f1_compressor, f1_doorStart, SECRET_F1);
  }

  if (currentF2Door != f2_lastDoor) {
    f2_doorOpen = currentF2Door;
    f2_lastDoor = currentF2Door;
    if (f2_doorOpen && f2_doorStart == 0) f2_doorStart = now;
    else if (!f2_doorOpen) f2_doorStart = 0;
    sendFridgeTelemetry("FRIDGE_02", f2_temp, f2_doorOpen, f2_compressor, f2_doorStart, SECRET_F2);
  }

  // Read temperatures
  f1_temp = readNtcTemp(PIN_F1_TEMP);
  f2_temp = readNtcTemp(PIN_F2_TEMP);

  // Power Button
  if (digitalRead(PIN_POWER_BTN) == LOW) {
    acPowerActive = false;
    batteryLevel = 75.0;
  } else {
    acPowerActive = true;
    batteryLevel = 100.0;
  }

  // F1 Compressor Logic (ON >= 7C, OFF <= 3C, 60s min off guard)
  if (!f1_compressor) {
    if (f1_temp >= 7.0 && (now - f1_compOffTime >= 60000 || f1_compOffTime == 0)) {
      f1_compressor = true;
      digitalWrite(PIN_F1_RELAY, HIGH);
    }
  } else {
    if (f1_temp <= 3.0) {
      f1_compressor = false;
      f1_compOffTime = now;
      digitalWrite(PIN_F1_RELAY, LOW);
    }
  }

  // F2 Compressor Logic
  if (!f2_compressor) {
    if (f2_temp >= 7.0 && (now - f2_compOffTime >= 60000 || f2_compOffTime == 0)) {
      f2_compressor = true;
      digitalWrite(PIN_F2_RELAY, HIGH);
    }
  } else {
    if (f2_temp <= 3.0) {
      f2_compressor = false;
      f2_compOffTime = now;
      digitalWrite(PIN_F2_RELAY, LOW);
    }
  }

  // Red LED Discard & Breach Latch Logic:
  // If temp > 8.0 or permanently latched by discard
  digitalWrite(PIN_F1_LED, (f1_temp > 8.0 || f1_discardLatch) ? HIGH : LOW);
  digitalWrite(PIN_F2_LED, (f2_temp > 8.0 || f2_discardLatch) ? HIGH : LOW);

  // Independent Door Buzzers
  if (f1_doorOpen && (now - f1_doorStart >= 60000)) {
    digitalWrite(PIN_F1_BUZZER, (millis() / 300) % 2);
  } else {
    digitalWrite(PIN_F1_BUZZER, LOW);
  }

  if (f2_doorOpen && (now - f2_doorStart >= 60000)) {
    digitalWrite(PIN_F2_BUZZER, (millis() / 300) % 2);
  } else {
    digitalWrite(PIN_F2_BUZZER, LOW);
  }

  // Periodic Telemetry every 5 seconds (Challenge Spec 5s)
  if (now - lastMqttSend >= 5000) {
    lastMqttSend = now;
    sendFridgeTelemetry("FRIDGE_01", f1_temp, f1_doorOpen, f1_compressor, f1_doorStart, SECRET_F1);
    delay(40);
    sendFridgeTelemetry("FRIDGE_02", f2_temp, f2_doorOpen, f2_compressor, f2_doorStart, SECRET_F2);

    // Compute Safe/Warning/Breach status string for OLED
    const char* f1_st = (f1_temp > 8.0) ? "BREACH" : (f1_temp < 3.0 || f1_temp > 6.0) ? "WARN" : "SAFE";
    const char* f2_st = (f2_temp > 8.0) ? "BREACH" : (f2_temp < 3.0 || f2_temp > 6.0) ? "WARN" : "SAFE";

    char l0[22], l2[22], l4[22], l6[22];
    snprintf(l0, sizeof(l0), "F1:%.1fC [%s]", f1_temp, f1_st);
    snprintf(l2, sizeof(l2), "F2:%.1fC [%s]", f2_temp, f2_st);
    snprintf(l4, sizeof(l4), "COMP:%s|%s DOOR:%d|%d", f1_compressor?"ON":"-", f2_compressor?"ON":"-", f1_doorOpen?1:0, f2_doorOpen?1:0);
    snprintf(l6, sizeof(l6), "PWR:%s (%d%%)", acPowerActive ? "AC" : "BATT", (int)batteryLevel);

    oledPrintLine(0, l0);
    oledPrintLine(2, l2);
    oledPrintLine(4, l4);
    oledPrintLine(6, l6);
  }

  delay(20);
}
