#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
/*COMANDI:

.\mosquitto_pub -h broker.hivemq.com -t '/tiot/group6/led' -m '{\"bn\": \"PC\", \"e\": [{\"n\": \"led\", \"v\": 1}]}'
.\mosquitto_pub -h broker.hivemq.com -t '/tiot/group6/led' -m '{\"bn\": \"PC\", \"e\": [{\"n\": \"led\", \"v\": 0}]}'
.\mosquitto_sub -h broker.hivemq.com -t '/tiot/group6/temperature'


*/



void callback(char* topic, byte* payload, unsigned int length);

String broker_address = "broker.hivemq.com";
int broker_port = 1883;
const String base_topic = "/tiot/group6"; // Updated to Group 6

const int pinLed = 3;
const int pinTemperature = A0;

// --- Timing Control ---
unsigned long lastPublishTime = 0;
const long interval = 10000; // 10 seconds

// --- Thermistor Constants ---
const int B = 4275; 
const long R0 = 100000;
const float T0 = 298.15;

// --- JSON Capacity from Screenshot ---
const int capacity = JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(4) + 100;
DynamicJsonDocument doc_snd(capacity);
DynamicJsonDocument doc_rec(capacity);

WiFiClient wifi;
// Callback forward declaration
void callback(char* topic, byte* payload, unsigned int length);
PubSubClient client(broker_address.c_str(), broker_port, callback, wifi);

char ssid[] = "A34 di Paolo";
char password[] = "ciaone89";

void setup() {
  Serial.begin(9600);
  pinMode(pinLed, OUTPUT);
  pinMode(pinTemperature, INPUT);

  Serial.print("Connecting to: ");
  Serial.println(ssid);
  while (WiFi.begin(ssid, password) != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
}

void loop() {
  // Logic from screenshot e3498c
  if (client.state() != MQTT_CONNECTED) {
    reconnect();
  }

  // Periodic Publish Logic
  unsigned long currentMillis = millis();
  if (currentMillis - lastPublishTime >= interval) {
    lastPublishTime = currentMillis;

    // Read sensor and create json message body
    String body = senMlEncode("temperature", readTemperature(), "Cel");
    
    // Publish using the structure from your screenshot
    client.publish((base_topic + String("/temperature")).c_str(), body.c_str());
  }

  client.loop(); 
}

// --- Callback Function (screenshot e349c9) ---
void callback(char* topic, byte* payload, unsigned int length) {
  // Invece di: deserializeJson(doc_rec, (char*) payload)
  DeserializationError err = deserializeJson(doc_rec, payload, length);
  if (err) {
    Serial.print(F("deserializeJson() failed with code "));
    Serial.println(err.c_str());
  }

  // Access fields by name as requested
  if (doc_rec["e"][0]["n"] == "led") {
    if (doc_rec["e"][0]["v"] == 1) {
      digitalWrite(pinLed, HIGH);
      Serial.println("led acceso");
    }
    if (doc_rec["e"][0]["v"] == 0) {
      digitalWrite(pinLed, LOW);
      Serial.println("led SPENTO");
    }
  }
}

// --- SenML Encode (screenshot e349af) ---
String senMlEncode(String res, float v, String unit) {
  doc_snd.clear();
  doc_snd["bn"] = "ArduinoGroup6"; // Group 6
  doc_snd["e"][0]["n"] = res;
  doc_snd["e"][0]["v"] = v;
  doc_snd["e"][0]["u"] = unit;
  doc_snd["e"][0]["t"] = int(millis() / 1000);

  String output;
  serializeJson(doc_snd, output);
  return output;
}

// --- Reconnect (screenshot e34972) ---
void reconnect() {
  while (client.state() != MQTT_CONNECTED) {
    if (client.connect("TiotGroup6")) {
      client.subscribe((base_topic + String("/led")).c_str());
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
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