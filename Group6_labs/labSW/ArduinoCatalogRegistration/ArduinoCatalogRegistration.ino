//Software Laboratory part 3, Exercise 10
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#define SECRET_SSID "XXXXXX"
#define SECRET_PASS "XXXXXX"

const char catalog_host[] = "172.22.198.XXX";
const int catalog_port = 8080;

void callback(char* topic, byte* payload, unsigned int length);

String broker_address = "broker.hivemq.com";
int broker_port = 1883;

const String device_id = "arduino_d001";
const String topic_pub = "/tiot/group6/temperature";
const String topic_sub = "/tiot/group6/led";

const int pinLed = 3;
const int pinTemperature = A0;

unsigned long lastPublishTime = 0;
const long interval = 10000;

const int B = 4275;
const long R0 = 100000;
const float T0 = 298.15;

unsigned long lastRenewTime = 0;
const long renewInterval = 60000;

DynamicJsonDocument doc_snd(512);
DynamicJsonDocument doc_rec(512);
WiFiClient mqttWifi;
PubSubClient mqttClient(mqttWifi);

char ssid[] = SECRET_SSID;
char password[] = SECRET_PASS;

const int pinPIR = 7;
const long TIMEOUT_PIR = 2 * 60 * 1000; // 2 minuti in ms
unsigned long lastMotionTime = 0;
bool presenceActive = false;
const String topic_motion = "/tiot/group6/motion";

void getBrokerInfo() {
  Serial.println("Connecting to the catalog...");
  
  WiFiClient httpWifi;
  HttpClient httpClient(httpWifi, catalog_host, catalog_port);

  httpClient.get("/catalog");
  int statusCode = httpClient.responseStatusCode();
  String response = httpClient.responseBody();
  httpClient.stop(); 

  if (statusCode >= 200 && statusCode < 300) {
    DynamicJsonDocument doc(512);
    deserializeJson(doc, response);
    String ip = doc["broker"]["ip"] | "broker.hivemq.com";
    broker_port = doc["broker"]["port"] | 1883;
    if (ip == "localhost" || ip == "127.0.0.1") {
      broker_address = String(catalog_host);
    } else {
      broker_address = ip;
    }
    Serial.println("Broker from catalog: " + broker_address);
  } else {
    Serial.println("Catalog error, status: " + String(statusCode) + ", using default broker");
    broker_address = "broker.hivemq.com";
  }
}

String createRegistrationPayload() {
  DynamicJsonDocument doc(256);
  doc["ID"] = device_id;
  doc["Description"] = "Arduino Sensor & Actuator Node";
  doc["MQTT_topic_pub"] = topic_pub;
  doc["MQTT_topic_sub"] = topic_sub;
  JsonArray resources = doc.createNestedArray("Resources");
  resources.add("temperature");
  resources.add("led");
  String output;
  serializeJson(doc, output);
  return output;
}

void registerToCatalog() {
  Serial.println("Registering to catalog...");

  WiFiClient httpWifi;
  HttpClient httpClient(httpWifi, catalog_host, catalog_port);

  String payload = createRegistrationPayload();
  httpClient.beginRequest();
  httpClient.post("/catalog");
  httpClient.sendHeader("Content-Type", "application/json");
  httpClient.sendHeader("Content-Length", payload.length());
  httpClient.beginBody();
  httpClient.print(payload);
  httpClient.endRequest();

  int statusCode = httpClient.responseStatusCode();
  String body = httpClient.responseBody(); 
  httpClient.stop();
  Serial.println("Registration status: " + String(statusCode));
}

void renewRegistration() {
  Serial.println("Keep-Alive...");
  WiFiClient httpWifi;
  HttpClient httpClient(httpWifi, catalog_host, catalog_port);

  String payload = createRegistrationPayload();
  httpClient.beginRequest();
  httpClient.put("/catalog");
  httpClient.sendHeader("Content-Type", "application/json");
  httpClient.sendHeader("Content-Length", payload.length());
  httpClient.beginBody();
  httpClient.print(payload);
  httpClient.endRequest();

  int statusCode = httpClient.responseStatusCode();
  String body = httpClient.responseBody(); 
  httpClient.stop();
  Serial.println("Renew status: " + String(statusCode));
}


void setup() {
  Serial.begin(9600);
  pinMode(pinLed, OUTPUT);
  pinMode(pinTemperature, INPUT);
  pinMode(pinPIR, INPUT);

  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  while (WiFi.begin(ssid, password) != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected! IP: " + WiFi.localIP().toString());

  delay(50); 

  getBrokerInfo();

  delay(50); 

  registerToCatalog();
  lastRenewTime = millis();

  mqttClient.setServer(broker_address.c_str(), broker_port);
  mqttClient.setCallback(callback);
}

void loop() {
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop();

  unsigned long now = millis();

  if (now - lastPublishTime >= interval) {
    lastPublishTime = now;
    String body = senMlEncode("temperature", readTemperature(), "Cel");
    mqttClient.publish(topic_pub.c_str(), body.c_str());
    Serial.println("Published temperature");
  }

  int pirVal = digitalRead(pinPIR);
  if (pirVal == HIGH) {
    lastMotionTime = now;
    if (!presenceActive) {
        presenceActive = true;
        String body = senMlEncode("motion", (float)pirVal, "boolean");
        mqttClient.publish(topic_motion.c_str(), body.c_str());
        Serial.println("Motion detected - published TRUE");
    }
  }

  if (presenceActive && (now - lastMotionTime) > TIMEOUT_PIR) {
    presenceActive = false;
    String body = senMlEncode("motion", (float)pirVal, "boolean");
    mqttClient.publish(topic_motion.c_str(), body.c_str());
    Serial.println("Presence timeout - published FALSE");
  }

  if (now - lastRenewTime >= renewInterval) {
    lastRenewTime = now;
    renewRegistration();
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  DeserializationError err = deserializeJson(doc_rec, payload, length);
  if (err) {
    Serial.println("JSON parse error: " + String(err.c_str()));
    return;
  }
  if (doc_rec["e"][0]["n"] == "led") {
    int val = doc_rec["e"][0]["v"];
    if (val == 1) {
      digitalWrite(pinLed, HIGH);
      Serial.println("LED ON");
    } else {
      digitalWrite(pinLed, LOW);
      Serial.println("LED OFF");
    }
  }
}

String senMlEncode(String res, float v, String unit) {
  doc_snd.clear();
  doc_snd["bn"] = device_id;
  doc_snd["e"][0]["n"] = res;
  doc_snd["e"][0]["v"] = v;
  doc_snd["e"][0]["u"] = unit;
  doc_snd["e"][0]["t"] = int(millis() / 1000);
  String output;
  serializeJson(doc_snd, output);
  return output;
}

void reconnect() {
  int attempts = 0;
  while (!mqttClient.connected() && attempts < 5) {
    Serial.print("Connecting to MQTT broker " + broker_address + "...");
    if (mqttClient.connect(device_id.c_str())) {
      Serial.println(" connected!");
      mqttClient.subscribe(topic_sub.c_str());
      mqttClient.subscribe(topic_motion.c_str());
    } else {
      Serial.println(" failed rc=" + String(mqttClient.state()) + ", retry in 5s");
      delay(5000);
      attempts++;
    }
  }
}

float readTemperature() {
  int val = analogRead(pinTemperature);
  if (val == 0) return 0;
  float R = (1023.0 / (float)val - 1.0) * R0;
  float temperatureC = 1.0 / (log(R / R0) / B + (1.0 / T0)) - 273.15;
  return temperatureC;
}