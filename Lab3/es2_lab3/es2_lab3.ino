//Exercise 2 Laboratory 3
#include <SPI.h> 
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#define SECRET_SSID "miao"
#define SECRET_PASS "12345678"
#define GROUP_NAME "ArduinoGroup6"

int LED_PIN=3;
int TEMP_PIN=A0;
const int B=4275;
const long int R0=100000;
const int T0= 298.13;
volatile float T=0.0;
char server_address[]="10.24.110.101";
int server_port=9090;
int status= WL_IDLE_STATUS;
WiFiClient wifi;
HttpClient client= HttpClient(wifi, server_address, server_port);

void setup() {
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Exercise Lab 3");

  pinMode(LED_PIN, OUTPUT);
  pinMode(TEMP_PIN, INPUT);

  while(status != WL_CONNECTED)
  {
    Serial.print("Attempting to connect ti SSID: ");
    Serial.println(SECRET_SSID);
    status= WiFi.begin(SECRET_SSID, SECRET_PASS);
    delay(5000);
  }
  Serial.print("Connected with IP address: ");
  Serial.println(WiFi.localIP());
}

void loop() {

  int V= analogRead(TEMP_PIN);
  float R= (1023.0/(float)V -1.0)*R0; 
  T= (1.0/(log(R/R0)/B + (1.0/T0)))- 273.1;

  Serial.print("Temp: ");
  Serial.println(T);
  String body=senMlEncode("temperature", T, "Cel");

  client.beginRequest();
  client.post("/log");
  client.sendHeader("Content-Type", "application/json");
  client.sendHeader("Content-Length", body.length());
  client.beginBody();
  Serial.println(body);
  client.print(body);
  client.endRequest();
  int ret= client.responseStatusCode();
  String resp= client.responseBody();

  delay(5000);
}

String senMlEncode(String name, float value, String unit)
{
  String json = "{";
  json += "\"bn\":\"" + String(GROUP_NAME) + "\",";
  json += "\"e\":[{";
  json += "\"n\":\"" + name + "\",";
  json += "\"t\":" + String(millis()) + ",";
  json += "\"v\":" + String(value) + ","; // Questa virgola separa 'v' da 'u' (corretto)
  json += "\"u\":\"" + unit + "\"";        // Nota i doppi apici \" attorno a unit
  json += "}]}";
  return json;
}
