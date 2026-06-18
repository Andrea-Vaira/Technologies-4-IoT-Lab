// Exercise Lab 2: Local Smart Home Modified for Exercise 14 Software Labs
#include <LiquidCrystal_PCF8574.h>
#include <MBED_RPi_Pico_TimerInterrupt.h>
#include <PDM.h>
#include <SPI.h> 
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>

#define SECRET_SSID "XXXXXX"
#define SECRET_PASS "XXXXXX"
#define GROUP_NAME "ArduinoGroup6"

int RLED = 2; 
int YLED = 3;
int PIRPIN = 7;
int FANPIN = 5; 
int TEMPPIN = A0; 
const int B = 4275;
const long int R0 = 100000;
const int T0 = 298.13;
volatile float T = 0.0;

unsigned long lastTimeTempRead = 0; 
unsigned long lastCatalogRefresh = 0;
const unsigned long catalogInterval = 60000; // 1 minute fo the keep-alive

int potSpeed = 0;
int brightness = 0;
LiquidCrystal_PCF8574 lcd(0x27);

const int sound_threshold = 1500;
short sampleBuffer[512];
volatile bool motionFlag = false;
volatile bool soundFlag = false;

// Configurazione di rete
char catalog_address[] = "172.22.198.XXX"; 
int catalog_port = 8080;
char broker_address[] = "broker.hivemq.com";
int broker_port = 1883;

String room = "livingroom";
String device_id = "arduino_d001";
String tempTopic = "/tiot/group6/livingroom/temperature"; 
String motionTopic = "/tiot/group6/livingroom/motion";
String soundTopic = "/tiot/group6/livingroom/sound";

String ledTopicSubscribed = "/tiot/group6/livingroom/led";
String fanTopicSubscribe = "/tiot/group6/livingroom/fan";
String displayTopicSubscribe = "/tiot/group6/livingroom/display";

int status = WL_IDLE_STATUS;

WiFiClient wifi;
void mqttCallback(char* topic, byte* payload, unsigned int length);
PubSubClient clientMqtt(broker_address, broker_port, mqttCallback, wifi);

const int capacity = JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(4) + 100;
DynamicJsonDocument msgReceived(capacity);

String getCatalogPayload() {
  return "{\"ID\":\"" + device_id + "\","
         "\"Description\":\"Arduino Smart Home Node\","
         "\"MQTT_topic\":\"" + tempTopic + "\","
         "\"Resources\":[\"temperature\",\"motion\",\"sound\"]}";
}

void registerToCatalog() {
  WiFiClient httpWifi;
  HttpClient clientHttp(httpWifi, catalog_address, catalog_port);
  String body = getCatalogPayload();
  
  Serial.println("Registering to Catalog via POST...");
  clientHttp.beginRequest();
  clientHttp.post("/catalog");
  clientHttp.sendHeader("Content-Type", "application/json");
  clientHttp.sendHeader("Content-Length", body.length());
  clientHttp.beginBody();
  clientHttp.print(body);
  clientHttp.endRequest();
  
  int ret = clientHttp.responseStatusCode();
  Serial.print("Registration Response code: ");
  Serial.println(ret);
}

void refreshRegistration() {
  WiFiClient httpWifi;
  HttpClient clientHttp(httpWifi, catalog_address, catalog_port);
  String body = getCatalogPayload();
  
  Serial.println("Refreshing Catalog registration via PUT...");
  clientHttp.beginRequest();
  clientHttp.put("/catalog");
  clientHttp.sendHeader("Content-Type", "application/json");
  clientHttp.sendHeader("Content-Length", body.length());
  clientHttp.beginBody();
  clientHttp.print(body);
  clientHttp.endRequest();
  
  int ret = clientHttp.responseStatusCode();
  Serial.print("Refresh Response code: ");
  Serial.println(ret);
}

void getCatalogSubscriptions() {
  WiFiClient httpWifi;
  HttpClient clientHttp(httpWifi, catalog_address, catalog_port);
  Serial.println("Request Catalog subscription with REST GET...");
  
  clientHttp.get("/catalog"); 
  int statusCode = clientHttp.responseStatusCode();
  String response = clientHttp.responseBody();
  
  Serial.print("Catalog responce: ");
  Serial.println(statusCode);
}

