//Exercise 1 Laboratory 3
#include <SPI.h> 
#include <WiFiNINA.h>
//#include "arduino_secrets.h"
#define SECRET_SSID "Galaxy A55 RS"
#define SECRET_PASS "RichiS04"
#define GROUP_NAME "ArduinoGroup6"

int LED_PIN= 3;
int TEMPPIN = A0; //14
const int B=4275;
const long int R0=100000;
const int T0= 298.13;
volatile float T=0.0;
char ssid[]= SECRET_SSID;
char pass[]= SECRET_PASS;
int status= WL_IDLE_STATUS;
WiFiServer server(80);

void setup() {

  Serial.begin(9600);
  while(!Serial);
  Serial.println("Exercise Lab 3");

  pinMode(LED_PIN, OUTPUT);
  pinMode(TEMPPIN, INPUT);

  while(status != WL_CONNECTED)
  {
    Serial.print("Attempting to connect ti SSID: ");
    Serial.println(ssid);
    status= WiFi.begin(ssid, pass);
    delay(5000);
  }
  Serial.print("Connected with IP address: ");
  Serial.println(WiFi.localIP());
  server.begin();
}

void loop() {
  WiFiClient client = server.available();

  if(client)
  {
    process(client);
    client.stop();
  }
  delay(50);
}

//Process what the client asks
void process(WiFiClient client)
{
  String req_type= client.readStringUntil(' ');
  req_type.trim();
  String url= client.readStringUntil(' ');
  url.trim();

  if(url.startsWith("/led/"))
  {
    String led_val= url.substring(5);
    Serial.println(led_val);

    if(led_val== "0" || led_val== "1")
    {
      int val= led_val.toInt();
      digitalWrite(LED_PIN, val);
      printResponse(client, 200, senMlEncode("led", val, ""));
    }
    else
    {
      printResponse(client, 403, "");
    }
  }
  else if(url.startsWith("/temperature"))
  {
    int V= analogRead(TEMPPIN);
    float R= (1023.0/(float)V -1.0)*R0; 
    T= (1.0/(log(R/R0)/B + (1.0/T0)))- 273.1;
    printResponse(client, 200, senMlEncode("temperature", T, "Cel"));
  }
  else
  {
    printResponse(client, 404, "");
  }
}

void printResponse(WiFiClient client, int code, String body){
  client.print("HTTP/1.1 " + String(code));
  if (code == 200){
    client.println("Content-type: application/jon; charset = utf-8");
    client.println();
    client.println(body);
  } 
  else{
    client.print("Error : ");
    client.println(code);
  }
}

String senMlEncode(String name, int value, String unit)
{
  String json;
  json = "{";
  json += "\"bn\":\"" + String(GROUP_NAME) + "\",";
  json += "\"e\":[{";
  json += "\"n\":\"" + name + "\",";
  json += "\"t\":" + String(millis()) + ",";
  json += "\"v\":" + String(value) + ",";
  json += "\"u\":" + unit; // unit is passed with quotes or as literal null
  json += "}]}";
  return json;
}


