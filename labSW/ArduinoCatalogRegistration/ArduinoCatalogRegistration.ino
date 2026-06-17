//Software Laboratory part 3, Exercise 10
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#define SECRET_SSID "XXXXX"
#define SECRET_PASS "XXXXX"
/*COMANDI:

.\mosquitto_pub -h broker.hivemq.com -t '/tiot/group6/led' -m '{\"bn\": \"PC\", \"e\": [{\"n\": \"led\", \"v\": 1}]}'
.\mosquitto_pub -h broker.hivemq.com -t '/tiot/group6/led' -m '{\"bn\": \"PC\", \"e\": [{\"n\": \"led\", \"v\": 0}]}'
.\mosquitto_sub -h broker.hivemq.com -t '/tiot/group6/temperature'


*/

const char catalog_host[] = "192.168.1.XXX"; 
const int catalog_port = 8080;

void callback(char* topic, byte* payload, unsigned int length);

String broker_address = "";
int broker_port = 1883;
const String base_topic = "/tiot/group6"; 

const String device_id = "arduino_d001";
const String topic_pub = "/tiot/group6/temperature";
const String topic_sub = "/tiot/group6/led";


const int pinLed = 3;
const int pinTemperature = A0;

unsigned long lastPublishTime = 0;
const long interval = 10000; // 10 seconds

const int B = 4275; 
const long R0 = 100000;
const float T0 = 298.15;

unsigned long lastRenewTime = 0;
const long renewInterval = 60000; // 60 seconds

const int capacity = JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(4) + 100;
DynamicJsonDocument doc_snd(capacity);
DynamicJsonDocument doc_rec(capacity);

WiFiClient wifi;
HttpClient httpClient = HttpClient(wifi, catalog_host, catalog_port);
// Callback forward declaration
void callback(char* topic, byte* payload, unsigned int length);
PubSubClient client(wifi);

char ssid[] = SECRET_SSID ;
char password[] = SECRET_PASS;


void getBrokerInfo(){
  Serial.println("Connecting to the catalog");
  httpClient.get("/");
  int statusCode = httpClient.responseStatusCode();
  String response = httpClient.responseBody();
  if (statusCode >= 200 && statusCode < 300){
    DynamicJsonDocument doc(capacity);
    deserializeJson(doc, response);
    //IP extraction with fallback
    broker_address = doc["broker"]["ip"] | "test.mosquitto.org";
    broker_port = doc["broker"]["port"] | 1883;

    //make sure PC and Arduino have the same address
    if (broker_address == "localhost" || broker_address == "127.0.0.1") {
      broker_address = catalog_host; 
    }
    Serial.print("Rest connection established");


  }
  else{
    Serial.print("Connection Error, default values applied");
    broker_address = "test.mosquitto.org";
  }

}

String createRegistrationPayload() {
  DynamicJsonDocument doc(JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(4) + 100);
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
  Serial.println("Rest cayalog registartion");
  String payload = createRegistrationPayload();
  
  httpClient.beginRequest();
  httpClient.post("/");
  httpClient.sendHeader("Content-Type", "application/json");
  httpClient.sendHeader("Content-Length", payload.length());
  httpClient.beginBody();
  httpClient.print(payload);
  httpClient.endRequest();

  int statusCode = httpClient.responseStatusCode();
  Serial.println("Rest registartion completed. Status: " + String(statusCode));
}

void renewRegistration() {
  Serial.println("Keep-Alive");
  String payload = createRegistrationPayload();
  
  httpClient.beginRequest();
  httpClient.put("/");
  httpClient.sendHeader("Content-Type", "application/json");
  httpClient.sendHeader("Content-Length", payload.length());
  httpClient.beginBody();
  httpClient.print(payload);
  httpClient.endRequest();

  int statusCode = httpClient.responseStatusCode();
  Serial.println("Renewed. Status: " + String(statusCode));
}


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

  getBrokerInfo();
  registerToCatalog();
  lastRenewTime = millis();

  client.setServer(broker_address.c_str(), broker_port);
  client.setCallback(callback);
}

void loop() {
  if (client.state() != MQTT_CONNECTED) {
    reconnect();
  }
  client.loop();
  unsigned long currentMillis = millis();
  if (currentMillis - lastPublishTime >= interval) {
    lastPublishTime = currentMillis;


    String body = senMlEncode("temperature", readTemperature(), "Cel");
    client.publish(topic_pub.c_str(), body.c_str());
    
  }

  if (currentMillis - lastRenewTime >= renewInterval) {
    lastRenewTime = currentMillis;
    renewRegistration();
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  DeserializationError err = deserializeJson(doc_rec, payload, length);
  if (err) {
    Serial.print(F("deserializeJson() failed with code "));
    Serial.println(err.c_str());
    return;
  }
  if (doc_rec["e"][0]["n"] == "led") {
    if (doc_rec["e"][0]["v"] == 1) {
      digitalWrite(pinLed, HIGH);
      Serial.println("led ON");
    }
    if (doc_rec["e"][0]["v"] == 0) {
      digitalWrite(pinLed, LOW);
      Serial.println("led OFF");
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
  while (client.state() != MQTT_CONNECTED) {
    if (client.connect(device_id.c_str())) {
      Serial.println("connected");
      client.subscribe(topic_sub.c_str());
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