void setup() {
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Exercise Lab 2: Fixed Architecture");
  
  while(status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(SECRET_SSID);
    status = WiFi.begin(SECRET_SSID, SECRET_PASS);
    delay(5000);
  }
  Serial.print("Connected with IP address: ");
  Serial.println(WiFi.localIP());
  
  delay(2000); 

  lcd.begin(16, 2);
  lcd.setBacklight(255);
  lcd.clear();

  pinMode(RLED, OUTPUT);
  pinMode(TEMPPIN, INPUT);
  pinMode(FANPIN, OUTPUT);
  digitalWrite(FANPIN, potSpeed);
  attachInterrupt(digitalPinToInterrupt(PIRPIN), checkPresence, RISING);

  PDM.onReceive(onPDMdata);
  if (!PDM.begin(1, 20000)) {
    Serial.println("Failed to start PDM!");
    while (1);
  }

  
  registerToCatalog();
  getCatalogSubscriptions();

  lastTimeTempRead = millis();
  lastCatalogRefresh = millis();
}

void checkSerialCommands() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() > 0) {
      String settingsTopic = "/tiot/" + String(GROUP_NAME) + "/settings";
      clientMqtt.publish(settingsTopic.c_str(), input.c_str());
      Serial.println("Command sent to remote Controller: " + input);
    }
  }
}

void loop() {
  if (!clientMqtt.connected()) {
    reconnectMQTT();
  }
  clientMqtt.loop();
  checkSerialCommands();

  if(motionFlag == true) {
    String body = senMlEncode("motion", String(true), "boolean");
    clientMqtt.publish(motionTopic.c_str(), body.c_str());
    motionFlag = false;
  }

  if(soundFlag == true) {
    String body = senMlEncode("sound", String(true), "boolean");
    clientMqtt.publish(soundTopic.c_str(), body.c_str());
    soundFlag = false;
  }

  unsigned long now = millis();


  if((now - lastTimeTempRead) >= 10000) {
    int V = analogRead(TEMPPIN);
    float R = (1023.0/(float)V - 1.0)*R0; 
    T = (1.0/(log(R/R0)/B + (1.0/T0))) - 273.1;
    lastTimeTempRead = now;
    String body = senMlEncode("temperature", String(T), "Cel");
    clientMqtt.publish(tempTopic.c_str(), body.c_str());
  }
  
  
  if((now - lastCatalogRefresh) >= catalogInterval) {
    lastCatalogRefresh = now;
    refreshRegistration();
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  if(length == 0) return;
  
  DeserializationError err = deserializeJson(msgReceived, payload, length);
  if(err) {
    Serial.print(F("deserializeJson() failed with code "));
    Serial.println(err.c_str());
    return;
  }

  if (msgReceived["e"][0]["n"] == "led") {
    float val = msgReceived["e"][0]["v"];
    brightness = map(val, 0, 100, 255, 0);
    analogWrite(RLED, brightness);
  }
  else if(msgReceived["e"][0]["n"] == "fan") {
    float val = msgReceived["e"][0]["v"];
    potSpeed = map(val , 0, 100, 0, 255);
    analogWrite(FANPIN, potSpeed);
  }
  else if(msgReceived["e"][0]["n"] == "display") {
    String text = msgReceived["e"][0]["v"];
    printOnLCD(text);
  }
}

void reconnectMQTT() {
  while (status == WL_CONNECTED && !clientMqtt.connected()) {
    Serial.println("Attempting MQTT connection...");
    if (clientMqtt.connect("TiotGroup6")) {
      Serial.println("MQTT Connected!");
      clientMqtt.subscribe(ledTopicSubscribed.c_str());
      clientMqtt.subscribe(fanTopicSubscribe.c_str());
      clientMqtt.subscribe(displayTopicSubscribe.c_str());
    } else {
      Serial.print("failed, rc=");
      Serial.print(clientMqtt.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void checkPresence() {
  motionFlag = true;
}

void onPDMdata() {
  int bytesAvailable = PDM.available();
  PDM.read(sampleBuffer, bytesAvailable);
  int samplesRead = bytesAvailable / 2;

  for(int i=0; i<samplesRead; i++) {
    if(sampleBuffer[i] > sound_threshold) {
      soundFlag = true;
      break;
    }
  }
}

void printOnLCD(String text) {
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print(text);
}

String senMlEncode(String name, String value, String unit) {
  String json = "{";
  json += "\"bn\":\"" + String(room) + "\",";
  json += "\"e\":[{";
  json += "\"n\":\"" + name + "\",";
  json += "\"t\":" + String(millis()) + ",";
  json += "\"v\":" + value + ","; 
  json += "\"u\":\"" + unit + "\"";       
  json += "}]}";
  return json;
}