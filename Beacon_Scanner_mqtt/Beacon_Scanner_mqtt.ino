#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <BLEBeacon.h>
#include <map>
#include <set>
#include <WiFi.h>
#include <PubSubClient.h>

// === Configuration Wi-Fi ===
const char* ssid = "anto-22s";
const char* password = "00dadafafa";

// === Configuration MQTT ===
const char* mqtt_server = "192.168.68.65"; // Adresse IP du broker Mosquitto
const int mqtt_port = 1883;
const char* mqtt_topic = "test/topic";

WiFiClient espClient;
PubSubClient client(espClient);

std::map<std::string, unsigned long> beaconLastSeen;
std::set<std::string> beaconsPresent;
const unsigned long TIMEOUT_MS = 10000;  // 10 sec d'inactivité = départ

int scanTime = 5;  //In seconds
BLEScan *pBLEScan;

void sendEvent(const std::string &beaconID, const String &eventType);

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

// === Connexion au broker MQTT ===
void reconnect() {
  while (!client.connected()) {
    Serial.print("Connexion au broker MQTT...");
    String clientId = "ESP32Publisher-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str())) {
      Serial.println("MQTT connecté");
    } else {
      Serial.print("Échec, rc=");
      Serial.print(client.state());
      Serial.println(" nouvelle tentative dans 5 secondes");
      Serial.println(WiFi.localIP());
      delay(5000);
    }
  }
}

// === Envoi de l’événement via MQTT
void sendEvent(const std::string &beaconID, const String &eventType) {
  String topic = "badge/" + String(beaconID.c_str()) + "/event";
  String json = "{\"badge_id\":\"" + String(beaconID.c_str()) + "\",\"event\":\"" + eventType + "\",\"timestamp\":" + String(millis()) + "}";

  Serial.printf("Publishing to topic: %s\n", topic.c_str());
  client.publish(topic.c_str(), json.c_str());
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
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  // put your main code here, to run repeatedly:
  BLEScanResults *foundDevices = pBLEScan->start(scanTime, false);
  Serial.println("Scan done!");
  pBLEScan->clearResults();  // delete results fromBLEScan buffer to release memory
  delay(2000);

  client.loop();

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
}
