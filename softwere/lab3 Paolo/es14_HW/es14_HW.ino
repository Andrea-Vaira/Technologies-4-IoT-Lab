//Exercise Lab 2e : Local Smart Home Modified for Exercise 14 Software Labs
#include <LiquidCrystal_PCF8574.h>
#include <Scheduler.h>
#include <MBED_RPi_Pico_TimerInterrupt.h>
#include <PDM.h>
#include <SPI.h> 
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#define SECRET_SSID "XXXXX"
#define SECRET_PASS "XXXXXX"
#define GROUP_NAME "ArduinoGroup6"

int RLED= 2; 
int YLED= 3;
int PIRPIN= 7;
int FANPIN= 5; 
int TEMPPIN = A0; //14
const int B=4275;
const long int R0=100000;
const int T0= 298.13;
volatile float T=0.0;
int potSpeed=0;
int brightness=0;
LiquidCrystal_PCF8574 lcd(0x27);
const int sound_interval= 1000*60*1;//1 minutes
const int sound_threshold=1500;
const int timeout_sound=1000*60*1; //1 minutes
volatile int timeSoundEvents[n_sound_events]; //Buffer for times for michrophone events
volatile int firstPos=0; //Indexes for the buffer 
volatile int lastPos=-1; //starts from -1 so that at the first reading is placed at 0
short sampleBuffer[512];
volatile int numSounds=0;

//Information related to connections, the Broker and servers
char catalog_address[]="xx.xx.xx.xx";
int catalog_port=9090;
cahr broker_address[] = "://broker.hivemq.com";
int broker_port = 1883;
//For being compatible with sofware labs we need to specify in the topics the room
String room="livingroom";
String base_topic = "/tiot/group6/livingroom"; 
String device_id = "arduino_d001";
String tempTopic = "/tiot/group6/livingroom/temperature"; 
String motionTopic = "/tiot/group6/livingroom/motion"; 
String ledTopicSubscribed= "/tiot/group6/livingroom/led";
String alertTopic="/tiot/group6/alert"
int status= WL_IDLE_STATUS;

WiFiClient wifi;
HttpClient clientHttp= HttpClient(wifi, catalog_address, catalog_port);
// Callback forward declaration
void mqttCallback(char* topic, byte* payload, unsigned int length);
PubSubClient clientMqtt(broker_address.c_str(), broker_port, mqttCallback, wifi);

void setup() {
  //Setup Serial Port
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Exercise Lab 2 version 2: Local Smart Home interacting with Smart Home Controller");
  
  //Setup of the wi-fi connection  
  while(status != WL_CONNECTED)
  {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(SECRET_SSID);
    status= WiFi.begin(SECRET_SSID, SECRET_PASS);
    delay(5000);
  }
  Serial.print("Connected with IP address: ");
  Serial.println(WiFi.localIP());
  
  //Setup of LCD Display
  lcd.begin(16, 2);
  lcd.setBacklight(255);
  lcd.home();
  lcd.clear();

  //Setup of the pins for LED, Temperature Sensor, FAN and PIR sensor
  pinMode(RLED, OUTPUT);
  pinMode(TEMPPIN, INPUT);
  pinMode(FANPIN, OUTPUT);
  digitalWrite(FANPIN, potSpeed);
  attachInterrupt(digitalPinToInterrupt(PIRPIN), checkPresence, RISING);

  //Setup of the michrophone of the board
  PDM.onReceive(onPDMdata);
  if (!PDM.begin(1, 20000)) {
    Serial.println("Failed to start PDM!");
    while (1);
  }

  registerToCatalog();
  Scheduler.startLoop(refreshRegistration());
}

void loop() {
  if (!clientMqtt.connected()) {
    reconnectMQTT();
  }

  //Read of the voltage and formulas to get the value in Celsius
  int V= analogRead(TEMPPIN);
  float R= (1023.0/(float)V -1.0)*R0; 
  T= (1.0/(log(R/R0)/B + (1.0/T0)))- 273.1;

  delay(10000);
}
//MQTT callback for every message that arrives from the broker
void mqttCallback(char* topic, byte* payload, unsigned int length)
{
  DeserializationError err = deserializeJson(msgReceived, payload, length);
  if(err){
    Serial.print(F("deserializeJson() failed with code "));
    Serial.println(err.c_str());
  }

  if (msqReceived["e"][0]["n"] == "led") 
  {
    if (msgReceived["e"][0]["v"] == "on") {
      digitalWrite(pinLed, HIGH);
      Serial.println("Led swithced ON");
    }
    if (msgReceived["e"][0]["v"] == "off") {
      digitalWrite(pinLed, LOW);
      Serial.println("Led Switched OFF");
    }
  }
  else if(msqReceived["e"][0]["n"] == "led")
}

//Fuction for Catalog Registration
void registerToCatalog()
{
  String body="{\"ID\":"+device_id+", \"room\":\"livingroom\"}";
  //Communicating with the Catalog
  clientHttp.beginRequest();
  clientHttp.post("/registration");
  clientHttp.sendHeader("Content-Type", "application/json");
  clientHttp.sendHeader("Content-Length", body.length());
  clientHttp.beginBody();
  SerialHttp.println(body);
  clientHttp.print(body);
  clientHttp.endRequest();
  int ret= clientHttp.responseStatusCode();
  Serial.print("Response code: ");
  Serial.println(ret);
}

//Function in a loop to send refresh the registration
void refreshRegistration()
{
  String body="{\"ID\":"+device_id+", \"room\":\"livingroom\"}";
  clientHttp.beginRequest();
  clientHttp.put("/registration");
  clientHttp.sendHeader("Content-Type", "application/json");
  clientHttp.sendHeader("Content-Length", body.length());
  clientHttp.beginBody();
  SerialHttp.println(body);
  clientHttp.print(body);
  clientHttp.endRequest();
  int ret= clientHttp.responseStatusCode();
  Serial.print("Response code: ");
  Serial.println(ret);
}

void reconnectMQTT()
{
  while (clientMqtt.state() != MQTT_CONNECTED) {
    if (clientMqtt.connect("TiotGroup6")) {
      clientMqtt.subscribe(ledTopicSubscribed.c_str());
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

//ISR for PIR sensor
void checkPresence()
{
  //Now we must publish a message to the Broker to say that motion is TRUE
  String body=senMLEncode(motion, String(True), "boolean");
  mqttClient.publish(motionTopic.c_str(), body.c_str())
}

//Function for the read of the data from the michropohone
void onPDMdata()
{
  int bytesAvailable= PDM.available();
  PDM.read(sampleBuffer, bytesAvailable);
  int samplesRead=bytesAvailable/2;

  for(int i=0; i<samplesRead; i++)
  {
    if(sampleBuffer[i] > sound_threshold)
    {
      String body=senMLEncode(motion, String(True), "boolean");
      mqttClient.publish(motionTopic.c_str(), body.c_str())
      break;
    }
  }
}

String senMlEncode(String name, String value, String unit)
{
  String json = "{";
  json += "\"bn\":\"" + String(room) + "\",";
  json += "\"e\":[{";
  json += "\"n\":\"" + name + "\",";
  json += "\"t\":" + String(millis()) + ",";
  json += "\"v\":" + value + ","; 
  json += "\"u\":\"" + unit + "\""; // unit is passed with quotes or as literal null       
  json += "}]}";
  return json;
}