//Exercise Lab 2: Local Smart Home Modified for Exercise 14 Software Labs
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
long lastTimeTempRead; 
int potSpeed=0;
int brightness=0;
LiquidCrystal_PCF8574 lcd(0x27);
const int sound_interval= 1000*60*1;//1 minutes
const int sound_threshold=1500;
const int timeout_sound=1000*60*1; //1 minutes
short sampleBuffer[512];
volatile int numSounds=0;
volatile bool motionFlag= false;
volatile bool soundFlag= false;

//Information related to connections, the Broker and servers
char catalog_address[]="xx.xx.xx.xx";
int catalog_port=9090;
char broker_address[] = "broker.hivemq.com";
int broker_port = 1883;
//For being compatible with sofware labs we need to specify in the topics the room
String room="livingroom";
String base_topic = "/tiot/group6/livingroom"; 
String device_id = "arduino_d001";
String tempTopic = "/tiot/group6/livingroom/temperature"; 
String motionTopic = "/tiot/group6/livingroom/motion";
String soundTopic= "/tiot/group6/livingroom/sound";

String ledTopicSubscribed= "/tiot/group6/livingroom/led";
String fanTopicSubscribe= "/tiot/group6/livingroom/fan";
String displayTopicSubscribe= "/tiot/group6/livingroom/display";
String alertTopic="/tiot/group6/alert";
int status= WL_IDLE_STATUS;

WiFiClient wifi;
HttpClient clientHttp= HttpClient(wifi, catalog_address, catalog_port);
// Callback forward declaration
void mqttCallback(char* topic, byte* payload, unsigned int length);
PubSubClient clientMqtt(broker_address, broker_port, mqttCallback, wifi);
const int capacity = JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(4) + 100;
DynamicJsonDocument msgReceived(capacity);

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
  lastTimeTempRead=millis();

  //Setup for registration to the Catalog
  registerToCatalog();
  Scheduler.startLoop(refreshRegistration);
}

void loop() {
  if (!clientMqtt.connected()) {
    reconnectMQTT();
  }
  clientMqtt.loop();

  //If a noise or the PIR activate means that there is someone, so a message is published
  if(motionFlag == true)
  {
    String body=senMlEncode("motion", String(true), "boolean");
    clientMqtt.publish(motionTopic.c_str(), body.c_str());
    motionFlag=false;
  }

  if(soundFlag == true)
  {
    String body=senMlEncode("sound", String(true), "boolean");
    clientMqtt.publish(soundTopic.c_str(), body.c_str());
    soundFlag=false;
  }

  long now=millis();
  if((now- lastTimeTempRead) >= 10000)
  {
    //Read of the voltage and formulas to get the value in Celsius
    int V= analogRead(TEMPPIN);
    float R= (1023.0/(float)V -1.0)*R0; 
    T= (1.0/(log(R/R0)/B + (1.0/T0)))- 273.1;
    lastTimeTempRead=millis();
    String body=senMlEncode("temperature", String(T), "Cel");
    clientMqtt.publish(tempTopic.c_str(), body.c_str());
  }
}
//MQTT callback for every message that arrives from the broker
void mqttCallback(char* topic, byte* payload, unsigned int length)
{
  DeserializationError err = deserializeJson(msgReceived, payload, length);
  if(err){
    Serial.print(F("deserializeJson() failed with code "));
    Serial.println(err.c_str());
  }

  if (msgReceived["e"][0]["n"] == "led") 
  {
    float val=msgReceived["e"][0]["v"];
    brightness= map(val, 0, 100, 255, 0);//The LED is more bright as the value is lower
    analogWrite(RLED, brightness);
  }
  else if(msgReceived["e"][0]["n"] == "fan")
  {
    float val=msgReceived["e"][0]["v"];
    potSpeed= map(val , 0, 100, 0, 255); //With higher value the FAN rotate more rapidly
    analogWrite(FANPIN, potSpeed);
  }
  else if(msgReceived["e"][0]["n"] == "display")
  {
    String text=msgReceived["e"][0]["v"];
    printOnLCD(text);
  }
  else
  {
    Serial.println("Error, Topic non right");
  }
}

//Fuction for Catalog Registration
void registerToCatalog()
{
  String body="{\"ID\":\""+device_id+"\", \"room\":\"livingroom\"}";
  //Communicating with the Catalog
  clientHttp.beginRequest();
  clientHttp.post("/registration");
  clientHttp.sendHeader("Content-Type", "application/json");
  clientHttp.sendHeader("Content-Length", body.length());
  clientHttp.beginBody();
  clientHttp.print(body);
  clientHttp.endRequest();
  int ret= clientHttp.responseStatusCode();
  Serial.print("Response code: ");
  Serial.println(ret);
}

//Function in a loop to send refresh the registration
void refreshRegistration()
{
  String body="{\"ID\":\""+device_id+"\", \"room\":\"livingroom\"}";
  clientHttp.beginRequest();
  clientHttp.put("/registration");
  clientHttp.sendHeader("Content-Type", "application/json");
  clientHttp.sendHeader("Content-Length", body.length());
  clientHttp.beginBody();
  clientHttp.print(body);
  clientHttp.endRequest();
  int ret= clientHttp.responseStatusCode();
  Serial.print("Response code: ");
  Serial.println(ret);
}

void reconnectMQTT()
{
  while (clientMqtt.state() != MQTT_CONNECTED) 
  {
    if (clientMqtt.connect("TiotGroup6")) 
    {
      clientMqtt.subscribe(ledTopicSubscribed.c_str());
      clientMqtt.subscribe(fanTopicSubscribe.c_str());
      clientMqtt.subscribe(displayTopicSubscribe.c_str());
    } 
    else 
    {
      Serial.print("failed, rc=");
      Serial.print(clientMqtt.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

//ISR for PIR sensor
void checkPresence()
{
  //Set the motion flag so that in the loop a message get published
  motionFlag=true;
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
      //Set the sound flag so that in the loop a message get published
      soundFlag=true;
      break;
    }
  }
}

void printOnLCD(String text)
{
  lcd.setCursor(0,0);
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print(text);
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