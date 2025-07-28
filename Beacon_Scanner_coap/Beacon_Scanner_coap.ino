#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <BLEBeacon.h>
#include <map>
#include <set>
#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "emilehuawei";
const char* password = "cacacaca";

std::map<std::string, unsigned long> beaconLastSeen;
std::set<std::string> beaconsPresent;
const unsigned long TIMEOUT_MS = 10000;  // 10 sec d'inactivité = départ

int scanTime = 5;  //In seconds
BLEScan *pBLEScan;

unsigned long lastLEDCheck = 0;
const unsigned long LED_CHECK_INTERVAL = 5000;  // toutes les 5 secondes

void sendEvent(const std::string &beaconID, const String &eventType);
void printHex(const String& data) {
  Serial.print("Manufacturer data (hex): ");
  for (size_t i = 0; i < data.length(); i++) {
    uint8_t byteVal = static_cast<uint8_t>(data[i]);
    if (byteVal < 16) Serial.print("0");
    Serial.print(byteVal, HEX);
    Serial.print(" ");
  }
  Serial.println();
}


class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    if (advertisedDevice.haveManufacturerData()) {
      String strManufacturerData = advertisedDevice.getManufacturerData();

      uint8_t cManufacturerData[100];
      memcpy(cManufacturerData, strManufacturerData.c_str(), strManufacturerData.length());

      if (strManufacturerData.length() == 25 && cManufacturerData[0] == 0x4C && cManufacturerData[1] == 0x00) {
        Serial.println("Found an iBeacon!");
        BLEBeacon oBeacon = BLEBeacon();
        oBeacon.setData(strManufacturerData);

        std::string uuid = oBeacon.getProximityUUID().toString().c_str();
        int major = ((oBeacon.getMajor() >> 8) & 0xFF) | ((oBeacon.getMajor() & 0xFF) << 8);
        int minor = ((oBeacon.getMinor() >> 8) & 0xFF) | ((oBeacon.getMinor() & 0xFF) << 8);


        std::string beaconID = uuid + "-" + std::to_string(major) + "-" + std::to_string(minor);
        beaconLastSeen[beaconID.c_str()] = millis();

        if (!beaconsPresent.count(beaconID)) {
          Serial.printf("Beacon %s has ARRIVED\n", beaconID.c_str());
          sendEvent(beaconID, "arrival");
          beaconsPresent.insert(beaconID);
        }
      }
    }
  };
};



// === Connexion au Wi-Fi ===
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connexion à ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connecté");
  Serial.print("Adresse IP : ");
  Serial.println(WiFi.localIP());
}

void sendEvent(const std::string &uuid, const String &eventType) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi non connecté, événement non envoyé.");
    return;
  }

  HTTPClient http;
  http.begin("http://192.168.43.187:8000/event");
  http.addHeader("Content-Type", "application/json");

  String payload = "{\"uuid\":\"" + String(uuid.c_str()) + "\",\"event\":\"" + eventType + "\"}"; 

  Serial.println("Sending HTTP payload: " + payload);

  int httpResponseCode = http.POST(payload);

  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("Réponse HTTP %d : %s\n", httpResponseCode, response.c_str());
  } else {
    Serial.printf("Erreur HTTP : %s\n", http.errorToString(httpResponseCode).c_str());
  }

  http.end();
}



void setup() {
  Serial.begin(115200);
  Serial.println("Scanning...");

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();  //create new scan
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true);  //active scan uses more power, but get results faster
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(99);  // less or equal setInterval value

  setup_wifi();
}

void checkLEDState() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin("http://192.168.43.187:8000/led");
  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();
    if (payload.indexOf("\"state\":\"on\"") != -1) {
      Serial.println("Led: On");
    } else {
      Serial.println("Led: Off");
    }
  }

  http.end();
}

void loop() {
  // put your main code here, to run repeatedly:
  BLEScanResults *foundDevices = pBLEScan->start(scanTime, false);
  Serial.println("Scan done!");
  pBLEScan->clearResults();  // delete results fromBLEScan buffer to release memory
  delay(2000);

  

  // Vérifier les beacons inactifs
  unsigned long now = millis();
  for (auto it = beaconLastSeen.begin(); it != beaconLastSeen.end(); ) {
    if (now - it->second > TIMEOUT_MS) {
      Serial.printf("Beacon %s has LEFT\n", it->first.c_str());
      sendEvent(it->first, "departure");
      beaconsPresent.erase(it->first);  // ← marquer comme parti
      it = beaconLastSeen.erase(it);  // Enlever le beacon qui a disparu
    } else {
      ++it;
    }
  }
  now = millis();
  if (now - lastLEDCheck >= LED_CHECK_INTERVAL) {
    checkLEDState();
    lastLEDCheck = now;
  }
}
