//Exercise 2 LAboratory 3
#include <SPI.h> 
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#define SECRET_SSID "Galaxy A55 RS"
#define SECRET_PASS "RichiS04"
#define GROUP_NAME "ArduinoGroup6"

char server_address[]="";
int server_port=8080;
WiFiClient wifi;
HttpClient client= HttpClient(wifi, server_address, server_port);

void setup() {
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Exercise Lab 3");

  while(status != WL_CONNECTED)
  {
    Serial.print("Attempting to connect ti SSID: ");
    Serial.println(SECRET_SSID);
    status= WiFi.begin(SECRET_SSID, SECCRET_PASS);
    delay(5000);
  }
  Serial.print("Connected with IP address: ");
  Serial.println(WiFi.localIP());
  server.begin();
}

void loop() {
  client.beginRequest();
  client.post("/log");
  
  client.endRequest();

}
